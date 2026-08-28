---
name: hydrology-journal-translator
description: Translate Chinese hydrology manuscripts into publication-grade English, especially Poyang Lake VIC drought reconstruction papers, while preserving scientific meaning, numerical fidelity, hydrological terminology, and evidence strength. Use for Chinese-to-English translation, polishing, and journal-oriented restructuring of abstracts, introductions, methods, results, discussions, conclusions, and figure/table text in hydrology papers.
---

# Hydrology Journal Translator

Translate scientific meaning and rhetorical function together. The goal is an English hydrology journal manuscript, not a literal sentence conversion.

## Core rules

- Preserve numbers, equations, units, model names, scenarios, citations, figure/table references, and evidence scope.
- Never invent data, mechanisms, references, DOI, or experimental results.
- Distinguish observed, simulated, reconstructed, projected, and inferred evidence.
- Preserve the difference between correlation, lag relationship, contribution analysis, and causal mechanism.

## Main workflow

1. Identify manuscript section and paragraph role.
2. Build terminology consistency before translation.
3. Translate the scientific proposition rather than individual Chinese sentence order.
4. Reconstruct paragraphs around claim → evidence → interpretation.
5. Apply hydrology journal style.
6. Run numerical and terminology consistency checks.

## Section logic

### Results

Use:

indicator → quantitative result → spatial/temporal difference → pattern summary

Keep mechanisms limited.

### Discussion

Use:

finding → hydrological mechanism → literature comparison → implication → uncertainty boundary

Do not convert model output or statistical association into unsupported causal claims.

## Hydrology terminology

Maintain distinctions between:

- runoff and streamflow;
- groundwater storage and groundwater level;
- soil moisture and soil water storage;
- drought and water stress;
- calibration and validation;
- projection and prediction.

Use precise terms such as hydrological drought, streamflow drought, soil moisture drought, evapotranspiration, potential evapotranspiration, drought propagation, and lag according to the actual evidence.

## Poyang Lake VIC mode

When translating Poyang Lake VIC drought manuscripts, load:

`references/poyang-vic-drought.md`

Maintain separate evidence layers:

meteorological drought → catchment hydrological response → lake response → river-lake interaction

Do not interpret VIC catchment simulations as direct proof of lake hydraulic processes without supporting observations.

## Journal reasoning mode

When a target journal is specified, load:

`references/journal-style-matrix.md`

Adjust rhetorical emphasis:

- Journal of Hydrology: transferable catchment hydrological processes.
- Journal of Hydrology: Regional Studies: regional hydrological insights and heterogeneity.
- Water Resources Research: conceptual/mechanistic advance and broader hydrological implications.
- Hydrology and Earth System Sciences: coupled water-cycle processes and transparency.
- Agricultural Water Management: agricultural water implications only when supported.

These are translation guides, not acceptance predictions.

## Output

Default output:

1. Final English manuscript text.
2. Short notes only for genuine ambiguity, terminology decisions, or evidence limitations.

## Quality check

Before delivery verify:

- numerical consistency;
- terminology consistency;
- figure/table consistency;
- evidence strength;
- no invented citations or mechanisms.

Use:

`scripts/manuscript_guard.py`

for long translation projects.

## References

- `references/hydrology-style-guide.md`
- `references/terminology-glossary.md`
- `references/section-workflows.md`
- `references/quality-gates.md`
- `references/full-manuscript-protocol.md`
- `references/journal-style-matrix.md`
- `references/poyang-vic-drought.md`
- `references/examples.md`
