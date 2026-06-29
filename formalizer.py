from __future__ import annotations

from typing import Any

from .engine import EvaluationResult


def _md_table(rows: list[list[Any]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(out)


def render_markdown_certificate(result: EvaluationResult, signed: bool = False) -> str:
    p = result.package
    lines: list[str] = []
    lines.append(f"# ClaimBench Certificate: {result.badge.value}")
    lines.append("")
    lines.append(f"**Claim ID:** {p.metadata.get('claim_id', '')}")
    lines.append(f"**Title:** {p.metadata.get('title', '')}")
    lines.append(f"**Owner:** {p.metadata.get('owner', '')}")
    lines.append(f"**Package Version:** {p.metadata.get('version', '')}")
    lines.append(f"**Standard Version:** {p.scope.get('standard_version', '')}")
    lines.append(f"**Kernel Version:** {result.to_core_dict().get('kernel_version')}")
    lines.append(f"**Certificate Core Hash:** `{result.core_hash()}`")
    lines.append(f"**Evaluated At:** {result.evaluated_at} *(run envelope; excluded from core hash)*")
    lines.append(f"**Certificate Core Signed:** {'yes' if signed else 'no'}")
    lines.append(f"**Claim Class:** {p.scope.get('claim_class', '')}")
    lines.append("")
    lines.append("## Badge")
    lines.append("")
    lines.append(f"**{result.badge.value}** — {result.explanation}")
    lines.append("")
    lines.append(f"**Rationale:** {result.rationale}")
    if result.projected_badge and result.projected_badge != result.badge:
        lines.append("")
        lines.append(f"**Non-certifying-contingent badge:** {result.projected_badge.value}")
        lines.append(f"**Non-certifying-contingent rationale:** {result.projected_rationale}")
    lines.append("")
    lines.append("## Claim")
    lines.append("")
    lines.append(f"> {p.claim.get('statement', '')}")
    lines.append("")
    lines.append("## Materiality")
    lines.append("")
    lines.append(str(p.scope.get("materiality", "")))
    lines.append("")
    lines.append("## Verifier")
    lines.append("")
    lines.append(_md_table([
        ["ID", p.verifier.get("id", "")],
        ["Type", p.verifier.get("type", "")],
        ["Pass Condition", p.verifier.get("pass_condition", "")],
    ], ["Field", "Value"]))
    lines.append("")
    lines.append("## Frozen Claim Record")
    lines.append("")
    record_rows = [[s.get("id", ""), s.get("source", ""), s.get("text", "")] for s in p.claim.get("record", [])]
    lines.append(_md_table(record_rows, ["Span", "Source", "Text"]))
    lines.append("")
    lines.append("## Formalizations")
    lines.append("")
    form_rows = []
    findings_by_id = {x.formalization_id: x for x in result.admission_findings}
    for f in p.formalizations:
        finding = findings_by_id.get(f.id)
        asserted = "yes" if finding and finding.asserted_admitted else "no"
        certified = "yes" if finding and finding.certified_admitted else "no"
        reason = finding.reason if finding else ""
        form_rows.append([
            f.id,
            f.role,
            f.kind,
            asserted,
            certified,
            f.verdict.status,
            f.verdict.summary,
            reason,
        ])
    lines.append(_md_table(form_rows, ["ID", "Role", "Kind", "Asserted Admitted", "Certified Admitted", "Verdict", "Summary", "Admission Rationale"]))
    lines.append("")
    lines.append("## Admission Findings")
    lines.append("")
    admission_rows = []
    for finding in result.admission_findings:
        admission_rows.append([
            finding.formalization_id,
            finding.asserted_admitted,
            finding.certified_admitted,
            ", ".join(finding.missing_gates) or "-",
            ", ".join(finding.failed_gates) or "-",
            ", ".join(finding.uncertified_gates) or "-",
            ", ".join(finding.unknown_spans) or "-",
            finding.reason,
        ])
    lines.append(_md_table(admission_rows, ["Formalization", "Asserted", "Certified", "Missing Gates", "Failed Gates", "Uncertified Gates", "Unknown Spans", "Reason"]))
    lines.append("")
    lines.append("## Gate Provenance")
    lines.append("")
    gate_rows = []
    for finding in result.admission_findings:
        for gate in finding.gate_findings:
            gate_rows.append([
                finding.formalization_id,
                gate.gate,
                gate.status,
                gate.source,
                gate.producer,
                gate.certifying,
                gate.reason or "-",
            ])
    lines.append(_md_table(gate_rows, ["Formalization", "Gate", "Status", "Source", "Producer", "Certifying", "Reason"]))
    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    if p.evidence:
        for key, value in p.evidence.items():
            lines.append(f"- **{key}:** {value}")
    else:
        lines.append("No additional evidence metadata supplied.")
    lines.append("")
    lines.append("## Replay")
    lines.append("")
    lines.append("The certificate core is deterministic and hashable. The timestamp appears only in the run envelope and is excluded from the core hash. In v2.1, the certificate core may be signed with Ed25519; verification checks the signature over the canonical certificate core, not over run metadata.")
    lines.append("")
    lines.append("## Doctrine")
    lines.append("")
    lines.append("ClaimBench certifies only readings the frozen claim record can bear. Candidate alternatives that lack textual grounding, alter evidence rather than meaning, or exist only to change the verdict are disclosed but excluded from the badge calculation. Submitter-asserted and LLM-proposed gates are disclosed as non-certifying provenance and do not support a ClaimBench-certified badge.")
    lines.append("")
    return "\n".join(lines)
