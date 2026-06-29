#!/usr/bin/env python3
"""Run the real-corpus validation pipeline and print the service-key decision.

Usage:
    PYTHONPATH=<dir-containing-validation-and-realcorpus> \
        python realcorpus/run_realcorpus.py \
        --papers realcorpus/papers/smoke_papers.yaml \
        --labels realcorpus/labels/smoke_labels.yaml \
        --synthetic

Drop the --synthetic flag only when papers are real and human-labeled. Even then,
the scorer refuses a key recommendation below the gate-corpus size.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

# Make sibling packages importable regardless of CWD.
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from validation.null_reconstructor import adjudicate  # the procedure under test
from realcorpus.model import PaperRecord, HumanLabel
from realcorpus.scorer import build_scored, score, gate, by_subclass, key_recommendation


def pct(x: float) -> str:
    return f"{100*x:.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--strictness", default="strict_fairness", choices=["lenient", "strict_fairness"])
    ap.add_argument("--synthetic", action="store_true",
                    help="Mark this corpus synthetic; forces service_key=BLOCKED.")
    args = ap.parse_args()

    records = {
        r["id"]: PaperRecord.from_dict(r)
        for r in yaml.safe_load(Path(args.papers).read_text())["records"]
    }
    labels = {
        l["record_id"]: HumanLabel.from_dict(l)
        for l in yaml.safe_load(Path(args.labels).read_text())["labels"]
    }

    audit = build_scored(records, labels, adjudicate,
                         strictness=args.strictness, is_synthetic=args.synthetic)

    print("=" * 70)
    print("ClaimBench Real-Corpus Validation")
    print(f"papers={len(records)}  labels={len(labels)}  strictness={args.strictness}  synthetic={args.synthetic}")
    print("=" * 70)

    print("\nContamination & ambiguity audit (cases NOT scored):")
    print(f"  excluded — extraction not human/verified : {audit.excluded_unverified_extraction}")
    print(f"  excluded — no human ground truth         : {audit.excluded_no_truth}")
    print(f"  needs_panel_review (ambiguity surface)   : {audit.needs_panel_review}")
    print(f"  disputed                                 : {audit.disputed}")
    print(f"  -> SCORED (clean): {len(audit.scored)} case(s): {[s.record_id for s in audit.scored]}")

    if audit.scored:
        m = score(audit.scored)
        print("\nScored metrics (on the clean set only):")
        print(f"  false-certify (of corpus) : {pct(m['false_certify_of_corpus'])}  ids={m['false_certify_ids']}")
        print(f"  false-certify (of issued) : {pct(m['false_certify_of_issued'])}")
        print(f"  false-refute  (of issued) : {pct(m['false_refute_of_issued'])}")
        print(f"  coverage                  : {pct(m['coverage'])}")
        for sub, rs in by_subclass(audit.scored).items():
            sm = score(rs)
            print(f"    {sub:20s} n={len(rs):2d}  fc(corpus)={pct(sm['false_certify_of_corpus']):>6s}  cov={pct(sm['coverage']):>6s}")

    rec = key_recommendation(audit)
    print("\n" + "-" * 70)
    print("SERVICE-KEY DECISION")
    print(f"  service_key            : {rec['service_key']}")
    print(f"  reason                 : {rec['reason']}")
    print(f"  eligible_subclasses    : {rec.get('eligible_subclasses')}")
    if rec.get("blocked_subclasses"):
        print(f"  blocked_subclasses     : {rec['blocked_subclasses']}")
    print("-" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
