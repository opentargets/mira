# PMDA provider

The Pharmaceuticals and Medical Devices Agency (PMDA) provider contributes Japanese new-drug approval indications. Mira extracts approval rows from PMDA's consolidated PDF and creates regulatory Clinical Reports from their active ingredients and notes.

See [PMDA approved products](../data-inputs.md#pmda-approved-products) for the source page, expected PDF structure, local path, and format-change checks.

## What PMDA contributes

Every PMDA report has these values:

| Clinical Report field | Value |
| --- | --- |
| `provider` | `PMDA` |
| `source` | `PMDA` |
| `origin` | `REGULATORY_AGENCY` |
| `type` | `INDICATION` |
| `clinicalStage` | `APPROVAL` |
| `year` | Year extracted from the approval date, when available. |

PMDA does not provide a stable report identifier for the extracted drug–disease pair in this file. Mira creates one by hashing the cleaned drug and extracted disease labels.

## Selection and label rules

The PDF parser searches for tables containing the expected approval, active-ingredient, and notes headings. It reuses the most recently recognised column layout when a continued table does not repeat its header.

The parser then:

- keeps rows whose approval field contains `Approval`;
- keeps all data rows when a recognised table has no approval-type column;
- removes rows that contain neither an active ingredient nor notes;
- cleans and separates multiple active ingredients;
- applies disease named-entity recognition (NER) to the notes;
- removes drug–disease rows where either extracted label is empty;
- removes duplicate rows.

> [!WARNING]
> The parser is sensitive to changes in the PDF layout. The checks described on the [data-input page](../data-inputs.md#pmda-approved-products) should be repeated whenever the source PDF changes.

## Mapping behavior

The active-ingredient and NER-derived disease labels initially have null identifiers. Disease NER extracts a mention from free text; it does not assign an EFO identifier. The shared [entity-mapping stage](../entity-mapping.md) maps the labels to ChEMBL and EFO after provider reports are combined.

## Implementation reference

- [PMDA provider](https://github.com/opentargets/mira/blob/main/src/mira/provider/pmda.py)
- [Default workflow](https://github.com/opentargets/mira/blob/main/src/mira/recipe/clinical_report_generation.yaml)
