# Mira usability and documentation handover checklist

First-pass audit: 15 September 2026. Baseline: `9db40da`.

## Outcome and scope

The handover is successful when a new colleague can install Mira, run a small example, change a recipe, interpret the resulting records, and diagnose a failed run without asking the departing maintainer.

### Current focus

The active handover scope is deliberately narrower than the full audit:

1. Explain `ClinicalReport` and `ClinicalIndication` and the decisions behind them.
2. Document and verify their generation with the default Open Targets workflow.
3. Make the YAML configuration portable and teach users how to tailor it.
4. Document the sources required by that workflow.

Work specific to the `aact_llm_extractor` recipe is deferred. Previously generated LLM results remain in scope only where they are an input to the default generation workflow. See [decision 0001](decision-log.md#0001-documentation-handover-scope-and-authoring-approach).

“100% documented” should mean coverage of supported user journeys, data contracts, scientific decisions, and maintenance procedures. Documenting every private helper is a lower priority than making those journeys work.

> [!NOTE]
> This is a proposed backlog, not a statement that the improvements are implemented. The first pass covered the README, packaging, both recipes, CLI and execution helpers, schemas and datasets, provider code, mapping and LLM workflows, tests, and CI/release configuration. It did not run live databases, Spark mapping, paid extraction, an installed wheel in a clean environment, or a production workflow. No runtime code or recipes were changed during this audit.

### Evidence collected

- The existing local test suite passed: `.venv/bin/python -m pytest -q` → **93 passed**.
- `.venv/bin/python -m mira.cli --help` worked and listed both recipes.
- A synthetic offline execution of the extraction recipe's setup step produced `trialDescription` and `trialDescriptionRight`, but no `trialDetailedDescription`.
- An OmegaConf list passed to `normalise_steps` produced zero steps, despite the helper documenting legacy list support.
- The working tree was clean at the start. The initial audit deliverable was this checklist; subsequent documentation scaffolding is tracked separately.

The audit distinguishes observed behavior from proposed changes and decisions needing domain review. Passing unit tests does not establish that the shipped recipes work end to end.

## What to borrow from TARGENE

TARGENE makes the reader's journey explicit: purpose and assumptions, setup, worked examples, configuration reference, output interpretation, and developer guidance. Its navigation separates these concerns and offers version selection. [Documentation home](https://targene.github.io/targene-pipeline/stable/)

Its GWAS example connects a concrete configuration to a command and a sample result, explaining why the settings matter. Mira's tutorials should use the same progression. [Worked example](https://targene.github.io/targene-pipeline/stable/examples/gwas/)

Its output guide explains what a result represents, not just its file extension. For Mira, this means explaining a report, an aggregated drug–disease association, and their supporting evidence. [Output guide](https://targene.github.io/targene-pipeline/stable/targene/outputs/)

The home page identifies Documenter.jl as its documentation engine. Mira should adopt the reader journey; choosing a Python-appropriate documentation tool can follow the content plan. Some linked TARGENE setup/reference/developer pages could not be fetched during this review, so the comparison is based on the home page, worked GWAS example, and output guide.

## Priorities

- **P0 — handover blocker:** needed for a trustworthy supported workflow or to interpret its output correctly.
- **P1 — handover target:** needed for independent use and maintenance; complete within the two weeks where possible.
- **P2 — follow-up:** useful expansion after the essential journeys pass.

Assign a named owner and reviewer to each workstream. **Agreed audience:** an Open Targets colleague is the minimum handover target; external researchers are also an expected audience, and friendliness is an explicit requirement. Provide two entry points: a small offline example anyone can run, followed by the team workflow with its internal prerequisites. A public-data workflow should describe how to omit internal-only enrichment and what changes in the resulting coverage.

## First-pass findings

| Priority | Observed gap | Consequence and next action | Evidence |
| --- | --- | --- | --- |
| Resolved | The packaged defaults previously contained four paths tied to one maintainer's home-directory layout. | All default local inputs and outputs now derive from `MIRA_DATA_DIR`, with individual Hydra overrides available. | [Base config](../src/mira/config.yaml), [CLI guide](cli-and-configuration.md#base-configuration-reference) |
| P0 | The full recipe requires prepared Open Targets indices, ChEMBL curation, downloaded LLM batch results, two databases, and provider files. | A user cannot get from installation to execution using the README alone. Record how every artifact is acquired or built and provide a smaller supported route. | [Full recipe](../src/mira/recipe/clinical_report_generation.yaml), [curation exporter](../src/mira/provider/chembl/curation.py) |
| Deferred | Live LLM extraction returns a DataFrame persisted as Parquet, while report generation parses `*_output.jsonl` Batch API response envelopes. Batch-file preparation exists as a helper, with no bundled submission/download recipe. | Address when work resumes on the extraction recipe. For the default generation workflow, document only the result format it currently consumes. | [LLM engine](../src/mira/workflows/llm.py), [batch parser](../src/mira/provider/aact/llm_extractor.py) |
| Resolved | The full recipe previously attempted a generic NDJSON load of `datasets.llm_results` before its dedicated directory parser. | The unused eager input was removed. The setup step now reads the batch-result directory in its expected format. | [Full recipe](../src/mira/recipe/clinical_report_generation.yaml), [CLI guide](cli-and-configuration.md#run-the-complete-open-targets-workflow) |
| Deferred | The extraction recipe joins two `description` columns without renaming detailed descriptions. Its prompt requests `trialDetailedDescription`, which the offline check found missing. | Fix and test when work resumes on the extraction recipe. | [Extraction recipe](../src/mira/recipe/aact_llm_extractor.yaml), [AACT tests](../tests/test_aact.py) |
| P0 | Supplying LLM extractions replaces the original drug/disease labels. Uncovered trials receive null labels, and report generation subsequently filters out rows with null drugs. | A partial extraction set changes trial coverage; this is not a fallback enrichment. Decide and document the intended policy and report coverage counts. | [AACT transformation](../src/mira/provider/aact/clinical_report.py) |
| P0 | Clinical Indication aggregation converts withdrawal, phase 4, and approval reports to `APPROVAL` when deriving `maxClinicalStage`. Aggregation forms combinations by exploding both drug and disease lists. | Readers need the exact meaning and limitations of `maxClinicalStage` and associations. These are domain decisions requiring examples and maintainer review. | [Report model](../src/mira/dataset/clinical_report.py), [indication model](../src/mira/dataset/clinical_indication.py) |
| Resolved | Database inputs previously could not forward `limit` or `where_clause`. | Database inputs now support bounded reads, and the introductory AACT recipe filters all three tables at the database. | [AACT recipe](../src/mira/recipe/aact_clinical_report.yaml), [CLI guide](cli-and-configuration.md#run-one-aact-study) |
| Deferred | Recipe comments show an unsupported `inspect_mode` argument. The engine instead inspects whenever exactly one prompt remains, still calling the API and returning no extraction dataset. | Address when work resumes on the extraction recipe. | [Extraction recipe](../src/mira/recipe/aact_llm_extractor.yaml), [engine](../src/mira/workflows/llm.py) |
| Deferred | Publication enrichment is already enabled in the extraction recipe, despite the README presenting enabling it as an optional change. A helper says Europe PMC, but implementation uses PubMed Entrez with a placeholder email. | Address when work resumes on the extraction recipe. | [README](../README.md), [publication provider](../src/mira/provider/pubmed.py) |
| P1 | `validate_schema` checks required column presence and reorders columns; it does not validate every DataFrame value against Pydantic types, enums, or nested fields. | Reference pages must distinguish declared models from enforced guarantees. Add validation at important input/output boundaries as appropriate. | [Schemas](../src/mira/schemas.py) |
| P1 | Spark selection depends on the input name containing `spark`. `$step` resolution handles direct values and list elements, but not nested dictionaries. Legacy YAML list steps are silently skipped. | Recipe behavior is difficult to infer and failures can be subtle. Document supported syntax and reject unsupported forms or implement them. | [CLI](../src/mira/cli.py), [execution helpers](../src/mira/utils/pipeline.py) |
| P1 | Outputs use a date directory and fixed filenames, allowing same-day replacement. The runner saves outputs after all transform sections complete. | Explain reruns and partial failures; provide a run identity, manifest, and deliberate overwrite policy. | [CLI](../src/mira/cli.py) |
| P1 | Spark settings include a hard-coded 10 GB driver allocation; mapping uses external models and indices. The README omits the full runtime setup. | Installation success alone does not establish runtime readiness. Verify and document Java/Spark/model/resource requirements by workflow. | [Spark setup](../src/mira/utils/spark_helpers.py), [mapping](../src/mira/utils/mapping.py), [packaging](../pyproject.toml) |
| P1 | There is no user documentation site or tracked tutorial fixture set. CI runs lint/format/tests, but has no documentation or complete-recipe check. | Examples can drift independently of implementation. Make documentation and recipe examples part of CI. | [CI](../.github/workflows/ci.yaml), [tests](../tests) |

## A. Supported use cases and project identity

**Done when:** a reader can identify the right workflow, prerequisites, and support contact before installing.

- [ ] **P0 A1** Define the minimum supported end-to-end journey for the agreed primary audience, an Open Targets colleague. Record which steps require internal resources and the corresponding external-researcher route.
- [ ] **P0 A2** State Mira's scope: source harmonisation, entity grounding, evidence records, and association aggregation. Explain that an extracted or co-occurring association is not evidence of treatment success by itself.
- [ ] **P1 A3** Add a workflow matrix focused on reports, mapped reports/indications, and existing extraction-result ingestion. Label shipped, planned, deferred, and helper-only capabilities accurately.
- [ ] **P1 A4** Explain naming once: Mira/MIRA, distribution `opentargets-mira`, Python import and CLI `mira`, formerly `clinical_mining`. Check release metadata, repository links, examples, and external integration references for the rename.
- [ ] **P1 A5** Replace the README's broad feature tour with a short entry point: who it serves, prerequisites, one verified command sequence, sample output, and links to detailed docs. Separate installed-package commands (`mira`) from checkout development (`uv run mira`).
- [ ] **P1 A6** Record known limitations and supported environments, with a named maintenance contact and issue-report template.
- [ ] **P1 A7** Review the docs for friendliness: define acronyms at first use, explain why each step matters, show success after each major step, use actionable error messages, and state which settings beginners can leave alone. External readers must not need Open Targets institutional knowledge to follow the introductory journey.

## B. Portable configuration and recipe authoring

**Done when:** a colleague can run from another directory and author a small recipe without editing installed package files or reading the runner source.

- [x] **P0 B1** Remove all personal layout assumptions in the base config and recipes. Use a documented data-root layout for supplied files and explicit required values for resources that cannot sensibly default. Cover the curation file as well as the three base-config paths. See [CLI and YAML configuration](cli-and-configuration.md#base-configuration-reference).
- [x] **P0 B2** Define and verify configuration layering: packaged defaults, named recipe, user/environment configuration, and CLI overrides. Supply a tested way to load user-owned YAML after `pip install`; do not assume users can edit `site-packages`. See [How configuration is composed](cli-and-configuration.md#how-configuration-is-composed) and [Use your own recipe](cli-and-configuration.md#use-your-own-recipe).
- [x] **P0 B3** Publish a config reference with each key's meaning, type, default, requiredness, consuming recipe, path/URI semantics, example, and environment override. Explain whether `.env` loading is supported; `python-dotenv` is a dependency, but no loader was found in the reviewed runtime code. See [Base configuration reference](cli-and-configuration.md#base-configuration-reference).
- [ ] **P0 B4** Add preflight validation before expensive work: input existence/format, required columns, callable and argument names, missing/forward references, output destination, and required credentials. Errors should name the YAML location and remedy. Do not include secrets in diagnostics or saved config examples.
- [ ] **P0 B5** Establish and document the LLM-result input format consumed by the default generation recipe. Defer fixes specific to producing those results with the extraction recipe.
- [x] **P1 B6** Write an annotated recipe explaining `# @package _global_`, `inputs`, `setup → generate → post_process`, insertion-order execution, step names, function paths, dataset `.df` unwrapping, and `output_` persistence. See [Anatomy of a recipe](cli-and-configuration.md#anatomy-of-a-recipe).
- [x] **P1 B7** Explain the three distinct expressions with examples: `${datasets.ttd_path}` for configuration interpolation, `${oc.env:MIRA_DATA_DIR,data}` for environment lookup, and `$aact_report` for an already-produced runtime object. Explain the current non-recursive reference limitation. See [Three kinds of references](cli-and-configuration.md#three-kinds-of-references).
- [ ] **P1 B8** Add task-based edits: change paths/output location; select one trial; sample reproducibly; switch off publications; change a prompt/model; add metadata with a rename/aggregation; save an intermediate result; remove a provider and all dependent references.
- [x] **P1 B9** Define recipe input formats precisely. Current `json` means newline-delimited JSON; database input keys are also table names; a name containing `spark` selects Spark. Replace name-based engine selection with an explicit setting if feasible, otherwise document it prominently. Recipes now use `engine: spark`; the name-based behavior remains as backwards compatibility. See [Inputs](cli-and-configuration.md#inputs).
- [ ] **P1 B10** Resolve legacy list handling and reject unknown workflows/unsupported output types clearly. Describe configuration mistakes as failures rather than successful no-ops.
- [ ] **P1 B11** Provide a configuration/plan inspection route and a separate prompt-preview route with no extraction calls. Mark any new commands as proposed until implemented and tested.

## C. Installation and input data contracts

**Done when:** each required input has a source, a preparation procedure, a compatible example, and a verification step.

- [ ] **P0 C1** Build an input inventory for the default generation recipe: provider, version/date, location, access requirements, format, required columns and nested types, join keys, null rules, expected scale, and obtaining/updating instructions.
- [ ] **P0 C2** Document AACT and ChEMBL PostgreSQL setup separately: hosted/local assumptions, schema, credentials, selected tables, tested snapshot/version, and connectivity checks. Check the fixed `chembl_36`/`CHEMBL_36` assumptions when describing version changes.
- [x] **P0 C3** Document production of the Open Targets disease and molecule indices: upstream owner/job, compatible schema, release alignment, storage layout, and minimal examples. Check external library contracts rather than inventing index columns. See [Open Targets entity indices](data-inputs.md#open-targets-entity-indices).
- [ ] **P0 C4** Before the final handover, create an issue to deprecate and remove the private Oracle clinical-trial curation process. The public documentation should only identify it as a legacy internal input and explain how to run without it.
- [ ] **P0 C5** Document the Batch response-envelope JSONL contract consumed by the default generation workflow, including its `*_output.jsonl` naming convention. Defer the live-extraction Parquet contract and adapter decision.
- [ ] **P1 C6** Add provider preparation pages for TTD text, EMA Excel, and PMDA PDF, including download/version identification, expected sheet/header/table layout, format-change diagnostics, and a small approved example or synthetic substitute.
- [ ] **P1 C7** Verify a fresh installation for Python 3.11/3.12 and each supported platform. Document Java, Spark/Spark NLP, NER model downloads/cache, network needs, memory/disk, and Oracle client requirements where relevant. Measure runtime rather than copying estimates.
- [ ] **P1 C8** Audit direct versus transitive dependencies and verify that wheel/sdist contain YAML recipes and prompt assets. Run help and the offline tutorial outside the repository from an installed wheel.
- [ ] **P1 C9** Specify relative path resolution, local file versus directory/glob support, and any remote storage support separately by loader. Do not infer universal remote support from the batch parser's use of `fsspec`.
- [x] **P1 C10** Add bounded data loading for small runs, or provide pre-exported fixtures. The CLI now forwards database `where_clause` and `limit`, and the introductory AACT recipe performs bounded reads.

## D. Principles and data models

**Done when:** a scientist can trace a result back to evidence and explain why Mira chose its labels, IDs, and stage.

- [x] **P0 D1** Write an architecture overview: providers → harmonised reports → entity mapping → aggregated indications; show the optional LLM replacement path and all external prerequisites. Distinguish raw inputs, intermediate objects, and persisted outputs. See [How Mira works](concepts.md).
- [ ] **P0 D2** Give `ClinicalReportSchema` and `ClinicalIndicationSchema` their own pages, including their nested drug and disease models. Include field dictionary, types, required versus nullable, enums, extra-field policy, and a fully explained representative record. Defer the extraction schema page.
- [ ] **P0 D3** Define provider versus source, origin versus evidence type, report versus indication, raw labels versus identifiers, and indication disease versus side effect. Explain only the LLM-derived fields needed to understand default report generation.
- [ ] **P0 D4** Document row granularity, lowercased report IDs, aggregation hash inputs, ID-versus-label fallback, mapping statuses, report-to-indication cardinality, and traceability through `clinicalReportIds`. Explain that `drugName`/`diseaseName` can contain IDs.
- [ ] **P0 D5** Review and explain stage harmonisation and ranking with examples: source-based approval overrides, unknown values, withdrawals, terminated trials, and the indication-level collapse to `APPROVAL`. Make clear whether `maxClinicalStage` describes development history rather than current authorization. Confirm the intended interpretation with the maintainer.
- [ ] **P2 D6** Keep the narrow EMA/ChEMBL report deduplication rule in code-level documentation and regression tests. Leave it out of the user guide unless its user impact grows.
- [x] **P0 D7** Explain entity mapping order: preserve existing IDs; curated study/label matches; dictionary mapping; optional drug NER fallback. Document one-to-many matches, ambiguity, label normalization, unmapped values, and cache invalidation. See [Entity mapping](entity-mapping.md).
- [x] **P0 D8** Review the consequences of exploding both drugs and diseases: all combinations within a report can become associations. Explain the evidence needed to interpret combinations and the handling of reports with no disease. See [AACT: Drug and disease cardinality](providers/aact.md#drug-and-disease-cardinality).
- [ ] **P0 D9** Confirm the policy for safety records in indication aggregation. The current aggregator has no explicit `type == INDICATION` filter. Demonstrate how safety evidence, side effects, and withdrawals should affect downstream outputs before presenting this as a stable contract.
- [x] **P0 D10** Explain AACT selection rules, exclusions for placebo/healthy terms, supported study types, and the coverage effect of LLM replacement. Show input/retained/dropped counts and reasons. See the [AACT provider guide](providers/aact.md).
- [ ] **P1 D11** Separate model declarations from runtime validation guarantees. Review null versus empty lists, malformed nested entities, invalid enums, and all-failed/empty extraction outputs; preserve typed empty schemas where required.
- [ ] **P1 D12** Preserve domain decisions in short decision records: problem, chosen rule, rationale, alternatives, owner, and a regression example. Prioritize rules whose rationale cannot be recovered from code.

## E. LLM extraction and evidence quality — deferred

This work is retained for later planning and does not block the current handover scope. Existing extraction results are documented only as an input to default report generation.

- [ ] **Deferred E1** Document the actual prompt inputs and exclusions. Verify configured trial fields against generated report columns; show exact synthetic before/after examples.
- [ ] **Deferred E2** Distinguish live concurrent requests, automatic single-prompt inspect behavior, offline prompt preview, Batch request-file creation, Batch submission/download, and Batch result ingestion. State which parts Mira currently implements.
- [ ] **Deferred E3** Decide the behavior for missing extractions, empty drug/indication lists, and partial failures. Show how these affect report coverage and avoid silently treating a reduced output as a complete run.
- [ ] **Deferred E4** Explain adjustable model, prompt resource, response schema, concurrency, retries, service tier, sampling, and seed. Align inconsistent comments/defaults and correct the unsupported inspect argument example.
- [ ] **Deferred E5** Explain publications configuration and actual PubMed source; configure the Entrez contact instead of a placeholder. Document when external requests occur and how to disable them for offline examples.
- [ ] **Deferred E6** Record model identifier, prompt version/hash, input snapshot, extraction schema version, sample IDs, and settings with each run. A sampling seed does not guarantee identical LLM output or identical samples from reordered data.
- [ ] **Deferred E7** Create a small maintainer-reviewed evaluation set covering therapeutic, diagnostic, preventive, supportive, ambiguous, and healthy-volunteer cases. Check drug roles, disease modifiers, evidence quotes, and omitted/unsupported claims. Treat model-reported confidence as uncalibrated unless validated.
- [ ] **Deferred E8** Explain errors/failed IDs, retry behavior, partial success, rerunning failed records, and duplicate prevention. State current limitations where resume/recovery is not implemented. Estimate cost from measured usage and verify current provider pricing when writing that guide.

## F. Outputs, operations, and troubleshooting

**Done when:** successful, partial, empty, and failed runs are distinguishable, and a maintainer can reproduce or investigate a result.

- [ ] **P0 F1** Publish the default generation output inventory: exact filename, format, schema, row meaning, example, and producer/consumer for `clinical_report.parquet` and `clinical_indication.parquet` under the date directory. Defer extraction-recipe outputs.
- [ ] **P0 F2** Provide a short output walkthrough: load Parquet, inspect nested entities, filter mapping status, look up an indication, and follow its supporting report IDs. Include partially/unmapped and conflicting-evidence cases.
- [ ] **P1 F3** Add a run manifest with package/code version, redacted config, input versions/checksums, timestamps, model/prompt versions where relevant, and output inventory. Account for already-existing Hydra artifacts rather than assuming a complete provenance record exists.
- [ ] **P1 F4** Define unique run directories and overwrite behavior. Explain current end-of-run persistence and what survives a failure; add intermediate checkpoints only where they support a real recovery need.
- [ ] **P1 F5** Add a concise run summary: input/output counts, provider counts, mapping coverage, dropped records, extraction failures, and output paths. Validate useful failure exit status and logging, including the mixed logger formatting in the LLM workflow.
- [ ] **P1 F6** Write symptom-based troubleshooting: missing file/table/column, database authentication, YAML interpolation/reference, import or bad parameter, Java/Spark startup, model download, memory, missing batch files, empty results, and malformed extraction records.
- [ ] **P1 F7** Create a maintainer runbook: refresh data, verify compatibility, run on the intended host, inspect completion, rerun/recover, compare releases, clean caches, and locate artifacts. Record operational owners and access procedures rather than credentials.

## G. Tutorials and documentation site

**Done when:** every published tutorial has runnable inputs, a tested command sequence, observable success criteria, and an explanation of the output.

- [ ] **P0 G1** Create a tiny, tracked, synthetic fixture set for the primary journey. It must avoid live databases, paid APIs, internal paths, and runtime model downloads. State explicitly which production stages this example bypasses.
- [ ] **P0 G2** Implement and verify Tutorials 1 and 2 below and the minimum internal workflow in Tutorial 5. The first two teach the shared foundations; the internal workflow is the handover acceptance target. Do not publish proposed commands as existing features.
- [ ] **P1 G3** Add the workflow-specific and maintainer tutorials in the agreed audience order. Include a real public-data route that can omit private curation, explain the resulting differences, and keep optional internal/online prerequisites visible at the start.
- [ ] **P1 G4** Create a version-controlled documentation site with the proposed navigation below, search, source links, local preview instructions, and a reproducible build. Choose the tool based on the team's ability to maintain it.
- [ ] **P1 G5** Build docs and check links/examples in CI. Prefer referencing tested YAML/snippets directly to copying them into multiple pages. Add a small complete-recipe smoke test; existing helper tests did not catch the description mismatch.
- [ ] **P1 G6** Run a colleague-led rehearsal on a clean environment. Record every undocumented step and fix the tutorial or software until the colleague can finish without verbal guidance.
- [ ] **P1 G7** Publish the reviewed docs at an agreed team-owned location, link from README/package metadata, and document how releases update the docs. Use a stable version label only for a matching reviewed release.
- [ ] **P2 G8** Add recorded walkthroughs and advanced examples after text tutorials are reproducible. Recordings should supplement maintainable written steps.

### Proposed navigation

```text
Home: what Mira does, supported uses, limitations
Getting started
  Installation and runtime requirements
  First offline run
  Choosing a workflow
Concepts
  Evidence, sources, and providers
  Reports, extractions, and indications
  Stage harmonisation
  Entity mapping and ambiguity
  LLM evidence and coverage
Tutorials
  First reports and indications
  Tailor a recipe
  Prepare and map a source
  Extract and inspect trial evidence
  Run the production workflow
How-to guides
  Obtain inputs; configure environments; customize; recover failures
Reference
  Configuration keys; recipe syntax; input contracts; output schemas
  Provider-specific behavior; supported Python API
Maintainer guide
  Architecture; tests; new providers; releases; operations; decisions
Troubleshooting and known limitations
```

### Tutorial sequence to design together

| Tutorial | Reader outcome | Inputs and observable success | Dependency |
| --- | --- | --- | --- |
| 1. Your first Mira dataset | Understand reports and derive indications from a few records. | Proposed synthetic local fixtures; inspect known report/association counts and trace one relationship. Include mapped and unmapped examples. | Portable config and an offline recipe; no live services. |
| 2. Make the pipeline yours | Copy a recipe, change selection, add metadata, and persist an intermediate dataset. | Reuse Tutorial 1; a deliberate change produces an explained difference in output. | Documented external YAML loading and recipe syntax. |
| 3. Prepare and map a source | Obtain/validate a real provider input and understand mapping outcomes. | One agreed provider plus compatible indices; verify input schema and explain mapped/unmapped labels. | Input contract and verified Spark/NER setup if used. |
| 4. Extract trial evidence — deferred | Preview text, run a small extraction, review roles/quotes, and consume results. | Synthetic/frozen preview first; optional live trial run with explicit external prerequisites. Separate one-prompt inspect from persisted multi-record results. | Resume work on the extraction recipe. |
| 5. Reproduce the team workflow | Run production-like integration with versioned inputs and check completion. | Recorded data versions, output manifest, stage/count/coverage checks. | Internal access where applicable; complete operational runbook. |
| 6. Add a provider | Implement an adapter returning the agreed report contract and wire it into a recipe. | Tiny new-provider fixture, schema/behavior checks, documented expected output. | Stable provider contract and maintainer guide. |

For every tutorial, specify audience, learning goal, prerequisites, estimated time measured on a named environment, input files, exact commands, expected outputs/counts, interpretation, a customization exercise, common failures, and verification against a package version. Use deterministic checks for fixtures and schema/quality checks for variable live outputs.

### How to use AI productively

AI can draft field references from schemas, inventory recipe parameters, create synthetic fixtures, explain a tested example, and generate troubleshooting cases from observed errors. The maintainer should review the scientific rationale, source limitations, intended coverage, and evidence interpretation. A colleague should execute the final steps. Keep a link from each generated reference to its source; require executable verification for commands and explicit review for claims the code cannot establish.

## H. Maintainer and release continuity

**Done when:** someone else can change, test, release, and operate Mira with team-owned access.

- [ ] **P0 H1** Assign the next code/domain/operations owners and capture the remaining implicit decisions before departure. Identify the data owners for every upstream artifact.
- [ ] **P1 H2** Write development setup, repository map, contribution procedure, appropriate tests, lint/format commands, and supported extension points. Identify public APIs versus internal helpers.
- [ ] **P1 H3** Add focused regression checks for default recipe composition, result ingestion, stage aggregation, LLM coverage loss in default report generation, and packaged resources. Defer extraction-recipe prompt checks. Validate important domain rules rather than only implementation details.
- [ ] **P1 H4** Document the existing tag-driven build → PyPI publication → GitHub release workflow, version updates, release checks, trusted-publisher/environment ownership, and correction procedure. Verify continuity of permissions with the receiving maintainer.
- [ ] **P1 H5** Record a tested dependency baseline, Python compatibility, input/schema compatibility policy, release notes, and how downstream pipeline consumers adopt a new version.
- [ ] **P1 H6** Create a final handover index linking the docs, last successful run and versions, unresolved issues, owners, and next priorities. Move essential knowledge out of untracked notebooks or personal directories.
- [ ] **P2 H7** Expand API reference coverage, integration matrices, performance benchmarks, and automated source-format monitoring after the essential journeys are reliable.

## Proposed two-week delivery sequence

This is a scope proposal for roughly ten working days, not a commitment to completing every P1 item. Reserve time for rehearsal and fixes; do not leave validation until departure day.

| Window | Focus | Exit criterion |
| --- | --- | --- |
| Days 1–2 | Agree audience, inventory data, capture domain decisions, fix portability and the recipe/format blockers. | One supported input-to-output route and its prerequisites are explicit; P0 implementation issues have owners. |
| Days 3–4 | Build the offline fixture/recipe; write installation, config reference, and annotated recipe. | A clean installed-package run succeeds outside the repository; Tutorial 1 is executable. |
| Day 5 | Models, stage/mapping/coverage principles, and output walkthrough; domain review. | Maintainer approves representative records and the interpretation of difficult cases. |
| Days 6–7 | Tutorial 2 and the minimum Open Targets workflow in Tutorial 5; input guides and recovery instructions. | A colleague can change a recipe, run the agreed team workflow, and explain the resulting output differences. |
| Day 8 | Docs build/CI, release guide, ownership/access continuity. | Docs build from a checkout and maintainers know how to release/update them. |
| Day 9 | Independent onboarding rehearsal and production-path validation where access permits. | Failures and undocumented assumptions are captured as concrete fixes. |
| Day 10 | Fix rehearsal blockers, publish reviewed docs, finalize handover index and deferred backlog. | Receiving maintainer accepts the supported journeys and owns remaining work. |

If capacity is tight, reduce the number of provider tutorials. Preserve the portable run, recipe guide, data contracts, domain explanations, independent rehearsal, and named ownership.

## Decisions to make together

1. With an Open Targets colleague confirmed as the first reader, which exact team workflow must they complete before departure, and which real public-data route should external researchers start with?
2. Which resources are essential to the supported production workflow, and which should be optional? In particular: curation, LLM results, and mapping indices.
3. **Deferred:** Should live extraction Parquet become the standard interchange format, with Batch JSONL imported into it, or should the documented production route remain Batch-first?
4. What is the intended policy for uncovered trials, safety evidence, ambiguous mappings, and withdrawal/approval aggregation? Which current behaviors need changing before documenting them as stable?
5. Who will own code, domain decisions, input refreshes, releases, and the documentation location?

## Final acceptance checklist

- [ ] A new colleague installs the released/built package in a clean environment and runs the offline example from outside the repository.
- [ ] They change a user-owned YAML recipe and get the expected output change.
- [ ] They can explain one report, one extracted record, one aggregated association, and the important limitations of each.
- [ ] The supported real-data workflow has complete acquisition/preparation instructions and a recorded successful run, or an explicitly documented external blocker with an owner.
- [ ] The default generation guide accurately documents the configured LLM-results input and its effect on report coverage.
- [ ] No supported example relies on personal paths or undisclosed input files.
- [ ] Documentation and recipe checks run in CI; published pages match the supported version.
- [ ] The receiving maintainer can run checks, investigate a failed run, and explain the release/update procedure.
- [ ] Remaining issues have priorities and owners, and the handover index identifies the final tested state.
