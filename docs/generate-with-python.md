# Generate data with Python

Mira can be used in two ways: by calling its Python API directly, or through its configuration-driven command-line interface. This guide starts with Python so the data flow and function boundaries are visible. The CLI guide will build on the same steps later.

## The generation flow

Generating the two core datasets involves four steps:

1. Load the input tables required by each provider.
2. Use provider functions to create Clinical Reports.
3. Combine the reports and map their drug and disease labels.
4. Aggregate the mapped reports into Clinical Indications.

Provider input formats and acquisition will be covered in the data-input guides. This page focuses on how the Python objects fit together.

## Connect to AACT

Mira includes a PostgreSQL connector that reads a database table directly into a Polars DataFrame. The default configuration expects an AACT database at `localhost:5432/aact`, with ClinicalTrials.gov tables in the `ctgov` schema.

> [!NOTE]
> This guide assumes that database is already available. Read the [AACT provider guide](providers/aact.md) for its table contract, selection rules, metadata handling, and report cardinality. Database acquisition and updates will be documented as a separate input-management workflow.

Build the connection URL using environment variables for credentials:

```python
import os

import polars as pl

from mira.utils.db import construct_db_uri, load_db_table


aact_url = construct_db_uri(
    db_type="postgresql",
    db_uri="localhost:5432/aact",
    db_user=os.getenv("AACT_USER"),
    db_password=os.getenv("AACT_PASSWORD"),
)
```

When the local database does not require authentication, the environment variables can be left unset. For another deployment, replace the host, port, or database name in `db_uri`.

Now load the three tables needed for a small AACT report example:

```python
trial_filter = "nct_id = 'NCT05188521'"

studies = load_db_table(
    table_name="studies",
    db_url=aact_url,
    db_schema="ctgov",
    select_cols=["nct_id", "phase", "study_type", "official_title"],
    where_clause=trial_filter,
)

interventions = load_db_table(
    table_name="interventions",
    db_url=aact_url,
    db_schema="ctgov",
    select_cols=["nct_id", "intervention_type", "name"],
    where_clause=trial_filter,
)

conditions = load_db_table(
    table_name="conditions",
    db_url=aact_url,
    db_schema="ctgov",
    select_cols=["nct_id", "downcase_name"],
    where_clause=trial_filter,
)

assert isinstance(studies, pl.DataFrame)
```

`load_db_table` returns `pl.DataFrame` objects directly. It also supports a row `limit` when a simple bounded preview is more useful than a SQL condition.

> [!WARNING]
> The `where_clause` is inserted into the SQL query, so it should contain trusted application text rather than unchecked user input.

## Create a Clinical Report

Each provider exposes a function that transforms its source data into a `ClinicalReport`. Pass the three AACT DataFrames to its provider function:

```python
from mira.provider.aact import extract_clinical_report


clinical_reports = extract_clinical_report(
    studies=studies,
    interventions=interventions,
    conditions=conditions,
)
```

Provider functions return a `ClinicalReport` object. Its Polars DataFrame is available through `.df`:

```python
clinical_reports.df.select(
    "id",
    "clinicalStage",
    "drugs",
    "diseases",
)
```

> [!NOTE]
> The example produces one Phase II report. At this point the source labels are present, but the drug and disease identifiers are null because mapping has not been run.

## Generate an indication directly

A `ClinicalIndication` can be generated from any valid Clinical Report DataFrame:

```python
from mira.dataset import ClinicalIndication


clinical_indications = ClinicalIndication.from_report(clinical_reports.df)

clinical_indications.df.select(
    "drugName",
    "diseaseName",
    "maxClinicalStage",
    "mappingStatus",
    "clinicalReportIds",
)
```

For the small example, the result is:

```python
{
    "drugName": "baricitinib",
    "diseaseName": "cutaneous lichen planus",
    "maxClinicalStage": "PHASE_2",
    "mappingStatus": "UNMAPPED",
    "clinicalReportIds": ["nct05188521"],
}
```

> [!IMPORTANT]
> This is useful for understanding the API, but Open Targets only displays fully mapped indications. The production flow maps the reports before creating indications.

## Combine reports from several providers

The default Open Targets workflow creates reports independently for AACT, ChEMBL indications, ChEMBL drug warnings, TTD, EMA, and PMDA. Once the provider functions have run, their DataFrames are combined with `union_dfs`:

```python
import polars as pl

from mira.utils.polars_helpers import union_dfs


# AACT is the primary provider for ClinicalTrials.gov records. Remove the
# ClinicalTrials.gov references republished through ChEMBL before combining.
chembl_indications = chembl_indication_reports.df.filter(
    pl.col("source") != "ClinicalTrials"
)

all_reports = union_dfs(
    [
        aact_reports.df,
        ttd_reports.df,
        ema_reports.df,
        pmda_reports.df,
        chembl_indications,
        chembl_drug_warning_reports.df,
    ]
)
```

`union_dfs` performs a diagonal concatenation: core fields line up across providers, and source-specific fields are retained with nulls for records that do not define them.

## Map drugs and diseases

The default workflow maps drug and disease labels after all provider reports have been combined. It uses the Open Targets disease and molecule indices, with optional ChEMBL clinical-trial curation and drug named-entity recognition:

```python
from mira.dataset import ClinicalReport


mapped_reports = ClinicalReport.map_entities(
    spark=spark,
    reports=all_reports,
    disease_index=disease_index,
    drug_index=molecule_index,
    chembl_curation=chembl_curation,
    drug_column_name="drugFromSource",
    disease_column_name="diseaseFromSource",
    ner_extract_drug=True,
    ner_batch_size=256,
    ner_cache_path=".cache/ner/ner_cache.parquet",
)
```

> [!NOTE]
> Here, `spark` is an active Spark session; `disease_index` and `molecule_index` are Spark DataFrames; and `chembl_curation` is an optional Polars DataFrame. Read [Entity mapping](entity-mapping.md) for the mapping order, the different drug and disease paths, ChEMBL curation, NER and failure behavior.

## Generate mapped Clinical Indications

Create Clinical Indications only after mapping when reproducing the Open Targets output:

```python
clinical_indications = ClinicalIndication.from_report(mapped_reports.df)
```

The resulting object includes fully mapped, partially mapped, and unmapped relationships. Filter to `FULLY_MAPPED` to reproduce the subset displayed by Open Targets:

```python
platform_indications = clinical_indications.df.filter(
    pl.col("mappingStatus") == "FULLY_MAPPED"
)
```

Read [Clinical Indication](clinical-indication.md) for the aggregation rules and field meanings.

## Write the datasets

When using the Python API, the caller chooses where and when to write the results:

```python
from pathlib import Path


output_dir = Path("data/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

mapped_reports.df.write_parquet(output_dir / "clinical_report.parquet")
clinical_indications.df.write_parquet(
    output_dir / "clinical_indication.parquet"
)
```

> [!NOTE]
> The CLI applies a dated output directory and writes steps whose names begin with `output_`. That convention belongs to the CLI and YAML execution model; it does not apply automatically when calling the Python API.

## Where provider functions live

Provider implementations are grouped under the [`mira.provider` package](../src/mira/provider/):

- [AACT](../src/mira/provider/aact/)
- [ChEMBL indications](../src/mira/provider/chembl/indications.py)
- [ChEMBL drug warnings](../src/mira/provider/chembl/drug_warnings.py)
- [TTD](../src/mira/provider/ttd.py)
- [EMA](../src/mira/provider/ema.py)
- [PMDA](../src/mira/provider/pmda.py)

Each source guide will document the required inputs before showing its provider call in full.
