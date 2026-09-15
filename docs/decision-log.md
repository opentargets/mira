# Mira decision log

> [!IMPORTANT]
> This log preserves decisions whose rationale would otherwise live only in code or conversations. Add an entry only when the project takes a meaningful stance between alternatives, such as defining data-model semantics, choosing workflow behavior, or establishing a configuration contract. Routine edits, documentation progress, and implementation notes do not belong here.

For each new decision, add a dated section containing its status, context, decision, and consequences. When a decision changes, add a new section that supersedes the earlier one rather than rewriting history.

## 0001: Documentation handover scope and authoring approach

- **Status:** Accepted
- **Date:** 2026-09-15

### Context

Mira needs to be handed over to a new maintainer. An Open Targets colleague is the minimum audience, while external researchers are also expected users and should have a friendly route into the project.

The initial audit identified many possible improvements. Treating them all as immediate blockers would dilute the work needed to explain and operate Mira's main outputs. The LLM extraction recipe is useful but less important to this handover phase.

Documentation also needs a publishable home. Choosing hosting before the content and ownership are clear could tie the project to an unsuitable tool or account.

### Decision

Develop and review the documentation one feature at a time, in this order:

1. Define and explain `ClinicalReport` and `ClinicalIndication`.
2. Document and verify how the default Open Targets workflow generates them.
3. Make the configuration portable and explain how to tailor its YAML files.
4. Document the data sources and add task-based tutorials.

Defer documentation and usability work specific to the `aact_llm_extractor` recipe. The default generation workflow may consume previously generated LLM results; that input remains in scope only as part of explaining and operating the default workflow.

Author the source documentation as Markdown under `docs/`. Prefer MkDocs with the Material theme for navigation, search, and a maintainable Python-oriented build. Prefer GitHub Pages for publication if Open Targets repository policy and permissions allow it. Confirm ownership and publication permissions before making the deployment decision final.

### Consequences

- The core data models and the workflow used by Open Targets receive attention first.
- External readers get shared conceptual documentation and, later, a public or offline path that labels internal dependencies clearly.
- LLM extraction findings remain in the backlog without blocking the core documentation.
- Markdown remains useful directly in GitHub even before a documentation site exists.
- A documentation build and deployment configuration still need to be selected, implemented, and checked in CI.

## 0002: Portable configuration and user-owned recipes

- **Status:** Accepted
- **Date:** 2026-09-15

### Context

The packaged configuration contained paths tied to one maintainer's home-directory layout. Editing those packaged files would also be unsuitable after installation. Small CLI examples could not restrict database reads at the input boundary.

### Decision

Use `datasets.data_root`, set by `MIRA_DATA_DIR` or defaulting to `data`, as the root for every default local input and output. Allow database connection details through environment variables and recipe inputs to specify `table_name`, `schema`, `where_clause`, and `limit`. Select Spark loading with `engine: spark`.

Keep reusable recipes in the package. Load deployment-specific recipes from a user-owned Hydra configuration directory with `--config-dir`, so users do not edit installed package files.

### Consequences

- Moving a run requires changing one data-root value or individual Hydra overrides.
- Credentials remain outside committed YAML.
- Tutorial recipes can query a bounded database subset.
- User recipes inherit the packaged defaults while remaining independently editable.
