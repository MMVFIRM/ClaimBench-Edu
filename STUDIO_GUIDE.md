# ClaimBench v2.1 Formalizer Interface

The formalizer layer generates draft formalizations from a frozen claim brief. It does not certify them.

## Doctrine

LLMs propose. ClaimBench adjudicates. The deterministic kernel tabulates. Signatures preserve integrity.

Formalizer-generated gates should use:

```yaml
source: llm_proposed
```

`llm_proposed` gates are non-certifying. A generated package will normally evaluate to **Self-Attested Only** until a separate adjudication process promotes certification-critical gates to `claimbench_adjudicated`.

## Provider modes

### mock

Offline deterministic provider for demos and tests.

```bash
claimbench formalize examples/formalizer_brief.yaml --provider mock --out examples/generated_from_formalizer.yaml --evaluate
```

### command

Runs a local command. The command receives the brief as JSON on stdin and must emit either `{"formalizations": [...]}` or a bare list.

```bash
claimbench formalize examples/formalizer_brief.yaml --provider command --command "python my_formalizer.py" --out generated.yaml
```

### http-json

POSTs the brief as JSON to a user-provided endpoint. The endpoint must return `{"formalizations": [...]}` or a bare list.

```bash
claimbench formalize examples/formalizer_brief.yaml --provider http-json --endpoint http://localhost:8000/formalize --out generated.yaml
```

## Formalizer brief shape

A formalizer brief includes `metadata`, `claim`, `scope`, `verifier`, and optional `evidence`.

The formalizer fills in `formalizations`.
