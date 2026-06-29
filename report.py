from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from . import __version__ as PACKAGE_VERSION
from .admission import AdmissionFinding, evaluate_admission
from .badges import BADGE_EXPLANATIONS, Badge
from .models import ClaimPackage, Formalization


def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_core(data: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


@dataclass
class EvaluationResult:
    badge: Badge
    explanation: str
    admitted_formalizations: List[str]
    rejected_formalizations: List[str]
    asserted_admitted_formalizations: List[str]
    uncertified_formalizations: List[str]
    admission_findings: List[AdmissionFinding]
    rationale: str
    package: ClaimPackage
    evaluated_at: str
    projected_badge: Badge | None = None
    projected_rationale: str | None = None

    def _formalization_dicts(self) -> List[Dict[str, Any]]:
        findings_by_id = {x.formalization_id: x for x in self.admission_findings}
        out: List[Dict[str, Any]] = []
        for f in self.package.formalizations:
            finding = findings_by_id.get(f.id)
            out.append(
                {
                    "id": f.id,
                    "role": f.role,
                    "kind": f.kind,
                    "description": f.description,
                    "grounding_spans": f.grounding_spans,
                    "changed_primitives": f.changed_primitives,
                    "admission_status": f.admission.status,
                    "admission_reason": f.admission.reason,
                    "gate_findings": [asdict(g) for g in finding.gate_findings] if finding else [],
                    "asserted_admitted": finding.asserted_admitted if finding else False,
                    "certified_admitted": finding.certified_admitted if finding else False,
                    "verdict": {
                        "status": f.verdict.status,
                        "summary": f.verdict.summary,
                        "metrics": f.verdict.metrics,
                    },
                }
            )
        return out

    def to_core_dict(self) -> Dict[str, Any]:
        """Deterministic, hashable certificate core.

        This object is a pure function of the claim package, standard behavior, and
        kernel version. It intentionally excludes timestamps and runner metadata.
        """
        return {
            "schema": "claimbench.certificate_core.v2.1",
            "kernel_version": PACKAGE_VERSION,
            "badge": self.badge.value,
            "explanation": self.explanation,
            "projected_badge_if_non_certifying_assertions_accepted": self.projected_badge.value if self.projected_badge else None,
            "projected_rationale": self.projected_rationale,
            "admitted_formalizations": self.admitted_formalizations,
            "rejected_formalizations": self.rejected_formalizations,
            "asserted_admitted_formalizations": self.asserted_admitted_formalizations,
            "uncertified_formalizations": self.uncertified_formalizations,
            "admission_findings": [asdict(x) for x in self.admission_findings],
            "rationale": self.rationale,
            "claim_id": self.package.metadata.get("claim_id"),
            "title": self.package.metadata.get("title"),
            "owner": self.package.metadata.get("owner"),
            "package_version": self.package.metadata.get("version"),
            "claim_statement": self.package.claim.get("statement"),
            "frozen_at": self.package.claim.get("frozen_at"),
            "standard_version": self.package.scope.get("standard_version"),
            "claim_class": self.package.scope.get("claim_class"),
            "materiality": self.package.scope.get("materiality"),
            "verifier": self.package.verifier,
            "formalizations": self._formalization_dicts(),
            "evidence": self.package.evidence,
        }

    def core_hash(self) -> str:
        return _sha256_core(self.to_core_dict())

    def to_dict(self) -> Dict[str, Any]:
        core = self.to_core_dict()
        return {
            "certificate_core": core,
            "core_hash_sha256": _sha256_core(core),
            "run_envelope": {
                "evaluated_at": self.evaluated_at,
                "timestamp_excluded_from_core_hash": True,
            },
        }


def _classify(admitted: List[Formalization]) -> Tuple[Badge, str]:
    semantic = [f for f in admitted if f.kind == "semantic"]
    evidentiary = [f for f in admitted if f.kind == "evidentiary"]
    if not semantic:
        return Badge.OUT_OF_SCOPE, "No admitted semantic formalization exists."

    statuses = {f.verdict.status for f in semantic}
    evid_statuses = {f.verdict.status for f in evidentiary}
    any_evid_inconclusive = "inconclusive" in evid_statuses

    if "pass" in statuses and "fail" in statuses:
        if "inconclusive" in statuses or any_evid_inconclusive:
            return Badge.SEMANTIC_BOUNDARY, "Admitted semantic formalizations diverge between pass and fail; evidentiary gaps are also disclosed."
        return Badge.SEMANTIC_BOUNDARY, "Admitted semantic formalizations diverge between pass and fail."

    if statuses == {"pass"}:
        if any_evid_inconclusive:
            return Badge.EVIDENTIARY_INCONCLUSIVE, "Semantic readings pass, but an admitted evidentiary channel remains inconclusive."
        return Badge.VERIFIED, "All admitted semantic formalizations pass."

    if statuses == {"fail"}:
        if any_evid_inconclusive:
            return Badge.REFUTED_WITH_EVIDENTIARY_GAPS, "All admitted semantic readings fail, with additional evidentiary gaps disclosed."
        return Badge.REFUTED, "All admitted semantic formalizations fail."

    if statuses == {"inconclusive"}:
        return Badge.EVIDENTIARY_INCONCLUSIVE, "All admitted semantic readings are evidentiary inconclusive."

    if statuses == {"fail", "inconclusive"}:
        return Badge.REFUTED_WITH_EVIDENTIARY_GAPS, "At least one admitted semantic reading fails, none pass, and at least one is inconclusive."

    if statuses == {"pass", "inconclusive"}:
        return Badge.EVIDENTIARY_INCONCLUSIVE, "At least one admitted semantic reading passes, none fail, but at least one remains inconclusive."

    return Badge.OUT_OF_SCOPE, "Verdict statuses could not be classified under the standard."


def evaluate_claim_package(data: Dict[str, Any]) -> EvaluationResult:
    package = ClaimPackage.from_dict(data)
    findings = [evaluate_admission(package, f) for f in package.formalizations]

    certified_ids = {x.formalization_id for x in findings if x.certified_admitted}
    asserted_ids = {x.formalization_id for x in findings if x.asserted_admitted}

    certified_admitted = [f for f in package.formalizations if f.id in certified_ids]
    asserted_admitted = [f for f in package.formalizations if f.id in asserted_ids]
    rejected = [f for f in package.formalizations if f.id not in asserted_ids]
    uncertified = [f for f in package.formalizations if f.id in asserted_ids and f.id not in certified_ids]

    projected_badge = None
    projected_rationale = None
    if asserted_admitted:
        projected_badge, projected_rationale = _classify(asserted_admitted)

    if certified_admitted:
        badge, rationale = _classify(certified_admitted)
    elif asserted_admitted:
        badge = Badge.SELF_ATTESTED_ONLY
        rationale = "One or more formalizations pass only as submitter-asserted or LLM-proposed support, but no formalization satisfies certification provenance requirements."
    else:
        badge, rationale = _classify(certified_admitted)

    return EvaluationResult(
        badge=badge,
        explanation=BADGE_EXPLANATIONS[badge],
        admitted_formalizations=[f.id for f in certified_admitted],
        rejected_formalizations=[f.id for f in rejected],
        asserted_admitted_formalizations=[f.id for f in asserted_admitted],
        uncertified_formalizations=[f.id for f in uncertified],
        admission_findings=findings,
        rationale=rationale,
        package=package,
        evaluated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        projected_badge=projected_badge,
        projected_rationale=projected_rationale,
    )
