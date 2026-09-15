from pathlib import Path

import polars as pl
from omegaconf import OmegaConf

from mira import cli


def test_packaged_dataset_paths_share_a_portable_data_root(monkeypatch):
    monkeypatch.delenv("MIRA_DATA_DIR", raising=False)
    config_path = Path(cli.__file__).parent / "config.yaml"
    config_text = config_path.read_text()
    cfg = OmegaConf.load(config_path)

    assert "oc.env:HOME" not in config_text
    assert cfg.datasets.data_root == "data"
    assert cfg.datasets.disease_index_path == "data/inputs/disease"
    assert cfg.datasets.molecule_index_path == "data/inputs/drug_molecule"
    assert cfg.datasets.chembl_curation_path == "data/inputs/chembl_mapping.parquet"
    assert cfg.datasets.llm_results == "data/inputs/aact_extraction_batch_results"
    assert cfg.datasets.output_path == "data/outputs"


def test_db_input_options_are_forwarded(monkeypatch, tmp_path):
    calls = []

    def fake_load_db_table(**kwargs):
        calls.append(kwargs)
        return pl.DataFrame({"nct_id": ["NCT05188521"]})

    monkeypatch.setattr(cli, "load_db_table", fake_load_db_table)

    cfg = OmegaConf.create(
        {
            "db_properties": {
                "aact": {
                    "type": "postgresql",
                    "uri": "localhost:5432/aact",
                    "schema": "ctgov",
                    "user": "",
                    "password": "",
                }
            },
            "datasets": {"output_path": str(tmp_path)},
            "inputs": {
                "trial_subset": {
                    "format": "db_table",
                    "db": "aact",
                    "table_name": "studies",
                    "schema": "archive",
                    "select_cols": ["nct_id"],
                    "where_clause": "nct_id = 'NCT05188521'",
                    "limit": 1,
                }
            },
        }
    )

    result = cli._run_transform(OmegaConf.create({}), cfg)

    assert result["trial_subset"].to_dicts() == [{"nct_id": "NCT05188521"}]
    assert calls == [
        {
            "table_name": "studies",
            "db_url": "postgresql://localhost:5432/aact",
            "select_cols": ["nct_id"],
            "db_schema": "archive",
            "limit": 1,
            "where_clause": "nct_id = 'NCT05188521'",
        }
    ]


def test_spark_engine_does_not_depend_on_input_name(monkeypatch, tmp_path):
    loaded = object()

    class FakeReader:
        def load(self, path, format):
            assert path == "/data/disease"
            assert format == "parquet"
            return loaded

    class FakeSpark:
        read = FakeReader()

    monkeypatch.setattr(cli, "spark_session", FakeSpark)
    cfg = OmegaConf.create(
        {
            "db_properties": {},
            "datasets": {"output_path": str(tmp_path)},
            "inputs": {
                "disease_index": {
                    "format": "parquet",
                    "engine": "spark",
                    "path": "/data/disease",
                }
            },
        }
    )

    result = cli._run_transform(OmegaConf.create({}), cfg)

    assert result["disease_index"] is loaded
    assert isinstance(result["spark_session"], FakeSpark)
