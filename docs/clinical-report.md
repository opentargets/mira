# Clinical Report

A Clinical Report is one traceable piece of evidence connecting one or more drugs with a disease or safety outcome. It gives records from clinical trials, regulatory agencies, drug labels, and curated resources a shared structure.

The model is deliberately small. It captures the information that every provider should supply, while allowing each source to add useful metadata of its own.

## What one report represents

One row represents one source record. Depending on the source, that record could be a clinical trial, a medicine label, a regulatory record, a curated indication, or a safety warning.

A report can contain more than one drug or disease. Its `id` and `url` provide traceability back to the underlying record.

For a broader explanation of the evidence and the sources used by Open Targets, see the [Open Targets Clinical Report documentation](https://platform-docs.opentargets.org/drug/clinical-report).

## Source and provider

`source` identifies where the evidence originated. `provider` identifies the resource from which Mira obtained it.

> [!IMPORTANT]
> These are sometimes the same organisation, but they do not have to be. For example, ChEMBL republishes references originating from sources such as EMA and FDA. A ClinicalTrials.gov record has `source: ClinicalTrials.gov` when Mira obtains it through the AACT database, so its provider is `AACT`.

The distinction makes it possible to inspect either the original evidence source or the route by which it entered Mira. To find all reports supplied by ChEMBL:

```python
import polars as pl


clinical_reports.filter(pl.col("provider") == "ChEMBL")
```

Mira currently integrates five providers:

| Provider | What it provides to Mira | Evidence sources represented | Implementation |
| --- | --- | --- | --- |
| AACT | Structured ClinicalTrials.gov study records | ClinicalTrials.gov | [AACT guide](providers/aact.md) and [implementation](../src/mira/provider/aact/) |
| ChEMBL | Curated drug indications and drug warnings | ChEMBL records and references from sources including FDA, EMA, ATC, DailyMed, INN, USAN, and ClinicalTrials.gov | [ChEMBL guide](providers/chembl.md) |
| EMA | Human medicine records published by the European Medicines Agency | EMA Human Drugs | [EMA guide](providers/ema.md) |
| PMDA | Public Japanese approval records | PMDA | [PMDA guide](providers/pmda.md) |
| TTD | Curated drug–disease records from the Therapeutic Target Database | TTD | [TTD guide](providers/ttd.md) |

The provider implementations live in the [`mira.provider` package](../src/mira/provider/). Each provider guide explains its contribution and selection rules; the [data-input inventory](data-inputs.md) documents acquisition and input formats.

## Drug and disease mapping

Names in source data are not always consistent. While preparing Clinical Reports, Mira maps disease labels to the Experimental Factor Ontology (EFO) and drug labels to the ChEMBL molecule dictionary. These are the controlled vocabularies used by Open Targets to identify diseases and drugs consistently across datasets.

The original labels remain available as `diseaseFromSource` and `drugFromSource`. When mapping succeeds, Mira adds the corresponding `diseaseId` or `drugId`. Keeping both makes the result traceable to the source while providing stable identifiers for integration and aggregation.

> [!NOTE]
> Mapping can be partial: a report may contain an identifier for only one of the two entities, or no mapped identifiers at all. The later [Clinical Indication](clinical-indication.md#mapping-status) records the mapping state of each aggregated drug–disease relationship.

Read [Entity mapping](entity-mapping.md) for the complete flow: existing identifiers, optional ChEMBL clinical-trial curation, OnToma label mapping, drug NER and provider-specific disease extraction.

## Origin and evidence type

The `origin` describes the kind of record behind the evidence:

- `CLINICAL_TRIAL`
- `DRUG_LABEL`
- `REGULATORY_AGENCY`
- `CURATED_RESOURCE`

The `type` describes the relationship captured by the report:

- `INDICATION` connects a drug with a disease in a clinical-development or approved-use context.
- `SAFETY` connects a drug with a safety outcome, warning, or withdrawal record.

An indication report normally uses `diseases`; a safety report can use `sideEffects` instead.

## Clinical stage

> [!NOTE]
> Every provider describes clinical development differently. Mira retains the original value in `phaseFromSource` and maps it to the shared `clinicalStage` categories used by Open Targets.

This makes clinical status comparable across different kinds of evidence and gives downstream datasets a consistent way to identify the most advanced stage reached by a drug–disease relationship.

| Category | Meaning |
| --- | --- |
| `WITHDRAWAL` | Evidence that a medicine was withdrawn, revoked, suspended, lapsed, or otherwise removed from use. |
| `APPROVAL` | Evidence of marketing authorisation or another recognised approved status. |
| `PHASE_4` | Post-marketing interventional evidence generated after approval. |
| `PREAPPROVAL` | A late regulatory stage before full authorisation, such as a submitted application or formal regulatory opinion. |
| `PHASE_3` | Late-stage clinical development, generally assessing efficacy and safety in larger patient populations. |
| `PHASE_2_3` | A study spanning or combining mid- and late-stage clinical development. |
| `PHASE_2` | Mid-stage clinical development, including subphases such as Phase IIa and IIb. |
| `PHASE_1_2` | A study spanning or combining early- and mid-stage clinical development. |
| `PHASE_1` | Early human clinical development, including subphases such as Phase Ib. |
| `EARLY_PHASE_1` | Exploratory human studies before standard Phase I, often focused on safety or pharmacokinetics. |
| `IND` | An Investigational New Drug application or equivalent filing before clinical trials begin. |
| `PRECLINICAL` | Evidence from preclinical development or an equivalent source-reported status. |
| `UNKNOWN` | The source value is missing, ambiguous, or cannot be mapped to another category. |

See the [Open Targets clinical-stage documentation](https://platform-docs.opentargets.org/drug/clinical-report#clinical-stage-categories) for the Platform-level interpretation. The mapping from source values to these categories is implemented in [`clinical_report.py`](../src/mira/dataset/clinical_report.py).

## Core fields

The core schema is defined in [`schemas.py`](../src/mira/schemas.py). Fields may be null where a source does not provide the information or where the field does not apply to that kind of report.

| Field | Meaning |
| --- | --- |
| `id` | Identifier of the underlying source record. Mira normalises report IDs to lowercase. |
| `clinicalStage` | Harmonised clinical-development or regulatory stage. |
| `phaseFromSource` | Development, regulatory, or safety status as represented by the source before harmonisation. |
| `origin` | Kind of source record, such as a clinical trial or drug label. |
| `type` | Whether the report captures indication or safety evidence. |
| `year` | Source-specific year associated with the report, when available. |
| `countries` | Countries or jurisdictions associated with the report, when available. |
| `url` | Link to the underlying evidence record. |
| `source` | Original source of the evidence. |
| `provider` | Resource from which Mira obtained the record. |
| `drugs` | Drugs associated with the report, with the source label and mapped ChEMBL identifier where available. |
| `diseases` | Diseases associated with an indication report, with the source label and mapped EFO identifier where available. |
| `sideEffects` | Safety outcomes associated with a safety report, with the source label and mapped EFO identifier where available. |

Each entry in `drugs` contains:

- `drugFromSource`: the label used by the source;
- `drugId`: the mapped ChEMBL identifier, when mapping succeeds.

Each entry in `diseases` or `sideEffects` contains:

- `diseaseFromSource`: the label used by the source;
- `diseaseId`: the mapped Experimental Factor Ontology (EFO) identifier, when mapping succeeds.

## Source-specific fields

> [!NOTE]
> Sources can add metadata beyond the core model. The schema accepts extra fields, and clinical-trial metadata uses the `trial` prefix. Examples include `trialOverallStatus`, `trialSponsor`, and `trialStartDate`.

This allows Mira to preserve useful source detail without requiring every provider to populate fields that only make sense for clinical trials. The available extended fields can evolve independently of the core model.

See the [complete Open Targets Clinical Report schema](https://platform.opentargets.org/downloads/clinical_report/schema) for the full downloadable dataset contract.

## Example

This report represents the ClinicalTrials.gov study `NCT05188521`, obtained through AACT:

```python
import datetime


{
    "id": "nct05188521",
    "clinicalStage": "PHASE_2",
    "origin": "CLINICAL_TRIAL",
    "type": "INDICATION",
    "source": "ClinicalTrials.gov",
    "provider": "AACT",
    "drugs": [
        {
            "drugFromSource": "baricitinib",
            "drugId": "CHEMBL2105759",
        }
    ],
    "trialDescription": (
        "This research study is evaluating the safety and efficacy of "
        "Baricitinib in treating Cutaneous Lichen Planus (LP)."
    ),
    "indicationText": None,
    "trialOverallStatus": "COMPLETED",
    "year": None,
    "trialPrimaryPurpose": "TREATMENT",
    "trialLiterature": [
        {"id": "39951132", "type": "DERIVED"},
        {"id": "38260663", "type": "DERIVED"},
    ],
    "trialSponsor": {
        "agencyClass": "OTHER",
        "name": "Aaron R. Mangold",
    },
    "trialPhase": "PHASE2",
    "countries": None,
    "trialWhyStopped": None,
    "phaseFromSource": "PHASE2",
    "trialNumberOfArms": 2,
    "diseases": [
        {
            "diseaseFromSource": "cutaneous lichen planus",
            "diseaseId": "EFO_1000726",
        }
    ],
    "url": "https://clinicaltrials.gov/study/NCT05188521",
    "sideEffects": None,
    "trialStudyType": "INTERVENTIONAL",
    "trialStartDate": datetime.date(2022, 1, 11),
    "trialDetailedDescription": None,
    "trialOfficialTitle": (
        "Baricitinib (LY3009104) in the Treatment of Cutaneous Lichen Planus"
    ),
}
```

Reading the record from the top:

- It is an indication report originating from a clinical trial.
- ClinicalTrials.gov is the evidence source; AACT is the provider used to retrieve it.
- The source phase `PHASE2` has been harmonised to `PHASE_2`.
- Baricitinib and cutaneous lichen planus have been mapped to ChEMBL and EFO identifiers.
- The `trial` fields preserve useful metadata specific to the clinical-trial record.

## From reports to indications

Clinical Reports preserve individual pieces of evidence and their provenance. Several reports can support the same drug–disease relationship: a trial, a regulatory record, and a curated reference may all describe the same association.

Mira brings those reports together in a Clinical Indication. Each Clinical Indication represents one drug–disease pair, records the maximum clinical stage reached, and retains `clinicalReportIds` so users can trace the association back to its supporting reports. It also records whether the drug and disease labels were successfully mapped to ChEMBL and EFO identifiers.

Read [Clinical Indication](clinical-indication.md) for the aggregation rules, mapping states, fields, and a worked example. The [Open Targets Indications documentation](https://platform-docs.opentargets.org/drug/indications) describes how these relationships appear in the Platform.
