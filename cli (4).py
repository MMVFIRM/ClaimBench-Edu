"""Baseline null-reconstructor v0.1 for real-corpus validation.

This module is intentionally simple and conservative. It is not a service-key-
ready adjudicator. It exists so the real-corpus validation pipeline can measure
known failure modes and enforce that no synthetic/non-human data authorizes trust.

Supported claim class: comparative_empirical.
Supported verdicts: pass, fail, semantic_boundary, evidentiary_inconclusive, out_of_scope.

Strictness modes:
  - lenient: trusts self-reported baseline fairness when `fair: true`.
  - strict_fairness: refuses decisive certification unless at least one fair
    baseline is independently verified.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

VALID_VERDICTS = {"pass", "fail", "semantic_boundary", "evidentiary_inconclusive", "out_of_scope"}


def _num(x: Any):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _beats(method_score: float, baseline_score: float, higher_better: bool) -> bool:
    return method_score > baseline_score if higher_better else method_score < baseline_score


def _material_margin(method_score: float, baseline_score: float, method_std=None, baseline_std=None) -> bool:
    """Simple conservative separation check.

    If both stds are present, require improvement greater than combined std.
    If stds are missing, any nonzero margin is considered separable for this
    baseline v0.1. Real deployments should replace this with a declared
    statistical procedure.
    """
    margin = abs(method_score - baseline_score)
    ms, bs = _num(method_std), _num(baseline_std)
    if ms is not None and bs is not None:
        return margin > (ms + bs)
    return margin > 0


def adjudicate(
    claim_class: str,
    evidence: Dict[str, Any],
    alternative_readings: List[Dict[str, Any]] | None = None,
    strictness: str = "strict_fairness",
) -> Tuple[str, str]:
    """Return (verdict, reason) for a structured evidence record."""
    alternative_readings = alternative_readings or []

    if claim_class != "comparative_empirical":
        return "out_of_scope", f"Unsupported claim_class={claim_class!r}."

    # Genuine semantic boundary only when the extraction already carries admitted
    # alternative readings. This baseline does not admit new alternatives.
    admitted = [a for a in alternative_readings if a.get("admitted") is True]
    alt_verdicts = {a.get("verdict") for a in admitted if a.get("verdict") in VALID_VERDICTS}
    if len({v for v in alt_verdicts if v in {"pass", "fail"}}) > 1:
        return "semantic_boundary", "Admitted semantic alternatives diverge."

    metric = evidence.get("metric", {}) or {}
    method = evidence.get("method", {}) or {}
    baselines = list(evidence.get("baselines", []) or [])
    higher_better = bool(metric.get("higher_better", True))
    method_score = _num(method.get("score"))

    if method_score is None or not baselines:
        return "evidentiary_inconclusive", "Missing method score or baselines."

    fair_baselines = []
    for b in baselines:
        if not bool(b.get("fair", False)):
            continue
        if strictness == "strict_fairness" and b.get("fairness_source") != "independently_verified":
            continue
        if _num(b.get("score")) is None:
            continue
        fair_baselines.append(b)

    if not fair_baselines:
        return "evidentiary_inconclusive", "No scoreable fair baseline under strictness policy."

    # For a comparative claim to pass, the method must beat every scoreable fair
    # baseline by a separable margin. If any scoreable fair baseline beats or ties
    # it materially, the claim fails.
    any_inconclusive = False
    for b in fair_baselines:
        baseline_score = _num(b.get("score"))
        if baseline_score is None:
            any_inconclusive = True
            continue
        separated = _material_margin(method_score, baseline_score, method.get("std"), b.get("std"))
        if not separated:
            any_inconclusive = True
            continue
        if not _beats(method_score, baseline_score, higher_better):
            return "fail", f"Method score {method_score} does not beat fair baseline {b.get('name')}={baseline_score}."

    if any_inconclusive:
        return "evidentiary_inconclusive", "At least one scoreable fair baseline is not statistically/separably resolved."

    return "pass", "Method beats all scoreable fair baselines under the declared policy."
