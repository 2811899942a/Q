---
name: hydrology-journal-translator
description: Translate and polish Chinese hydrology, water-resources, hydroclimate, drought, agricultural-water, and watershed-model manuscripts into publication-grade English while preserving scientific meaning, numbers, equations, citations, model/scenario names, and evidence strength. Use for Chinese-to-English translation or English revision of titles, highlights, abstracts, introductions, methods, results, discussions, conclusions, figure/table text, reviewer responses, and full manuscripts involving SWAT/SWAT+, VIC, DSSAT, CMIP6, GEE, PLUS, drought indices, streamflow, evapotranspiration, soil moisture, groundwater, or related water-science topics. Apply journal-style rhetorical restructuring, terminology normalization, Results/Discussion boundary control, and deterministic fidelity checks for long or submission-oriented manuscripts.
---

# Hydrology Journal Translator

Translate scientific meaning and rhetorical function together. Produce English that reads as an original water-science manuscript while keeping the source evidence intact.

## Core operating rule

Treat the Chinese manuscript as the scientific authority unless the user identifies another source as authoritative. Improve language, paragraph architecture, and journal fit without changing data, equations, causal strength, scope, or conclusions.

Never invent missing values, experiments, statistics, citations, DOI values, station metadata, model settings, or mechanisms. Flag material ambiguity instead of silently filling it.

## Route the task

Choose the smallest workflow that fits the request:

| Request | Workflow |
|---|---|
| One sentence or short paragraph | Translate directly, then run terminology and fidelity checks. |
| One manuscript section | Load `references/section-workflows.md` and the relevant part of `references/hydrology-style-guide.md`. |
| Results or Discussion | Also load `references/quality-gates.md` for evidence-strength and Results/Discussion boundary checks. |
| Full manuscript or long document | Load `references/full-manuscript-protocol.md` before translating. |
| Terminology uncertainty | Load `references/terminology-glossary.md`. |
| User asks for examples or rationale | Load `references/examples.md`. |
| User asks where the workflow came from | Load `references/source-provenance.md`. |

For DOCX, PDF, LaTeX, spreadsheet, or slide files, compose with the corresponding artifact skill. Preserve the original file and create a translated copy unless the user explicitly asks to replace it.

## Translation modes

Infer the mode from the request; default to **Journal-ready**.

1. **Faithful** — preserve sentence and paragraph structure closely; improve only grammar and terminology.
2. **Journal-ready** — preserve facts while rebuilding sentence order, paragraph flow, and rhetorical emphasis for English journal prose.
3. **Polish** — revise an existing English draft for clarity, concision, terminology, and water-science style.
4. **Bilingual** — return aligned Chinese and English segments for manual checking.
5. **Audit** — inspect a translation and report mistranslation, evidence drift, terminology inconsistency, and awkward academic English.

## Non-negotiable fidelity constraints

Before improving style, freeze these items:

- all numbers, signs, decimals, percentages, ranges, dates, years, thresholds, sample sizes, p-values, confidence intervals, and uncertainty values;
- units and dimensional meaning;
- equations, variable symbols, subscripts/superscripts, and equation numbering;
- model, dataset, scenario, station, basin, gauge, algorithm, and software names;
- figure/table/equation references and citation markers;
- calibration, validation, training, testing, warm-up, baseline, and scenario periods;
- direction and magnitude of trends and biases;
- correlation versus causation;
- observed, simulated, reconstructed, projected, inferred, and scenario-based evidence states.

If the Chinese source contains an apparent error, preserve it in the translation and add a concise `AUTHOR_CHECK` note unless the user asks you to correct verified errors.

## Workflow

### 1. Classify the scientific function

Identify the manuscript section and the paragraph role before translating. Typical roles are background, gap, objective, method, evidence, spatial pattern, temporal pattern, comparison, mechanism, implication, limitation, and transition.

Do not polish sentence by sentence until the paragraph role is clear. English fluency cannot repair a paragraph whose scientific function is unclear.

### 2. Build a local terminology map

For section-length or longer text, create an internal glossary from the manuscript before translation:

- Chinese source term;
- preferred English term;
- abbreviation and first-use form;
- context-specific alternatives;
- terms that must remain unchanged.

Use `references/terminology-glossary.md` as the default. Manuscript-defined terminology takes precedence when scientifically correct and internally consistent.

### 3. Translate the scientific proposition

For every sentence, preserve four layers:

1. **Entity** — basin, model, indicator, driver, process, period, scenario, or dataset.
2. **Relation** — increase, decrease, reproduce, correlate, contribute, propagate, respond, simulate, or compare.
3. **Evidence** — number, trend, spatial pattern, statistical result, figure/table, or cited source.
4. **Scope** — period, spatial domain, scenario, model framework, or uncertainty boundary.

Then rewrite the sentence into natural English syntax. Reorder clauses when this improves information flow, but do not alter the proposition.

### 4. Rebuild paragraph architecture

Use message-first paragraphs:

