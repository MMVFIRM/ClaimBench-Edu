# Human label template — the GROUND TRUTH column. A human fills this after
# reading the paper. labeled_by_model MUST stay false.
labels:
  - record_id: "CB-REAL-0001"
    verdict: ""                        # pass | fail | semantic_boundary | evidentiary_inconclusive | out_of_scope
    claim_class: comparative_empirical
    rationale: ""                      # why, in your words, grounded in the paper
    confidence: ""                     # high | medium | low
    reviewer_id: "your-id"
    review_status: single_reviewer_label   # single_reviewer_label | panel_confirmed_label | disputed_label | needs_panel_review
    labeled_by_model: false
