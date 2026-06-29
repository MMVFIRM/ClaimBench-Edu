"""Real-corpus scorer and service-key eligibility report.

Guards, in order of how badly they bite if violated:

  G1 (contamination): a case is SCORED only if its extraction is human or
     human-verified AND its label is human ground truth. Cases failing this are
     excluded from rates and reported separately. This prevents a model-correlated
     truth/extraction column from flattering false-certify toward zero.

  G2 (no-synthetic-key): a service-key recommendation may be emitted ONLY from a
     corpus of real, human-labeled cases meeting a minimum count. Synthetic or
     under-labeled corpora can score, but the report's key recommendation is
     forced to "BLOCKED — insufficient real ground truth".

  G3 (ambiguity honesty): needs_panel_review / disputed cases never enter the
     truth set; they are surfaced as the ambiguity surface, which is itself a
     finding (claims a single reviewer can't adjudicate are claims the machine
     certainly shouldn't certify).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .model import HumanLabel, PaperRecord, ReviewStatus

# Minimum human-labeled, contamination-clean cases before any key recommendation.
MIN_CASES_FOR_KEY = 200          # the "gate corpus" size
MIN_CASES_PER_SUBCLASS = 30

DEFAULT_THRESHOLDS = {
    "false_certify_of_corpus_max": 0.02,
    "false_refute_of_issued_max": 0.05,
    "false_boundary_of_issued_max": 0.03,
    "coverage_min": 0.40,
}

DECISIVE = {"pass", "fail"}


@dataclass
class ScoredCase:
    record_id: str
    subclass: str
    predicted: str
    truth: str
    correct: bool


@dataclass
class CorpusAudit:
    scored: List[ScoredCase]
    excluded_unverified_extraction: List[str]
    excluded_no_truth: List[str]
    needs_panel_review: List[str]
    disputed: List[str]
    is_synthetic: bool


def build_scored(
    records: Dict[str, PaperRecord],
    labels: Dict[str, HumanLabel],
    adjudicate,
    strictness: str = "strict_fairness",
    is_synthetic: bool = False,
) -> CorpusAudit:
    scored: List[ScoredCase] = []
    excl_extraction: List[str] = []
    excl_no_truth: List[str] = []
    needs_panel: List[str] = []
    disputed: List[str] = []

    for rid, rec in records.items():
        label = labels.get(rid)
        if label is not None and label.review_status == ReviewStatus.NEEDS_PANEL_REVIEW.value:
            needs_panel.append(rid)
        if label is not None and label.review_status == ReviewStatus.DISPUTED.value:
            disputed.append(rid)

        # G1: extraction must be trustworthy.
        if not rec.extraction_scoreable:
            excl_extraction.append(rid)
            continue
        # Ground truth must exist and be human + truth-status.
        if label is None or not label.is_ground_truth:
            excl_no_truth.append(rid)
            continue

        predicted, _reason = adjudicate(
            claim_class=rec.claim_class,
            evidence=rec.evidence,
            alternative_readings=rec.alternative_readings,
            strictness=strictness,
        )
        scored.append(
            ScoredCase(
                record_id=rid,
                subclass=rec.subclass,
                predicted=predicted,
                truth=label.verdict,
                correct=(predicted == label.verdict),
            )
        )

    return CorpusAudit(
        scored=scored,
        excluded_unverified_extraction=excl_extraction,
        excluded_no_truth=excl_no_truth,
        needs_panel_review=needs_panel,
        disputed=disputed,
        is_synthetic=is_synthetic,
    )


def _rate(num: int, den: int) -> float:
    return (num / den) if den else 0.0


def score(scored: List[ScoredCase]) -> Dict[str, Any]:
    n = len(scored)
    issued_pass = [s for s in scored if s.predicted == "pass"]
    issued_fail = [s for s in scored if s.predicted == "fail"]
    issued_boundary = [s for s in scored if s.predicted == "semantic_boundary"]
    fc = [s for s in issued_pass if s.truth != "pass"]
    fr = [s for s in issued_fail if s.truth != "fail"]
    fb = [s for s in issued_boundary if s.truth != "semantic_boundary"]
    decisive = [s for s in scored if s.predicted in DECISIVE]
    return {
        "n": n,
        "false_certify_of_corpus": _rate(len(fc), n),
        "false_certify_of_issued": _rate(len(fc), len(issued_pass)),
        "false_certify_ids": [s.record_id for s in fc],
        "false_refute_of_issued": _rate(len(fr), len(issued_fail)),
        "false_boundary_of_issued": _rate(len(fb), len(issued_boundary)),
        "coverage": _rate(len(decisive), n),
    }


def gate(m: Dict[str, Any], thresholds: Dict[str, float] = DEFAULT_THRESHOLDS) -> Dict[str, Any]:
    checks = {
        "false_certify_of_corpus": m["false_certify_of_corpus"] <= thresholds["false_certify_of_corpus_max"],
        "false_refute_of_issued": m["false_refute_of_issued"] <= thresholds["false_refute_of_issued_max"],
        "false_boundary_of_issued": m["false_boundary_of_issued"] <= thresholds["false_boundary_of_issued_max"],
        "coverage": m["coverage"] >= thresholds["coverage_min"],
    }
    return {"passed": all(checks.values()), "failed": [k for k, v in checks.items() if not v]}


def by_subclass(scored: List[ScoredCase]) -> Dict[str, List[ScoredCase]]:
    g: Dict[str, List[ScoredCase]] = defaultdict(list)
    for s in scored:
        g[s.subclass].append(s)
    return dict(g)


def key_recommendation(audit: CorpusAudit, thresholds: Dict[str, float] = DEFAULT_THRESHOLDS) -> Dict[str, Any]:
    """G2: the load-bearing guard. No key from synthetic or under-labeled data."""
    n = len(audit.scored)

    if audit.is_synthetic:
        return {
            "service_key": "BLOCKED",
            "reason": "No Machine-Adjudicated service key may be issued from synthetic-only validation.",
            "eligible_subclasses": [],
        }
    if n < MIN_CASES_FOR_KEY:
        return {
            "service_key": "BLOCKED",
            "reason": f"Only {n} contamination-clean human-labeled cases; need >= {MIN_CASES_FOR_KEY} (gate corpus).",
            "eligible_subclasses": [],
        }

    eligible = []
    blocked = {}
    for sub, rs in by_subclass(audit.scored).items():
        if len(rs) < MIN_CASES_PER_SUBCLASS:
            blocked[sub] = f"insufficient cases ({len(rs)} < {MIN_CASES_PER_SUBCLASS})"
            continue
        g = gate(score(rs), thresholds)
        if g["passed"]:
            eligible.append(sub)
        else:
            blocked[sub] = "failed: " + ",".join(g["failed"])

    return {
        "service_key": "ELIGIBLE (scoped)" if eligible else "BLOCKED",
        "reason": "Per-subclass gate evaluated on real human-labeled cases." if eligible
        else "No subclass cleared the gate on real data.",
        "eligible_subclasses": eligible,
        "blocked_subclasses": blocked,
    }
