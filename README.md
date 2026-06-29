# SMOKE / ILLUSTRATIVE ONLY — not real papers, not real ground truth.
# Exists solely to exercise the pipeline and prove the guards fire.
# Real records replace these and the runner sets is_synthetic=False.
records:
  - id: SMOKE-1
    paper_id: "0000.00001"
    title: "Illustrative metric-comparison claim"
    claim_statement: "Method beats the standard baseline on top-1 accuracy."
    claim_class: comparative_empirical
    subclass: metric_comparison
    extraction_provenance: human
    extracted_by: SMOKE
    evidence:
      metric: {name: top1, higher_better: true}
      method: {score: 90.1, std: 0.2, n_seeds: 3}
      baselines: [{name: public-baseline, score: 86.0, std: 0.2, fair: true, fairness_source: independently_verified}]
      budget: {claimed: false}
      ablations_present: true
    evidence_spans: [{id: S1, text: "we report 90.1 vs 86.0 top-1"}]
  - id: SMOKE-2
    paper_id: "0000.00002"
    title: "Illustrative budget-normalized claim"
    claim_statement: "Method beats baseline under equal parameter budget."
    claim_class: comparative_empirical
    subclass: budget_normalized
    extraction_provenance: human
    extracted_by: SMOKE
    evidence:
      metric: {name: acc, higher_better: true}
      method: {score: 84.0, std: 0.3, n_seeds: 3}
      baselines: [{name: matched, score: 86.0, std: 0.3, fair: true, fairness_source: independently_verified}]
      budget: {claimed: true, matched: true}
      ablations_present: true
    evidence_spans: [{id: S1, text: "84.0 vs 86.0 at equal params"}]
  - id: SMOKE-3
    paper_id: "0000.00003"
    title: "Illustrative — extraction not human-verified (G1 should exclude)"
    claim_statement: "Method beats baseline."
    claim_class: comparative_empirical
    subclass: metric_comparison
    extraction_provenance: llm_unverified
    extracted_by: some-llm
    evidence:
      metric: {name: acc, higher_better: true}
      method: {score: 88.0, std: 0.2, n_seeds: 3}
      baselines: [{name: b, score: 85.0, std: 0.2, fair: true, fairness_source: self_reported}]
      budget: {claimed: false}
      ablations_present: true
    evidence_spans: []
  - id: SMOKE-4
    paper_id: "0000.00004"
    title: "Illustrative — too ambiguous for single-reviewer truth (G3)"
    claim_statement: "Our approach is more efficient in practice."
    claim_class: comparative_empirical
    subclass: metric_comparison
    extraction_provenance: human
    extracted_by: SMOKE
    evidence:
      metric: {name: efficiency, higher_better: true}
      method: {score: 1.0, n_seeds: 1}
      baselines: []
      budget: {claimed: false}
      ablations_present: false
    evidence_spans: [{id: S1, text: "more efficient in practice"}]
