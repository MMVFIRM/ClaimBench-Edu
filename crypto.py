from __future__ import annotations

from typing import Any, Dict, List

from .models import ADMISSION_GATES, VALID_GATE_SOURCES, ClaimPackage

REQUIRED_TOP = ["metadata", "claim", "scope", "verifier", "formalizations"]
REQUIRED_METADATA = ["claim_id", "title", "owner", "version"]
REQUIRED_CLAIM = ["statement", "record"]
REQUIRED_SCOPE = ["standard_version", "claim_class", "materiality"]
REQUIRED_VERIFIER = ["id", "type", "pass_condition"]
VALID_VERDICTS = {"pass", "fail", "inconclusive"}
VALID_ADMISSION = {"admitted", "rejected"}
VALID_KIND = {"semantic", "evidentiary", "out_of_scope"}
VALID_ROLE = {"canonical", "alternative"}


def validate_claim_package(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in REQUIRED_TOP:
        if key not in data:
            errors.append(f"Missing top-level key: {key}")
    if errors:
        return errors

    for key in REQUIRED_METADATA:
        if key not in data.get("metadata", {}):
            errors.append(f"metadata missing required key: {key}")
    for key in REQUIRED_CLAIM:
        if key not in data.get("claim", {}):
            errors.append(f"claim missing required key: {key}")
    for key in REQUIRED_SCOPE:
        if key not in data.get("scope", {}):
            errors.append(f"scope missing required key: {key}")
    for key in REQUIRED_VERIFIER:
        if key not in data.get("verifier", {}):
            errors.append(f"verifier missing required key: {key}")

    package = ClaimPackage.from_dict(data)
    if not package.formalizations:
        errors.append("At least one formalization is required.")

    span_ids = package.record_span_ids
    if not span_ids:
        errors.append("claim.record must include at least one span with an id.")

    seen_ids = set()
    for f in package.formalizations:
        if f.id in seen_ids:
            errors.append(f"Duplicate formalization id: {f.id}")
        seen_ids.add(f.id)
        if f.role not in VALID_ROLE:
            errors.append(f"{f.id}: invalid role '{f.role}'")
        if f.kind not in VALID_KIND:
            errors.append(f"{f.id}: invalid kind '{f.kind}'")
        if f.verdict.status not in VALID_VERDICTS:
            errors.append(f"{f.id}: invalid verdict status '{f.verdict.status}'")
        if f.admission.status not in VALID_ADMISSION:
            errors.append(f"{f.id}: invalid admission status '{f.admission.status}'")
        unknown = [s for s in f.grounding_spans if s not in span_ids]
        if unknown:
            errors.append(f"{f.id}: unknown grounding span(s): {', '.join(unknown)}")
        if f.admission.status == "admitted":
            missing = [gate for gate in ADMISSION_GATES if gate not in f.admission.gates]
            if missing:
                errors.append(f"{f.id}: admitted formalization missing gates: {', '.join(missing)}")
        for gate_name, gate in f.admission.gates.items():
            if gate_name not in ADMISSION_GATES:
                errors.append(f"{f.id}: unknown admission gate '{gate_name}'")
            if gate.source not in VALID_GATE_SOURCES:
                errors.append(f"{f.id}: gate '{gate_name}' has invalid source '{gate.source}'")

    return errors
