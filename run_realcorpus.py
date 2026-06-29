"""Conformance and replay verification for ClaimBench certificates.

Motivation
----------
``crypto.verify_certificate_dict`` answers a narrow question: *was this
``certificate_core`` signed by the holder of this key, and does its stored hash
match its stored bytes?* It does **not** answer the question a hostile reader
actually cares about: *does this badge follow deterministically from the claim
package and the embedded evidence?* A malicious or buggy issuer can hand-edit a
core (flip ``Refuted`` to ``Verified``), re-sign it, and pass signature
verification. The signature is integrity over the wrong object.

This module supplies the missing layer. It re-derives the badge two ways and
checks the certificate against itself and against its source package:

1. **Self-consistency** (needs only the certificate): the core embeds every
   formalization's ``kind``, ``verdict``, and ``certified_admitted`` /
   ``asserted_admitted`` flags. The badge is a pure function of those. We
   recompute it and require it to equal the stored badge. This alone catches the
   forge above, because the forged core still carries the formalizations that
   incriminate it.
2. **Package reproduction** (needs the original claim package): re-run the
   deterministic kernel and require the re-derived core to be byte-identical to
   the stored core. This catches tampering anywhere in the core, not just the
   badge label.
3. **Hash + signature** (optional): recompute the core hash; verify the
   signature if a public key is supplied.

Doctrine
--------
A ClaimBench signature should be read as the issuer asserting *"I ran the kernel
and obtained this core."* A verifier must **reproduce** to confirm that assertion
is true. Signature without reproduction is trust; reproduction is verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .badges import Badge
from .engine import _canonical_json, _sha256_core, _classify, evaluate_claim_package
from .models import Formalization


# --------------------------------------------------------------------------- #
# Re-derivation from an existing certificate core
# --------------------------------------------------------------------------- #

def _formalization_from_core_entry(entry: Dict[str, Any]) -> Formalization:
    """Rebuild a Formalization from a core ``formalizations`` entry.

    Only the fields the classifier reads (kind, verdict) need to be faithful;
    admission is reconstructed minimally because certified/asserted membership is
    taken from the explicit flags the core already records.
    """
    return Formalization.from_dict(
        {
            "id": entry.get("id", ""),
            "role": entry.get("role", ""),
            "kind": entry.get("kind", "semantic"),
            "description": entry.get("description", ""),
            "grounding_spans": entry.get("grounding_spans", []),
            "changed_primitives": entry.get("changed_primitives", []),
            "admission": {"status": entry.get("admission_status", "")},
            "verdict": entry.get("verdict", {}) or {},
        }
    )


def recompute_badge_from_core(core: Dict[str, Any]) -> Tuple[Badge, str]:
    """Re-derive the badge purely from the core's embedded formalization payload.

    Mirrors ``engine.evaluate_claim_package``'s selection logic: certified set
    drives the badge; if only asserted membership exists, the result is
    Self-Attested Only; if neither, Out of Scope.
    """
    entries = core.get("formalizations", []) or []
    certified = [
        _formalization_from_core_entry(e) for e in entries if e.get("certified_admitted")
    ]
    asserted = [
        _formalization_from_core_entry(e) for e in entries if e.get("asserted_admitted")
    ]

    if certified:
        return _classify(certified)
    if asserted:
        return (
            Badge.SELF_ATTESTED_ONLY,
            "One or more formalizations pass only as submitter-asserted or "
            "LLM-proposed support, but no formalization satisfies certification "
            "provenance requirements.",
        )
    return _classify(certified)  # empty -> Out of Scope


# --------------------------------------------------------------------------- #
# Conformance report
# --------------------------------------------------------------------------- #

@dataclass
class Check:
    name: str
    passed: bool
    critical: bool
    detail: str = ""


@dataclass
class ConformanceReport:
    checks: List[Check] = field(default_factory=list)

    def add(self, name: str, passed: bool, critical: bool, detail: str = "") -> None:
        self.checks.append(Check(name=name, passed=passed, critical=critical, detail=detail))

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks if c.critical)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [
                {"name": c.name, "passed": c.passed, "critical": c.critical, "detail": c.detail}
                for c in self.checks
            ],
        }

    def render(self) -> str:
        lines = [f"Conformance: {'PASS' if self.ok else 'FAIL'}"]
        for c in self.checks:
            mark = "PASS" if c.passed else ("FAIL" if c.critical else "warn")
            lines.append(f"  [{mark:4s}] {c.name}" + (f" — {c.detail}" if c.detail else ""))
        return "\n".join(lines)


def _first_core_diffs(stored: Dict[str, Any], rederived: Dict[str, Any], limit: int = 6) -> List[str]:
    diffs: List[str] = []
    keys = sorted(set(stored) | set(rederived))
    for k in keys:
        if stored.get(k) != rederived.get(k):
            diffs.append(k)
            if len(diffs) >= limit:
                break
    return diffs


def verify_certificate_conformance(
    certificate: Dict[str, Any],
    package_data: Optional[Dict[str, Any]] = None,
    public_key: Any = None,
) -> ConformanceReport:
    """Full third-party conformance check on a (possibly signed) certificate.

    Returns a ConformanceReport. ``ok`` is True only if every critical check
    passes. Signature validity alone is *not* sufficient — the badge must also
    reproduce.
    """
    report = ConformanceReport()

    core = certificate.get("certificate_core")
    if not isinstance(core, dict):
        report.add("core_present", False, critical=True, detail="No certificate_core object found.")
        return report
    report.add("core_present", True, critical=True)

    # 1. Stored hash matches stored core bytes.
    stored_hash = certificate.get("core_hash_sha256")
    recomputed_hash = _sha256_core(core)
    if stored_hash is None:
        report.add("core_hash_present", False, critical=False, detail="No core_hash_sha256 in wrapper.")
    else:
        report.add(
            "core_hash_matches_core",
            stored_hash == recomputed_hash,
            critical=True,
            detail="" if stored_hash == recomputed_hash else f"stored={stored_hash[:16]} recomputed={recomputed_hash[:16]}",
        )

    # 2. Self-consistency: badge follows from the core's own formalizations.
    stored_badge = core.get("badge")
    rederived_badge, _ = recompute_badge_from_core(core)
    consistent = stored_badge == rederived_badge.value
    report.add(
        "badge_self_consistent",
        consistent,
        critical=True,
        detail="" if consistent else f"core says '{stored_badge}', formalizations imply '{rederived_badge.value}'",
    )

    # 3. Package reproduction (if the source package is provided).
    if package_data is not None:
        rederived_core = evaluate_claim_package(package_data).to_core_dict()
        identical = _canonical_json(rederived_core) == _canonical_json(core)
        report.add(
            "package_reproduces_core",
            identical,
            critical=True,
            detail="" if identical else "differs in: " + ", ".join(_first_core_diffs(core, rederived_core)),
        )

    # 4. Signature (if a key is provided). Non-critical to conformance: a valid
    #    signature over a non-reproducing core must still FAIL overall, which is
    #    the entire point. We record it for provenance, not as a pass condition.
    if public_key is not None:
        try:
            from .crypto import verify_certificate_dict

            sig_ok, msgs = verify_certificate_dict(certificate, public_key)
            report.add(
                "signature_valid",
                sig_ok,
                critical=False,
                detail="; ".join(msgs),
            )
        except Exception as exc:  # pragma: no cover - defensive
            report.add("signature_valid", False, critical=False, detail=f"verify error: {exc}")

    return report
