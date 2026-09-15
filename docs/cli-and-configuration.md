# CLI and YAML configuration

Mira's command-line interface turns a YAML recipe into a sequence of Python function calls. It is useful when we want to generate similar versions of a dataset, e.g. clinical reports from a particular combination of providers, clinical reports with different levels of metadata,...

This guide starts with one ClinicalTrials.gov study from AACT. It then explains how the same configuration model supports the full Open Targets workflow and user-owned recipes.

## Inspect the CLI

From a source checkout, run Mira through `uv`:

```bash
uv run mira --help
```

An installed package also provides the `mira` command directly. The help output lists the packaged recipes:

- `aact_clinical_report` creates reports and indications for one AACT study;
- `clinical_report_generation` runs the complete Open Targets workflow;
- `aact_llm_extractor` is an experimental extraction workflow and is outside the current documentation scope.

Inspect a recipe's fully composed configuration without loading data or running functions:

```bash
uv run mira +recipe=aact_clinical_report --cfg job --resolve
```

> [!TIP]
> This is the safest way to check environment-variable expansion and command-line overrides before a long run.

## Run one AACT study

The introductory recipe connects to an AACT PostgreSQL database and selects `NCT05188521` from the `ctgov` schema. It needs the `studies`, `interventions`, and `conditions` tables.

For the default local connection:

```bash
uv run mira +recipe=aact_clinical_report
```

Set database credentials when the local server requires them:

```bash
export AACT_USER="your-user"
export AACT_PASSWORD="your-password"
uv run mira +recipe=aact_clinical_report
```

Choose another study with its NCT identifier:

```bash
MIRA_AACT_STUDY_ID=NCT00144209 \
  uv run mira +recipe=aact_clinical_report
```

The recipe queries each table with the study filter, rather than loading the complete AACT database and filtering afterwards.

## Find the outputs

Mira writes steps whose names begin with `output_` beneath a dated directory:

```text
data/
└── outputs/
    └── YYYY-MM-DD/
        ├── clinical_report.parquet
        └── clinical_indication.parquet
```

> [!NOTE]
> The introductory recipe does not load the Open Targets disease and molecule indices, so its source labels remain unmapped. Its Clinical Indications normally have `mappingStatus: UNMAPPED`. The recipe demonstrates CLI execution and the data-model transition; the full workflow adds [entity mapping](entity-mapping.md).

Inspect the generated records with Polars:

```python
from datetime import date
from pathlib import Path

import polars as pl


run_dir = Path("data/outputs") / date.today().isoformat()
reports = pl.read_parquet(run_dir / "clinical_report.parquet")
indications = pl.read_parquet(run_dir / "clinical_indication.parquet")

print(reports.select("id", "clinicalStage", "drugs", "diseases"))
print(
    indications.select(
        "drugName",
        "diseaseName",
        "mappingStatus",
        "clinicalReportIds",
    )
)
```

With the current AACT record, the default example produces one Phase II Clinical Report. Its two dose-specific baricitinib intervention labels produce two unmapped Clinical Indications for cutaneous lichen planus. AACT is a live database, so source corrections can change these details over time.

> [!WARNING]
> Running the same recipe more than once on the same day writes to the same filenames. Copy results that must be retained or override the output location for the next run:

```bash
uv run mira +recipe=aact_clinical_report \
  datasets.output_path=/path/to/run-outputs
```

Relative paths are resolved from the directory in which the command starts.

## How configuration is composed

Four layers determine a run, from general defaults to the most specific value:

1. [`config.yaml`](../src/mira/config.yaml) supplies shared database and path defaults.
2. A named file under [`recipe/`](../src/mira/recipe/) adds inputs and workflow steps.
3. Environment interpolation supplies deployment-specific values such as credentials and the data root.
4. Command-line overrides replace individual values for one run.

Recipes begin with:

```yaml
# @package _global_
```

This Hydra directive merges the recipe's `inputs` and `workflow` keys into the root configuration beside the shared defaults.

The following command changes the data root only for that invocation:

```bash
uv run mira +recipe=clinical_report_generation \
  datasets.data_root=/path/to/mira-data
```

Use `--cfg job --resolve` with the same overrides to see the final values without executing the workflow.

## Three kinds of references

Recipe files contain three similar-looking expressions with different purposes.

### Refer to another configuration value

Hydra resolves `${...}` while composing the configuration:

```yaml
path: ${datasets.disease_index_path}
```

This copies the configured value of `datasets.disease_index_path`.

### Read an environment variable

The `oc.env` resolver reads the process environment and can provide a default:

```yaml
data_root: ${oc.env:MIRA_DATA_DIR,data}
```

> [!NOTE]
> This uses `MIRA_DATA_DIR` when it is set and `data` otherwise. Mira reads the process environment; it does not load a `.env` file automatically.

### Refer to a runtime result

