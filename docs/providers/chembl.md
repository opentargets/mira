# ChEMBL provider

ChEMBL contributes two kinds of Clinical Reports to Mira: curated drug indications and drug safety warnings. Both are read from the ChEMBL PostgreSQL database and already contain ChEMBL drug identifiers. Many indication and warning records also contain EFO disease or safety-outcome identifiers.

See [ChEMBL 37 PostgreSQL database](../data-inputs.md#chembl-37-postgresql-database) for the release, tables, selected columns, connection settings, and local data preparation.

## What ChEMBL contributes

ChEMBL is the provider. The `source` of each report comes from the ChEMBL reference type, so reports supplied by ChEMBL can represent evidence originating from FDA, EMA, DailyMed, ATC, INN, USAN, ClinicalTrials.gov, or another curated reference.

| ChEMBL contribution | Clinical Report `type` | Typical `origin` | Main content |
| --- | --- | --- | --- |
| Drug indications | `INDICATION` | Clinical trial, drug label, regulatory agency, or curated resource | A drug, disease, development stage, and supporting reference. |
| Drug warnings | `SAFETY` | Drug label, regulatory agency, or curated resource | A drug, warning or withdrawal status, jurisdiction, and optional mapped safety outcome. |

> [!IMPORTANT]
> The provider/source distinction matters when filtering the output. To find every report obtained through ChEMBL, use `provider == "ChEMBL"`; to select an original evidence source, filter `source` instead.

## Drug indications

ChEMBL indications join the `drug_indication`, `molecule_dictionary`, and `indication_refs` tables. Each retained reference becomes a traceable indication report with:

- the preferred ChEMBL molecule name and identifier;
- the ChEMBL EFO term and identifier;
- the reference type, identifier, and URL;
- the maximum phase reported by ChEMBL where the reference is not itself evidence of approval.

The reference type determines the report origin. ClinicalTrials.gov references become `CLINICAL_TRIAL`, DailyMed references become `DRUG_LABEL`, and FDA or EMA references become `REGULATORY_AGENCY`. Other reference types are represented as `CURATED_RESOURCE`.

### Selection and stage rules

- Rows without an `efo_id` are excluded.
- Reference URLs beginning with `www` are excluded by the current adapter.
- ATC, EMA, FDA, DailyMed, and PMDA references are treated as approval evidence.
- INN and USAN references have an unknown clinical stage.
- Other references use ChEMBL's `max_phase_for_ind` value, which Mira then maps to its shared clinical-stage categories.

> [!NOTE]
> In the default Open Targets workflow, indication reports whose source is `ClinicalTrials` are removed before providers are combined. AACT is the selected provider for ClinicalTrials.gov study records in that workflow.

## Drug warnings

ChEMBL warnings join the `drug_warning`, `molecule_dictionary`, and `warning_refs` tables. They become safety reports containing:

- a mapped ChEMBL drug;
- the warning type as `phaseFromSource`;
- the warning year and countries, when supplied;
- the supporting reference and URL;
- an optional side effect or warning class represented with its EFO identifier when available.

DailyMed warnings have a `DRUG_LABEL` origin. FDA and EMA warnings have a `REGULATORY_AGENCY` origin. Other warning references use `CURATED_RESOURCE`.

> [!NOTE]
> Warnings do not require a mapped side effect. Mira keeps a warning report when its drug and reference are present even if `sideEffects` is null.

## Mapping behavior

ChEMBL supplies `drugId` directly from `molecule_dictionary`. Indication diseases also enter the pipeline with an EFO `diseaseId`. Warning side effects use the warning's EFO term and identifier where available, falling back to the warning class fields.

The shared [entity-mapping stage](../entity-mapping.md) preserves identifiers already supplied by the provider and attempts to fill remaining gaps across the combined report dataset.

## Implementation reference

- [Indication provider](../../src/mira/provider/chembl/indications.py)
- [Drug-warning provider](../../src/mira/provider/chembl/drug_warnings.py)
- [Default workflow](../../src/mira/recipe/clinical_report_generation.yaml)
