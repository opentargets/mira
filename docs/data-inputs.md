# Data inputs

Mira combines public clinical and biomedical datasets with Open Targets entity indices. This page records where each source comes from, the format Mira expects, and where it fits in the default local layout.

Input acquisition will be automated separately. A future Make target or equivalent command should implement this contract without moving source-specific assumptions into the provider code.

> [!NOTE]
> Previously generated LLM results are deliberately outside the scope of this page.

## Input inventory

| Input | Source | Version policy | Format used by Mira | Default destination |
| --- | --- | --- | --- | --- |
| Disease index | [Open Targets downloads](https://platform.opentargets.org/downloads/disease/access) | Latest Open Targets release; use the same release as the drug-molecule index. | Partitioned Parquet read by Spark. | `<data_root>/inputs/disease/` |
| Drug-molecule index | [Open Targets downloads](https://platform.opentargets.org/downloads/drug_molecule/access) | Same Open Targets release as the disease index. | Partitioned Parquet read by Spark. | `<data_root>/inputs/drug_molecule/` |
| ChEMBL database | [ChEMBL 37 PostgreSQL archive](https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_37/chembl_37_postgresql.tar.gz) | ChEMBL 37. | PostgreSQL database. | Database configured by `CHEMBL_DB_URI`; default `localhost:5432/chembl_37`. |
| ChEMBL clinical-trial mapping | Legacy private Oracle curation | Existing internal runs only; the process is intended for deprecation. | One Parquet file. | `<data_root>/inputs/chembl_mapping.parquet` |
| AACT | [AACT downloads](https://aact.ctti-clinicaltrials.org/downloads) | Latest database snapshot selected for the run. | PostgreSQL database using the `ctgov` schema. | Database configured by `AACT_DB_URI`; default `localhost:5432/aact`. |
| TTD drug–disease data | [Therapeutic Target Database file](https://ttd.idrblab.cn/files/download/P1-05-Drug_disease.txt) | Latest available file; record the download date. | Structured text file. | `<data_root>/inputs/P1-05-Drug_disease.txt` |
| EMA human medicines | [EMA medicines report](https://www.ema.europa.eu/en/documents/report/medicines-output-medicines-report_en.xlsx) | Latest report; record the download date. | Excel workbook. | `<data_root>/inputs/medicines-output-medicines-report_en.xlsx` |
| PMDA approvals | [PMDA list of approved products](https://www.pmda.go.jp/english/review-services/reviews/approved-information/drugs/0002.html) | Latest consolidated New Drugs PDF linked from the page; record its covered date range. | PDF. | `<data_root>/inputs/pmda_approvals.pdf` |

`data_root` is set by `MIRA_DATA_DIR` and defaults to `data`. Database inputs are configured separately because Mira queries them rather than reading their dump archives directly.

## Recommended local layout

```text
<MIRA_DATA_DIR>/
├── inputs/
│   ├── disease/
│   │   └── *.parquet
│   ├── drug_molecule/
│   │   └── *.parquet
│   ├── chembl_mapping.parquet
│   ├── P1-05-Drug_disease.txt
│   ├── medicines-output-medicines-report_en.xlsx
│   └── pmda_approvals.pdf
└── outputs/
```

The Open Targets indices are distributed datasets: keep their Parquet parts together in their respective directories. Spark reads the directory, so the files do not need to be concatenated.

## Keep a release manifest

> [!IMPORTANT]
> “Latest” changes over time. Every prepared input bundle should record the versions actually used, even when the acquisition command normally selects the newest release.

A future acquisition rule should write a small manifest containing at least:

- acquisition timestamp;
- source URL;
- Open Targets release identifier for both indices;
- ChEMBL release number;
- AACT snapshot date;
- download date for TTD and EMA;
- PMDA PDF title and covered date range;
- local destination;
- checksum when the publisher provides one, or a locally computed checksum otherwise.

> [!IMPORTANT]
> The disease and drug-molecule indices must come from the same Open Targets release. The ChEMBL database and any derived ChEMBL export should also record a common ChEMBL release.

## Open Targets entity indices

Mira uses the Open Targets disease and drug-molecule datasets to build OnToma lookup tables. Download both from the [Open Targets data downloads](https://platform.opentargets.org/downloads) page and select the same release.

Open Targets distributes each dataset as a directory of Parquet parts. Place the complete directories at:

```text
<data_root>/inputs/disease/
<data_root>/inputs/drug_molecule/
```

### Disease fields used by OnToma

The current OnToma integration reads:

- `id`
- `name`
- `exactSynonyms`
- `narrowSynonyms`
- `broadSynonyms`
- `relatedSynonyms`

The disease identifier becomes the mapped `diseaseId`. Names and synonyms become candidate labels.

### Drug-molecule fields used by OnToma

The current integration reads:

- `id`
- `name`
- `tradeNames`
- `synonyms`
- `crossReferences`

The current OnToma version expects `tradeNames` and `synonyms` to contain structured labels with their source, and `crossReferences` to contain a source and list of identifiers. This is why Mira should consume the Open Targets release dataset directly rather than a simplified list of ChEMBL names.

Mira loads both directories as Spark DataFrames. See [Entity mapping](entity-mapping.md) for how the lookup tables are used.

## ChEMBL 37 PostgreSQL database

The default workflow uses the [ChEMBL 37 PostgreSQL distribution](https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_37/chembl_37_postgresql.tar.gz). The configured default is:

```text
postgresql://localhost:5432/chembl_37
```

Override the address, schema, or credentials with `CHEMBL_DB_URI`, `CHEMBL_DB_SCHEMA`, `CHEMBL_USER`, and `CHEMBL_PASSWORD`.

Mira reads these tables from the standard ChEMBL database:

| Table | Columns selected by the default recipe | Purpose |
| --- | --- | --- |
| `drug_indication` | `drugind_id`, `molregno`, `max_phase_for_ind`, `efo_id`, `efo_term` | Curated drug indications and maximum phase. |
| `indication_refs` | `drugind_id`, `ref_type`, `ref_id`, `ref_url` | Evidence source and traceable reference for each indication. |
| `molecule_dictionary` | `molregno`, `chembl_id`, `pref_name` | Converts internal molecule keys to ChEMBL identifiers and preferred names. |
| `drug_warning` | `warning_id`, `molregno`, warning metadata, EFO fields | Drug warnings and withdrawals. |
| `warning_refs` | `warning_id`, `ref_type`, `ref_id`, `ref_url` | Evidence source and traceable reference for each warning. |

The recipe uses the singular ChEMBL table name `drug_indication`.

See the [ChEMBL provider guide](providers/chembl.md) for the indication and safety evidence contributed, reference-source semantics, and selection rules.

## Legacy ChEMBL clinical-trial mapping

> [!WARNING]
> The current Open Targets workflow can optionally use a mapping file produced from private ChEMBL Oracle curation. This is a legacy internal input and the process is intended for deprecation. It should not form part of the public input-acquisition workflow.

The file contains:

| Column | Meaning |
| --- | --- |
| `studyId` | ClinicalTrials.gov NCT identifier. |
| `drugFromSource` | Intervention label used for the study-and-label match. |
| `drugId` | ChEMBL molecule identifier. |
| `diseaseFromSource` | Condition label used for the study-and-label match. |
| `diseaseId` | EFO identifier. |

Save the export as:

```text
<data_root>/inputs/chembl_mapping.parquet
```

The legacy exporter is [`extract_chembl_ct_curation`](https://github.com/opentargets/mira/blob/main/src/mira/provider/chembl/curation.py). The full recipe currently expects its Parquet output. Public and new workflows should omit it with the override documented in [Run without ChEMBL clinical-trial curation](cli-and-configuration.md#run-without-chembl-clinical-trial-curation).

## AACT

Download the selected PostgreSQL snapshot from the [AACT downloads page](https://aact.ctti-clinicaltrials.org/downloads). AACT publishes current snapshots and archives; record the snapshot date used for a reproducible run.

Mira expects the database schema to be `ctgov` and reads:

- `studies`
- `interventions`
- `conditions`
- `study_references`
- `designs`
- `brief_summaries`
- `detailed_descriptions`
- `sponsors`

The exact selected columns and transformation rules are documented in the [AACT provider guide](providers/aact.md). Database installation and refresh commands will be owned by the future acquisition workflow.

## Therapeutic Target Database

Download [`P1-05-Drug_disease.txt`](https://ttd.idrblab.cn/files/download/P1-05-Drug_disease.txt) and preserve that filename in the default layout.

The Mira parser recognises records by line prefixes:

- `TTDDRUID` for the TTD drug identifier;
- `DRUGNAME` for the drug label;
- `INDICATI` for the disease label, ICD-11 value, and clinical stage.

These fields are separated by tabs. A format change that removes the prefixes, changes their order, or changes the number of indication fields requires a parser update.

See the [TTD provider guide](providers/ttd.md) for the evidence contributed and the transformation and selection rules.

## EMA human medicines

Download the [EMA medicines report workbook](https://www.ema.europa.eu/en/documents/report/medicines-output-medicines-report_en.xlsx) and save it as:

```text
<data_root>/inputs/medicines-output-medicines-report_en.xlsx
```

Mira reads the `Medicine` worksheet. It expects the workbook's first data row to contain the effective column headings and filters `Category` to `Human`.

The provider uses these fields:

- `EMA product number`
- `Medicine status`
- `International non-proprietary name (INN) / common name`
- `Active substance`
- `Name of medicine`
- `Therapeutic area (MeSH)`
- `Therapeutic indication`
- `Medicine URL`
- `Marketing authorisation date`

When `Therapeutic area (MeSH)` is unavailable, Mira uses disease NER on `Therapeutic indication`.

See the [EMA provider guide](providers/ema.md) for the evidence contributed and the label-selection rules.

## PMDA approved products

Open the [PMDA List of Approved Products](https://www.pmda.go.jp/english/review-services/reviews/approved-information/drugs/0002.html) and select the consolidated PDF under **New Drugs**. The link and covered date range change as PMDA updates the list.

Save the chosen PDF as:

```text
<data_root>/inputs/pmda_approvals.pdf
```

The parser discovers tables by headers resembling:

- approval date;
- brand name;
- approval or partial change;
- active ingredient;
- notes.

> [!WARNING]
> It keeps rows whose approval field contains `Approval`, extracts drug names from the active-ingredient column, and applies disease NER to the notes. Because PDF tables are layout-sensitive, record the PDF title and date range and verify parsed row counts whenever the source is refreshed.

See the [PMDA provider guide](providers/pmda.md) for the evidence contributed and the row-selection rules.

## What the acquisition rule should provide

The acquisition mechanism remains open. Whether it is implemented with Make, a script, or another workflow tool, it should:

1. Resolve and record concrete source versions before downloading.
2. Download public files into the paths defined above.
3. Restore or refresh the AACT and ChEMBL databases through separate targets.
4. Avoid redownloading unchanged files when checksums match.
5. Write the release manifest only after each input has been prepared successfully.
6. Validate file type, required directories, database connectivity, tables, and essential columns.
7. Fail with the source name and expected remedy when an input contract changes.

This keeps acquisition reproducible while allowing the provider and mapping documentation to remain focused on data behavior.