A string beginning with `$` refers to an object already held in the current run:

```yaml
parameters:
  report: $output_clinical_report
```

> [!WARNING]
> Mira resolves runtime references in direct parameter values and list elements. It does not recursively resolve `$...` references nested inside dictionaries. A reference must point to an input or an earlier step; forward references fail.

## Anatomy of a recipe

A recipe declares `inputs` and a `workflow`:

```yaml
# @package _global_

inputs:
  studies:
    format: db_table
    db: aact
    select_cols: [nct_id, phase, study_type]
    where_clause: "nct_id = 'NCT05188521'"

workflow:
  transform:
    generate:
      output_clinical_report:
        function: mira.provider.aact.extract_clinical_report
        parameters:
          studies: $studies
          interventions: $interventions
          conditions: $conditions
```

### Inputs

Inputs are loaded before any workflow step. Their keys become names in the runtime data store, so `$studies` refers to the loaded `studies` input.

Mira supports these input formats:

| Format | Loader | Configuration |
| --- | --- | --- |
| `db_table` | PostgreSQL through Polars and ConnectorX | `db` and `select_cols`; optionally `table_name`, `schema`, `where_clause`, and `limit`. |
| `parquet` | Polars by default | `path`. Add `engine: spark` when the function needs a Spark DataFrame. |
| `json` | Polars newline-delimited JSON reader | `path`. The file must be NDJSON, with one JSON value per line. |

For a database input:

- the input key is the table name unless `table_name` is supplied;
- `db` selects a connection under `db_properties` and defaults to `aact`;
- `schema` overrides the schema from that database connection;
- `select_cols` can be a list of columns or `"*"`;
- `where_clause` is SQL text without the `WHERE` keyword;
- `limit` adds a database-side row limit.

> [!WARNING]
> Use trusted text in `where_clause`. Mira inserts the clause into the generated query and does not parameterise it.

Use an explicit engine for Spark data:

```yaml
disease_index:
  format: parquet
  engine: spark
  path: ${datasets.disease_index_path}
```

Spark starts lazily when a Spark input or `$spark_session` parameter is encountered.

### Steps

The transform workflow has three sections, executed in this order:

1. `setup`
2. `generate`
3. `post_process`

Steps run in their YAML order within each section. Every step declares an importable Python function or class method and the keyword arguments passed to it. The step name becomes the runtime key used by later `$...` references.

When a function returns a Mira dataset object such as `ClinicalReport`, the runner stores its `.df` Polars DataFrame. This lets a later step pass `$aact_report` directly to a function expecting a DataFrame.

### Outputs

A step beginning with `output_` is persisted after all transform sections finish:

| Returned value | Written output |
| --- | --- |
| Polars `DataFrame` | Parquet with duplicate rows removed. |
| Python `dict` | JSON. |
| `None` | No file. |

The `output_` prefix is removed from the filename. Other runtime values are intermediate results and are not written automatically. Rename an intermediate step with the prefix when you want to inspect it as a file.

## Base configuration reference

All local dataset defaults live beneath `datasets.data_root`. Setting `MIRA_DATA_DIR` relocates the entire file layout without editing packaged files.

| Key | Type | Default or environment override | Required by | Meaning |
| --- | --- | --- | --- | --- |
| `db_properties.aact.type` | String | `postgresql` | AACT recipes | Database URI scheme. |
| `db_properties.aact.uri` | String | `AACT_DB_URI` or `localhost:5432/aact` | AACT recipes | AACT host, port, and database. The address must be reachable. |
| `db_properties.aact.schema` | String | `AACT_DB_SCHEMA` or `ctgov` | AACT recipes | Default schema for AACT inputs. |
| `db_properties.aact.user` | String | `AACT_USER` or empty | Authenticated AACT deployments | Database username. |
| `db_properties.aact.password` | String | `AACT_PASSWORD` or empty | Authenticated AACT deployments | Database password. |
| `db_properties.chembl.type` | String | `postgresql` | Full workflow | Database URI scheme. |
| `db_properties.chembl.uri` | String | `CHEMBL_DB_URI` or `localhost:5432/chembl_37` | Full workflow | ChEMBL host, port, and database. The address must be reachable. |
| `db_properties.chembl.schema` | String | `CHEMBL_DB_SCHEMA` or `public` | Full workflow | Default schema for ChEMBL inputs. |
| `db_properties.chembl.user` | String | `CHEMBL_USER` or empty | Authenticated ChEMBL deployments | Database username. |
| `db_properties.chembl.password` | String | `CHEMBL_PASSWORD` or empty | Authenticated ChEMBL deployments | Database password. |
| `datasets.data_root` | Path | `MIRA_DATA_DIR` or `data` | All recipes | Root for all default local inputs and outputs. Relative paths start at the launch directory. |
| `datasets.disease_index_path` | Path | `<data_root>/inputs/disease` | Full workflow | Open Targets disease-index directory read by Spark. |
| `datasets.molecule_index_path` | Path | `<data_root>/inputs/drug_molecule` | Full workflow | Open Targets drug-molecule index directory read by Spark. |
| `datasets.chembl_curation_path` | Path | `<data_root>/inputs/chembl_mapping.parquet` | Full workflow with curation | ChEMBL clinical-trial curation Parquet file. |
| `datasets.ttd_path` | Path | `<data_root>/inputs/P1-05-Drug_disease.txt` | Full workflow | TTD source text file. |
| `datasets.ema_path` | Path | `<data_root>/inputs/medicines-output-medicines-report_en.xlsx` | Full workflow | EMA source workbook. |
| `datasets.pmda_path` | Path | `<data_root>/inputs/pmda_approvals.pdf` | Full workflow | PMDA source PDF. |
| `datasets.llm_results` | Path | `<data_root>/inputs/aact_extraction_batch_results` | Full workflow | Directory of previously generated AACT batch-result files. |
| `datasets.output_path` | Path | `<data_root>/outputs` | All CLI recipes | Parent directory for dated outputs; created by Mira. |

