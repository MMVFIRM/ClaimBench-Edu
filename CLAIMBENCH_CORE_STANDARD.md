# SMOKE labels (reviewer_id: SMOKE). Not real ground truth.
labels:
  - {record_id: SMOKE-1, verdict: pass, claim_class: comparative_empirical, rationale: "Large margin over verified baseline.", confidence: high, reviewer_id: SMOKE, review_status: single_reviewer_label, labeled_by_model: false}
  - {record_id: SMOKE-2, verdict: fail, claim_class: comparative_empirical, rationale: "Below matched-budget baseline.", confidence: high, reviewer_id: SMOKE, review_status: single_reviewer_label, labeled_by_model: false}
  - {record_id: SMOKE-3, verdict: pass, claim_class: comparative_empirical, rationale: "(excluded: extraction llm_unverified)", confidence: medium, reviewer_id: SMOKE, review_status: single_reviewer_label, labeled_by_model: false}
  - {record_id: SMOKE-4, verdict: out_of_scope, claim_class: comparative_empirical, rationale: "Single reading insufficient; to panel.", confidence: low, reviewer_id: SMOKE, review_status: needs_panel_review, labeled_by_model: false}
