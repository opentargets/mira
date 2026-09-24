# TTD provider

The Therapeutic Target Database (TTD) contributes curated drug–disease indication records. Mira reads the public drug–disease text export and turns each retained drug and indication into a Clinical Report.

See [Therapeutic Target Database](../data-inputs.md#therapeutic-target-database) for the download location, expected record prefixes, and local file path.

## What TTD contributes

Every TTD report represents indication evidence from a curated resource:

| Clinical Report field | Value |
| --- | --- |
| `provider` | `TTD` |
| `source` | `TTD` |
| `origin` | `CURATED_RESOURCE` |
| `type` | `INDICATION` |
| `url` | TTD drug-detail page for the source drug identifier. |

The report identifier combines the TTD drug identifier with the disease label. The drug name and disease name from TTD are lowercased and retained as `drugFromSource` and `diseaseFromSource`.

## Selection and transformation

The parser reads three record types from each drug block:

- `TTDDRUID` identifies the current TTD drug;
- `DRUGNAME` supplies its label;
- `INDICATI` supplies a disease label, ICD-11 value, and clinical stage.

The file's first parsed indication row is treated as a header and removed. Duplicate report rows are removed. The adapter does not otherwise filter indications by stage or disease category.

TTD's clinical-stage value becomes `phaseFromSource` and is harmonised through Mira's shared [clinical-stage mapping](../clinical-report.md#clinical-stage).

## Mapping behavior

> [!NOTE]
> The TTD export includes an ICD-11 value, but the current Clinical Report adapter does not use it as `diseaseId`. Both drug and disease identifiers are initially null. The shared [entity-mapping stage](../entity-mapping.md) maps the TTD labels to ChEMBL and EFO identifiers later.

## Implementation reference

- [TTD provider](https://github.com/opentargets/mira/blob/main/src/mira/provider/ttd.py)
- [Default workflow](https://github.com/opentargets/mira/blob/main/src/mira/recipe/clinical_report_generation.yaml)