> [!IMPORTANT]
> Secrets should come from environment variables or another process-level secret manager. Do not commit them to a recipe.

## Use your own recipe

Keep deployment-specific recipes outside the installed package. Create a configuration directory containing a `recipe` subdirectory:

```text
mira-config/
└── recipe/
    └── my_pipeline.yaml
```

Run it by adding that directory to Hydra's configuration search path:

```bash
uv run mira \
  --config-dir /absolute/path/to/mira-config \
  +recipe=my_pipeline
```

The user-owned recipe still inherits Mira's packaged `config.yaml`. This approach works after installation and avoids editing `site-packages`.

## Run the complete Open Targets workflow

The full recipe is [`clinical_report_generation.yaml`](../src/mira/recipe/clinical_report_generation.yaml). It expects both databases and the following layout beneath `MIRA_DATA_DIR`:

```text
<MIRA_DATA_DIR>/
├── inputs/
│   ├── disease/
│   ├── drug_molecule/
│   ├── chembl_mapping.parquet
│   ├── P1-05-Drug_disease.txt
│   ├── medicines-output-medicines-report_en.xlsx
│   ├── pmda_approvals.pdf
│   └── aact_extraction_batch_results/
└── outputs/
```

> [!NOTE]
> The batch-results directory must contain OpenAI Batch response files ending in `_output.jsonl`, in the format consumed by `parse_batch_results`. Producing those files belongs to the deferred LLM extraction workflow.

After placing the files and setting the AACT and ChEMBL connection variables, inspect the resolved plan:

```bash
MIRA_DATA_DIR=/path/to/mira-data \
  uv run mira +recipe=clinical_report_generation --cfg job --resolve
```

Then run it:

```bash
MIRA_DATA_DIR=/path/to/mira-data \
  uv run mira +recipe=clinical_report_generation
```

This workflow loads AACT and ChEMBL tables, creates reports for all configured providers, maps drugs and diseases, and writes `clinical_report.parquet` and `clinical_indication.parquet`.

See [Data inputs](data-inputs.md) for authoritative source links, release alignment, required database tables, file contracts, and the planned acquisition boundary.

## Common configuration changes

### Disable drug NER

```bash
uv run mira +recipe=clinical_report_generation \
  workflow.transform.post_process.output_clinical_report.parameters.ner_extract_drug=false
```

### Change the NER cache

```bash
uv run mira +recipe=clinical_report_generation \
  workflow.transform.post_process.output_clinical_report.parameters.ner_cache_path=/path/to/ner-cache.parquet
```

### Run without ChEMBL clinical-trial curation

Remove the input and pass a null value to the mapping function:

```bash
uv run mira +recipe=clinical_report_generation \
  '~inputs.chembl_curation' \
  workflow.transform.post_process.output_clinical_report.parameters.chembl_curation=null
```

The mapper will continue with OnToma label mapping and the optional drug NER fallback. See [Entity mapping](entity-mapping.md) for the effect on mapping precedence.

### Save an intermediate step

Outputs are selected by step name. In a copied recipe, rename a step such as `all_reports` to `output_all_reports`, then update later references from `$all_reports` to `$output_all_reports`. Mira will persist it as `all_reports.parquet` and continue passing the same DataFrame to later steps.

## Relevant implementation

- [`mira.cli`](../src/mira/cli.py) loads inputs, runs sections, and writes outputs.
- [`mira.utils.pipeline`](../src/mira/utils/pipeline.py) imports callables and resolves runtime references.
- [`mira.utils.db`](../src/mira/utils/db.py) constructs database queries and returns Polars DataFrames.
- [Packaged recipes](../src/mira/recipe/) define the supported workflows.
