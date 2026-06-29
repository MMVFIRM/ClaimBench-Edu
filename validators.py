from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .models import (
    ADMISSION_GATES,
    CERTIFYING_GATE_SOURCES,
    GateSource,
    GateValue,
    ClaimPackage,
    Formalization,
)


@dataclass
class GateFinding:
    gate: str
    status: str
    source: str
    producer: str
    reason: str = ""
    certifying: bool = False


@dataclass
class AdmissionFinding:
    formalization_id: str
    asserted_admitted: bool
    certified_admitted: bool
    reason: str
    missing_gates: List[str]
    failed_gates: List[str]
    unknown_spans: List[str]
    uncertified_gates: List[str]
    gate_findings: List[GateFinding] = field(default_factory=list)

    @property
    def admitted(self) -> bool:
        """Backward-compatible alias for certified admission."""
        return self.certified_admitted


def _kernel_gate(name: str, passed: bool, reason: str) -> GateFinding:
    return GateFinding(
        gate=name,
        status="pass" if passed else "fail",
        source=GateSource.KERNEL_RECOMPUTED.value,
        producer="claimbench_kernel",
        reason=reason,
        certifying=True,
    )


def _finding_from_gate(name: str, gate: GateValue | None) -> GateFinding:
    if gate is None:
        return GateFinding(
            gate=name,
            status="missing",
            source=GateSource.SUBMITTER_ASSERTED.value,
            producer="submitter",
            reason="No gate value supplied in package.",
            certifying=False,
        )
    return GateFinding(
        gate=name,
        status=gate.status,
        source=gate.source,
        producer=gate.producer,
        reason=gate.reason,
        certifying=gate.source in CERTIFYING_GATE_SOURCES,
    )


def evaluate_admission(package: ClaimPackage, formalization: Formalization) -> AdmissionFinding:
    """Evaluate whether a formalization enters the certified badge calculation.

    v2.1 separates asserted gates from checked/adjudicated gates. Legacy scalar gate
    values remain readable, but are treated as submitter_asserted. The deterministic
    kernel recomputes frozen_record, span_grounding, and publication; remaining gates
    must be marked claimbench_adjudicated to support a certified badge.
    """
    known = package.record_span_ids
    unknown_spans = [s for s in formalization.grounding_spans if s not in known]

    gate_findings_by_name: Dict[str, GateFinding] = {}
    for gate in ADMISSION_GATES:
        gate_findings_by_name[gate] = _finding_from_gate(gate, formalization.admission.gates.get(gate))

    gate_findings_by_name["frozen_record"] = _kernel_gate(
        "frozen_record",
        package.has_frozen_record,
        "Kernel checked claim.frozen_at and claim.record are present." if package.has_frozen_record else "Frozen claim record is incomplete.",
    )
    gate_findings_by_name["span_grounding"] = _kernel_gate(
        "span_grounding",
        not unknown_spans and bool(formalization.grounding_spans),
        "Kernel checked all grounding spans resolve against the frozen record."
        if not unknown_spans and formalization.grounding_spans
        else "One or more grounding spans are missing from the frozen record, or no spans were supplied.",
    )
    gate_findings_by_name["publication"] = _kernel_gate(
        "publication",
        True,
        "Kernel emits admitted/rejected formalizations and gate findings in the certificate core.",
    )

    gate_findings = [gate_findings_by_name[gate] for gate in ADMISSION_GATES]
    missing = [g.gate for g in gate_findings if g.status == "missing"]
    failed = [g.gate for g in gate_findings if g.status == "fail"]
    uncertified = [g.gate for g in gate_findings if g.status == "pass" and not g.certifying]

    asserted_admitted = (
        formalization.admission.status == "admitted"
        and not missing
        and not failed
    )
    certified_admitted = asserted_admitted and not uncertified

    if formalization.admission.status != "admitted":
        reason = formalization.admission.reason or "Formalization marked rejected."
    elif failed:
        reason = "One or more admission gates failed."
    elif missing:
        reason = "Admitted formalization is missing required admission gates."
    elif uncertified:
        reason = "Admission relies on submitter-asserted gates and is not eligible for a ClaimBench-certified badge."
    else:
        reason = "All admission gates passed with certifying provenance."

    return AdmissionFinding(
        formalization_id=formalization.id,
        asserted_admitted=asserted_admitted,
        certified_admitted=certified_admitted,
        reason=reason,
        missing_gates=missing,
        failed_gates=failed,
        unknown_spans=unknown_spans,
        uncertified_gates=uncertified,
        gate_findings=gate_findings,
    )