- open with the paragraph's scientific message;
- develop it with evidence, comparison, or mechanism;
- place the highest-value new information near sentence ends;
- connect adjacent sentences through an explicit logical relation: cause, contrast, detail, evidence, consequence, or qualification;
- remove repeated Chinese-style framing such as repeated equivalents of “研究表明”, “结果表明”, “由图可知”, or “可以看出” when the indicator itself can be the grammatical subject.

Keep one main scientific message per paragraph. Split overloaded paragraphs when necessary in Journal-ready mode.

### 5. Apply section-specific water-science style

Load `references/section-workflows.md`.

Mandatory boundary:

- **Results:** report indicator → value/change → spatial or temporal difference → pattern → limited interpretation tied directly to evidence.
- **Discussion:** explain process/mechanism → compare literature → interpret drivers → state implications and boundaries.

Do not move mechanism-heavy explanation into Results simply to make the prose sound sophisticated.

### 6. Calibrate evidence strength

Match verbs to evidence:

- direct measured or replicated evidence: `shows`, `demonstrates` when justified;
- model evaluation: `reproduced`, `captured`, `simulated`;
- association: `was associated with`, `was correlated with`;
- scenario decomposition: `accounted for the largest simulated contribution`, `within the scenario framework`;
- indirect mechanism: `suggests`, `is consistent with`, `may reflect`;
- projection: `is projected to`, `is expected under [scenario]` only when the source supports it.

Avoid causal verbs such as `drives`, `controls`, `determines`, `leads to`, or `proves` unless the study design supports causality.

### 7. Run final QA

Use `references/quality-gates.md` before delivering substantial text.

For long sections or full manuscripts, run:

```bash
python scripts/manuscript_guard.py --source source.txt --translation translation.txt
```

Treat a nonzero exit code as a fidelity warning that must be resolved or reported. This script checks deterministic tokens; it does not replace scientific review.

## Default output contract

For ordinary translation requests, return:

1. **Final English text** — directly usable in the manuscript.
2. **Material notes** — include only if there is a genuine ambiguity, terminology decision, source inconsistency, or evidence-strength issue.

Do not burden the user with a modification table unless requested.

For **Bilingual** mode, align source and translation by paragraph or sentence.

For **Audit** mode, use:

| Location | Issue type | Source meaning | Current English | Recommended correction | Severity |
|---|---|---|---|---|---|

Severity: `CRITICAL`, `MAJOR`, or `MINOR`.

For a full-manuscript translation, also maintain:

- terminology table;
- abbreviation table;
- ambiguity log;
- numerical/fidelity check summary;
- cross-section consistency notes.

## Hydrology-specific language policy

Use standard water-science terminology and process names. Prefer precise process terms such as `surface runoff`, `lateral flow`, `groundwater flow/baseflow`, `percolation`, `recharge`, `evapotranspiration`, `potential evapotranspiration`, `soil water`, `streamflow/discharge`, and `water yield` according to the actual model variable and context.

Do not collapse distinct concepts:

- `runoff` and `streamflow/discharge`;
- `groundwater storage` and `groundwater level`;
- `soil moisture` and `soil water storage`;
- `drought` and `water stress`;
- `calibration` and `validation`;
- `projection` and `prediction`;
- `attribution` and scenario-based contribution decomposition;
- `land use` and `land cover` when the distinction matters.

Use SI notation consistently. Preserve `m³ s⁻¹`, `mm d⁻¹`, `km²`, `°C`, `decade⁻¹`, and percentage-point language when the source metric requires them.

## Preferred manuscript stance

Use direct, evidence-led prose. State advantages when the evidence supports them. Keep uncertainty precise and bounded. Express future work as a route to extend the evidence rather than as a generic self-weakening paragraph.

Avoid empty claims such as `has important significance`, `provides a theoretical basis`, `is of great importance`, `obviously`, `remarkably`, or `better` without a named metric or comparison.

Do not add stock transitions merely to make the English appear academic. Use transitions only when they encode a real relation.

## Full-document continuity

When translating in chunks:

- establish glossary and abbreviation decisions before the first chunk;
- carry the previous paragraph and section objective as context into the next chunk;
- preserve heading hierarchy, citations, equations, and figure/table anchors;
- never translate the same technical term differently across chunks without recording the change;
- after stitching, review cross-section terminology and repeated numerical claims globally.

See `references/full-manuscript-protocol.md` for the complete procedure.

## Resource map

- `references/hydrology-style-guide.md` — section style, evidence language, and water-science conventions.
- `references/terminology-glossary.md` — preferred Chinese-English hydrology terminology.
- `references/section-workflows.md` — title through conclusions plus figures/tables.
- `references/quality-gates.md` — submission-oriented translation QA.
- `references/full-manuscript-protocol.md` — long-document chunking and continuity.
- `references/examples.md` — synthetic before/after patterns.
- `references/source-provenance.md` — design sources and licensing notes.
- `scripts/manuscript_guard.py` — deterministic token-fidelity checker.
