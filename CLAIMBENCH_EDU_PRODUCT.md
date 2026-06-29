# Paper record template — the EXTRACTION column.
# One file may hold many records under `records:`. Fill from the actual paper.
# extraction_provenance MUST be `human` or `human_verified` for the case to score.
records:
  - id: "CB-REAL-0001"                 # your corpus id
    paper_id: "ARXIV-ID"               # e.g. 2606.27242
    title: ""
    claim_statement: ""                # the exact central comparative claim
    claim_class: comparative_empirical
    subclass: metric_comparison        # or budget_normalized
    extraction_provenance: human       # human | human_verified  (llm_unverified will NOT score)
    extracted_by: "your-id"
    artifact_links: []                 # code/data if shipped
    evidence:
      metric: {name: "", higher_better: true}
      method: {score: null, std: null, n_seeds: null}
      baselines:
        - name: ""
          score: null
          std: null
          fair: true                   # is this a fair comparison baseline?
          fairness_source: self_reported   # self_reported | independently_verified
      budget: {claimed: false, matched: false, kind: ""}
      ablations_present: false
    evidence_spans:                    # verbatim spans backing every number above
      - {id: S1, text: ""}
    alternative_readings: []           # for genuine semantic-boundary claims only
