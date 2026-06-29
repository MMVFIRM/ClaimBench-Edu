# ClaimBench Edu v0.1

**ClaimBench Edu** is the free and open-source academic edition of the ClaimBench Suite. It packages the ClaimBench deterministic certificate kernel, real-corpus validation guards, and a local human-in-the-loop web UI called **ClaimBench Studio**.

The product doctrine is simple:

> The machine proposes. The human adjudicates. Training data improves the adjudicator. Validation data decides whether the adjudicator deserves authority.

ClaimBench Edu is intended for universities, labs, students, reviewers, and open research teams who want to turn paper claims into structured, contestable adjudication records without pretending a model-generated label is ground truth.

## What is included

- **ClaimBench Core v2.1**
  - deterministic badge kernel
  - signed certificate cores
  - conformance/reproduction verifier
  - red-team harness from the prior suite

- **Real-corpus validation v0.1**
  - contamination guards
  - human-label templates
  - synthetic smoke test that cannot authorize a service key

- **ClaimBench Studio v0.1**
  - local browser UI
  - upload a paper or text file
  - extract candidate claims
  - grade claims from structured evidence
  - human Certify / Override / Abstain / Needs Panel Review
  - export RLHF training JSONL
  - export validation labels separately
  - create adjudication artifacts
  - optional Ed25519 signatures for local academic artifacts

## Install

```bash
python -m pip install -e .
```

Optional PDF extraction:

```bash
python -m pip install -e .[pdf]
```

Without the optional PDF dependency, PDFs are still stored, but claim text must be entered manually or uploaded as `.txt` / `.md`.

## Run Studio

```bash
claimbench-edu studio --workspace claimbench_edu_workspace --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

## Human workflow

1. Upload a paper.
2. Review extracted claim candidates.
3. Add/edit one claim card.
4. Enter metric, method score, baseline score, and fairness source.
5. Let the system produce a **machine-proposed** grade.
6. Human selects:
   - Certify proposal
   - Override
   - Abstain
   - Needs panel review
   - Disputed
7. Human chooses dataset split:
   - training
   - validation
   - panel
   - disputed
   - do_not_use
8. Studio writes:
   - adjudication artifact
   - `exports/rlhf_training.jsonl`
   - optional validation/panel/disputed labels

## Critical trust boundary

ClaimBench Edu does **not** allow model-produced labels to become ground truth.

Training rows may improve a future adjudicator. Validation rows measure it. Panel-confirmed rows can become stronger gold labels. These streams are physically separated.

## Commands

```bash
claimbench-edu init --workspace claimbench_edu_workspace
claimbench-edu studio --workspace claimbench_edu_workspace
claimbench-edu exports --workspace claimbench_edu_workspace
claimbench validate examples/agent_safety_verified.yaml
claimbench evaluate examples/geodistill_semantic_boundary.yaml --out reports
```

## Academic positioning

ClaimBench Edu is not the commercial certification service. It is the open academic loop that lets researchers build, contest, and share claim adjudication datasets.

The commercial-grade service key remains blocked until real human-labeled validation proves the adjudicator's false-certify rate is low enough under a declared claim class.

## License

MIT. See `LICENSE`.

