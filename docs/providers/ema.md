# EMA provider

The European Medicines Agency (EMA) provider contributes human-medicine regulatory indications. Mira reads the EMA medicines report and creates regulatory Clinical Reports from its therapeutic areas and indication text.

See [EMA human medicines](../data-inputs.md#ema-human-medicines) for the workbook, worksheet, expected columns, and local file path.

## What EMA contributes

Every EMA report has these values:

| Clinical Report field | Value |
| --- | --- |
| `provider` | `EMA` |
| `source` | `EMA Human Drugs` |
| `origin` | `REGULATORY_AGENCY` |
| `type` | `INDICATION` |
| `id` | Lowercase EMA product number. |
| `url` | Medicine URL supplied in the workbook. |

The workbook's medicine status becomes `phaseFromSource` and is mapped to Mira's shared clinical-stage categories. For example, `authorised` becomes `APPROVAL`, while withdrawn, suspended, lapsed, or other statuses retain their corresponding meaning. The marketing-authorisation year is retained when its date can be parsed.

## Selection and label rules

Mira keeps workbook rows whose `Category` is `Human`. It chooses drug labels in this order:

1. international non-proprietary or common name;
2. active substance;
3. medicine name.

> [!NOTE]
> For diseases, Mira prefers the supplied `Therapeutic area (MeSH)`. When that field is missing, disease named-entity recognition (NER) extracts disease mentions from `Therapeutic indication`.

Semicolon-separated drug and disease values are split into separate labels. Rows are excluded when no drug label or no disease label remains after this processing. Duplicate report rows are removed.

## Mapping behavior

EMA supplies descriptive drug and disease labels rather than the ChEMBL and EFO identifiers required by the Open Targets output. Disease NER identifies mentions; it does not perform ontology mapping. The shared [entity-mapping stage](../entity-mapping.md) assigns identifiers after EMA reports have been combined with the other providers.

## Implementation reference

- [EMA provider](https://github.com/opentargets/mira/blob/main/src/mira/provider/ema.py)
- [Default workflow](https://github.com/opentargets/mira/blob/main/src/mira/recipe/clinical_report_generation.yaml)
