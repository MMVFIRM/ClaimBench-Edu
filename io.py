from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


ADMISSION_GATES = [
    "frozen_record",
    "span_grounding",
    "semantic_difference",
    "materiality",
    "minimal_change",
    "structure_preservation",
    "parity",
    "symmetry",
    "adversarial_review",
    "publication",
]

# These gates are recomputed by the deterministic kernel in v2.1.
# The remaining gates may be supplied by ClaimBench adjudication or by the submitter,
# and the certificate will preserve that provenance instead of flattening it.
KERNEL_RECOMPUTED_GATES = {"frozen_record", "span_grounding", "publication"}

PASS_VALUES = {"pass", "passed", True}
FAIL_VALUES = {"fail", "failed", False}
VALID_GATE_STATUSES = {"pass", "fail", "missing", "unknown"}
VALID_GATE_SOURCES = {"kernel_recomputed", "claimbench_adjudicated", "submitter_asserted", "llm_proposed"}
CERTIFYING_GATE_SOURCES = {"kernel_recomputed", "claimbench_adjudicated"}


class GateSource(str, Enum):
    KERNEL_RECOMPUTED = "kernel_recomputed"
    CLAIMBENCH_ADJUDICATED = "claimbench_adjudicated"
    SUBMITTER_ASSERTED = "submitter_asserted"
    LLM_PROPOSED = "llm_proposed"


@dataclass
class GateValue:
    status: str
    source: str = GateSource.SUBMITTER_ASSERTED.value
    producer: str = "submitter"
    reason: str = ""

    @classmethod
    def from_raw(cls, raw: Any) -> "GateValue":
        """Parse either legacy scalar gates or v2.1 structured gates.

        Legacy scalar gates are kept valid for backward compatibility, but are
        explicitly treated as submitter_asserted unless the deterministic kernel
        recomputes the gate later in admission.py.
        """
        if isinstance(raw, dict):
            status = _normalize_gate_status(raw.get("status", raw.get("value", "unknown")))
            source = str(raw.get("source", GateSource.SUBMITTER_ASSERTED.value))
            if source not in VALID_GATE_SOURCES:
                source = GateSource.SUBMITTER_ASSERTED.value
            producer = str(raw.get("producer", "submitter"))
            reason = str(raw.get("reason", ""))
            return cls(status=status, source=source, producer=producer, reason=reason)
        return cls(status=_normalize_gate_status(raw))

    def to_dict(self) -> Dict[str, str]:
        return {
            "status": self.status,
            "source": self.source,
            "producer": self.producer,
            "reason": self.reason,
        }

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def failed(self) -> bool:
        return self.status == "fail"

    @property
    def certifying(self) -> bool:
        return self.source in CERTIFYING_GATE_SOURCES


def _normalize_gate_status(value: Any) -> str:
    if value in PASS_VALUES or str(value).lower() in PASS_VALUES:
        return "pass"
    if value in FAIL_VALUES or str(value).lower() in FAIL_VALUES:
        return "fail"
    if value is None:
        return "missing"
    text = str(value).lower()
    if text in VALID_GATE_STATUSES:
        return text
    return "unknown"


@dataclass
class ClaimRecordSpan:
    id: str
    source: str
    text: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClaimRecordSpan":
        return cls(id=str(data["id"]), source=str(data.get("source", "")), text=str(data.get("text", "")))


@dataclass
class Verdict:
    status: str
    summary: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Verdict":
        return cls(
            status=str(data.get("status", "")).lower(),
            summary=str(data.get("summary", "")),
            metrics=dict(data.get("metrics", {}) or {}),
        )


@dataclass
class Admission:
    status: str
    gates: Dict[str, GateValue] = field(default_factory=dict)
    reason: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Admission":
        raw_gates = dict(data.get("gates", {}) or {})
        gates = {str(name): GateValue.from_raw(value) for name, value in raw_gates.items()}
        return cls(
            status=str(data.get("status", "")).lower(),
            gates=gates,
            reason=str(data.get("reason", "")),
        )

    @property
    def gate_failures(self) -> List[str]:
        return [gate for gate in ADMISSION_GATES if gate in self.gates and self.gates[gate].failed]

    @property
    def missing_gates(self) -> List[str]:
        if self.status != "admitted":
            return []
        return [gate for gate in ADMISSION_GATES if gate not in self.gates]

    def all_gates_pass_as_asserted(self) -> bool:
        if self.status != "admitted" or self.missing_gates:
            return False
        return all(self.gates[gate].passed for gate in ADMISSION_GATES)


@dataclass
class Formalization:
    id: str
    role: str
    kind: str
    description: str
    grounding_spans: List[str]
    changed_primitives: List[str]
    admission: Admission
    verdict: Verdict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Formalization":
        return cls(
            id=str(data["id"]),
            role=str(data.get("role", "")).lower(),
            kind=str(data.get("kind", "semantic")).lower(),
            description=str(data.get("description", "")),
            grounding_spans=[str(x) for x in data.get("grounding_spans", [])],
            changed_primitives=[str(x) for x in data.get("changed_primitives", [])],
            admission=Admission.from_dict(data.get("admission", {}) or {}),
            verdict=Verdict.from_dict(data.get("verdict", {}) or {}),
        )


@dataclass
class ClaimPackage:
    raw: Dict[str, Any]
    metadata: Dict[str, Any]
    claim: Dict[str, Any]
    scope: Dict[str, Any]
    verifier: Dict[str, Any]
    formalizations: List[Formalization]
    evidence: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClaimPackage":
        return cls(
            raw=data,
            metadata=dict(data.get("metadata", {}) or {}),
            claim=dict(data.get("claim", {}) or {}),
            scope=dict(data.get("scope", {}) or {}),
            verifier=dict(data.get("verifier", {}) or {}),
            formalizations=[Formalization.from_dict(x) for x in data.get("formalizations", [])],
            evidence=dict(data.get("evidence", {}) or {}),
        )

    @property
    def record_span_ids(self) -> set[str]:
        return {str(s.get("id")) for s in self.claim.get("record", [])}

    @property
    def has_frozen_record(self) -> bool:
        return bool(self.claim.get("frozen_at")) and bool(self.claim.get("record"))
