<p align="center">
  <img src="https://raw.githubusercontent.com/opentargets/mira/main/assets/brand/mira-logo-1200.png" alt="MIRA logo" width="640">
</p>

<h1 align="center">MIRA</h1>

<p align="center">
  <strong>Multi-source Indication &amp; Report Analytics</strong><br>
  Clinical trial data mining and integration tools for drug discovery.
</p>

<p align="center">
  <a href="https://pypi.org/project/opentargets-mira/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/opentargets-mira?color=173B59"></a>
  <img alt="Supported Python versions" src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3489CA?logo=python&amp;logoColor=white">
  <a href="https://github.com/opentargets/mira/actions/workflows/ci.yaml"><img alt="CI status" src="https://github.com/opentargets/mira/actions/workflows/ci.yaml/badge.svg"></a>
  <a href="https://github.com/opentargets/mira/blob/main/LICENSE"><img alt="Apache 2.0 license" src="https://img.shields.io/github/license/opentargets/mira?color=AED0EA"></a>
</p>

## Motivation

Mining clinical trials is essential for accelerating drug discovery and biomedical research. ClinicalTrials.gov contains a wealth of information on ongoing and completed studies, including interventions, conditions, and outcomes. Systematic extraction and integration of this data enables:

- Mapping of drug–disease relationships
- Identification of drug repurposing opportunities
- Analysis of intervention efficacy and safety

### Key Features

- **Direct Connection to clinical databases like AACT or ChEMBL:** Uses a robust connector to securely access PostgreSQL databases.
- **Automated Table Loading:** Loads and filters relevant tables (studies, interventions, conditions, etc.) using Polars for scalable processing.
- **Drug and Disease Mapping:** Integrates external drug and disease vocabularies to annotate interventions and indications in trials.
- **LLM Extraction:** Uses LLMs to extract structured drug–disease evidence from clinical trial records.
- **Config-Driven Workflows:** All pipelines are defined via YAML recipes — no code changes needed to reconfigure.

## Data Sources

1. **AACT Database**  

    AACT database is a PostgreSQL database containing clinical trial data from the ClinicalTrials.gov database. We use Polars to connect to the database and return queried data in a DataFrame format. Credentials and connection parameters are provided via configuration.

2. **ChEMBL Drug Indication Data**

    JSON file storing indications for drugs, and clinical candidate drugs, from a variety of sources (e.g., FDA, EMA, WHO ATC, ClinicalTrials.gov, INN, USAN).

3. **ChEMBL Clinical Trials Pipeline**

   The private DRUGBASE_CURATION database in ChEMBL stores metadata related to clinical trials. After processing data from ClinicalTrials.gov, their internal pipeline automatically assigns an EFO ID to each condition and a ChEMBL ID to each intervention mentioned in the trials. This database is used to map the conditions and interventions in the AACT database to ChEMBL and EFO IDs, and it **requires a valid ChEMBL user account** to access.

4. **PMDA Database**

   The PMDA (Pharmaceuticals and Medical Devices Agency) is the Japanese regulatory agency. We use their PDF of approved products to extract drug/disease associations. The PDF can be downloaded from their site: https://www.pmda.go.jp/english/review-services/reviews/approved-information/drugs/0002.html

## Usage

### Installation

Install MIRA from PyPI:

```bash
pip install opentargets-mira
```

To include Oracle support:

```bash
pip install "opentargets-mira[oracle]"
```

### Configuration

The project uses a **base config + recipes** pattern:

- **`config.yaml`** — minimal shared infrastructure (database connections, path definitions)
- **`recipe/`** — workflow-specific configurations that extend the base

Run `uv run mira --help` to see available recipes.

### Workflows

#### 1. Clinical Report Generation

Loads data from all providers (AACT, ChEMBL, TTD, EMA, PMDA), generates clinical reports, maps entities to ChEMBL/EFO IDs, and produces the final clinical indication dataset.

```bash
uv run mira +recipe=clinical_report_generation
```

#### 2. LLM Extraction

Loads clinical trial data from AACT and uses an LLM (via OpenAI) to extract structured drug–disease evidence including drug intent, primary indications, investigated drugs, comparators, and supportive medications.

```bash
# Batch extraction with defaults
uv run mira +recipe=aact_llm_extractor

# Single-trial inspect mode (prints to stdout, no output written)
uv run mira +recipe=aact_llm_extractor \
  workflow.transform.generate.filtered_report.parameters.id_value=NCT00002742

# Override any config value
uv run mira +recipe=aact_llm_extractor \
  workflow.transform.generate.output_llm_extraction.parameters.model=gpt-4o

# Enable publications enrichment
uv run mira +recipe=aact_llm_extractor \
  workflow.transform.generate.publications_map.parameters.enabled=true
```
### Configuring a Workflow Step

Each step within a workflow is defined as a dictionary keyed by name:

```yaml
workflow:
  transform:
    generate:
      my_step:                        # step name (becomes data_store key)
        function: mira...  # full Python path
        parameters:
          input: $previous_step       # reference another step's output
          literal_value: 42           # literal values passed as-is
```

To override step parameters from the command line, use the full path:

```bash
uv run mira +recipe=aact_llm_extractor \
  workflow.transform.generate.filtered_report.parameters.id_value=NCT00002742
```

The path follows the structure: `workflow.transform.<section>.<step_name>.parameters.<param>`

### Output

Any step whose name starts with `output_` is automatically persisted:

- **Polars DataFrame** → written as Parquet to `${datasets.output_path}/<date>/<name>.parquet`
- **Dict** → written as JSON to `${datasets.output_path}/<date>/<name>.json`
- **None** → skipped (used for inspect/debug modes)

### Environment Variables

| Variable | Required for |
|---|---|
| `AACT_USER` | AACT database access (optional for localhost) |
| `AACT_PASSWORD` | AACT database access (optional for localhost) |
| `OPENAI_API_KEY` | LLM extraction workflow |
| `MIRA_DATA_DIR` | Local input and output directory (defaults to `data`) |

### Contribute

If you need to add a new data transformation or a new input source, please submit a pull request with the new functionality. Once merged, your function can be integrated into the pipeline via the configuration file.
