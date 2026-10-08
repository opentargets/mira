import pandas as pd
import polars as pl
import pytest

from mira.provider import ema
from mira.provider.ema import extract_marketing_year

EMA_COLUMNS = [
    "Category",
    "Name of medicine",
    "EMA product number",
    "Medicine status",
    "International non-proprietary name (INN) / common name",
    "Active substance",
    "Therapeutic area (MeSH)",
    "Therapeutic indication",
    "Marketing authorisation date",
    "Medicine URL",
]


def _ema_sheet(rows: list[dict]) -> pl.DataFrame:
    """Build the raw EMA sheet: generic column names, real names in the first row."""
    defaults = {
        "Category": "Human",
        "Medicine status": "Authorised",
        "Marketing authorisation date": "19/06/2015",
        "Medicine URL": "https://www.ema.europa.eu/en/medicines/human/EPAR/x",
    }
    records = [dict(zip(EMA_COLUMNS, EMA_COLUMNS))] + [
        {c: r.get(c, defaults.get(c)) for c in EMA_COLUMNS} for r in rows
    ]
    return pl.DataFrame(
        [[rec[c] for c in EMA_COLUMNS] for rec in records],
        schema=[f"column_{i}" for i in range(len(EMA_COLUMNS))],
        orient="row",
    )


def _fake_ner(extracted: dict[str, list[str]]):
    """Stand in for ontoma's spark NER: map each indication text to fixed diseases."""

    class _Result:
        def __init__(self, df: pl.DataFrame):
            self.df = df

        def toPandas(self) -> pd.DataFrame:
            out = self.df.to_pandas()
            out["extracted_diseases"] = [
                extracted[text] for text in out["therapeutic_indication"]
            ]
            return out

    def extract_disease_entities(spark, df, input_col, output_col):
        return _Result(df)

    return extract_disease_entities


def test_extract_clinical_report_keeps_medicine_when_ner_finds_nothing(monkeypatch):
    """A medicine whose indication yields no NER disease is kept through its MeSH term.

    Polars 2.0 explodes an empty list into zero rows, which silently dropped
    these medicines; 1.x kept them as a null row that the MeSH coalesce fills.
    """
    monkeypatch.setattr(
        ema, "convert_polars_to_spark", lambda polars_df, spark: polars_df
    )
    monkeypatch.setattr(
        ema,
        "extract_disease_entities",
        _fake_ner(
            {
                "treatment of breast cancer": ["breast cancer"],
                "see product information": [],
                "nothing to extract": [],
            }
        ),
    )
    sheet = _ema_sheet(
        [
            {
                "Name of medicine": "Alpha",
                "EMA product number": "EMEA/H/C/000001",
                "International non-proprietary name (INN) / common name": "alphamab",
                "Active substance": "alphamab",
                "Therapeutic indication": "treatment of breast cancer",
            },
            {
                # NER finds nothing, but the MeSH term identifies the disease
                "Name of medicine": "Beta",
                "EMA product number": "EMEA/H/C/000002",
                "International non-proprietary name (INN) / common name": "betanib",
                "Active substance": "betanib",
                "Therapeutic area (MeSH)": "Diabetes Mellitus, Type 2",
                "Therapeutic indication": "see product information",
            },
            {
                # Neither NER nor MeSH give a disease: no report
                "Name of medicine": "Gamma",
                "EMA product number": "EMEA/H/C/000003",
                "International non-proprietary name (INN) / common name": "gammastat",
                "Active substance": "gammastat",
                "Therapeutic indication": "nothing to extract",
            },
        ]
    )

    reports = ema.extract_clinical_report(sheet, spark=None).df

    assert sorted(reports["id"].to_list()) == ["emea/h/c/000001", "emea/h/c/000002"]
    diseases = {
        r["id"]: [d["diseaseFromSource"] for d in r["diseases"]]
        for r in reports.iter_rows(named=True)
    }
    assert diseases == {
        "emea/h/c/000001": ["breast cancer"],
        "emea/h/c/000002": ["diabetes mellitus, type 2"],
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("19/06/2015", 2015),
        ("08/03/2002", 2002),
        ("", None),
        (None, None),
        ("not a date", None),
    ],
)
def test_extract_marketing_year(value, expected):
    assert extract_marketing_year(value) == expected


def test_extract_marketing_year_in_select():
    df = pl.DataFrame(
        {"Marketing authorisation date": ["19/06/2015", "", "01/01/2024"]}
    )
    out = df.with_columns(
        year=pl.col("Marketing authorisation date").map_elements(
            extract_marketing_year, return_dtype=pl.Int32
        )
    )
    assert out["year"].to_list() == [2015, None, 2024]
