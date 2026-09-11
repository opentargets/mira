import polars as pl

from clinical_mining.provider import fda
from clinical_mining.schemas import ClinicalStageCategory


def test_split_active_ingredients_handles_combination_products():
    assert fda.split_active_ingredients(
        "elexacaftor, ivacaftor, tezacaftor; ivacaftor (co-packaged)"
    ) == ["elexacaftor", "ivacaftor", "tezacaftor"]
    assert fda.split_active_ingredients(
        "vanzacaftor, tezacaftor and deutivacaftor"
    ) == ["vanzacaftor", "tezacaftor", "deutivacaftor"]


class _FakeSparkDataFrame:
    def __init__(self, df: pl.DataFrame):
        self.df = df

    def toPandas(self):
        return self.df.to_pandas()


def test_extract_clinical_report_uses_both_indication_columns(monkeypatch):
    raw_df = pl.DataFrame(
        {
            "Active Ingredient/Moiety": [
                "leuprolide acetate",
                "vanzacaftor, tezacaftor and deutivacaftor",
            ],
            "NDA/BLA": ["NDA", "NDA"],
            " Application Number(1)": [19010, 218730],
            " Application Number(2)": [None, 218731],
            "Approval Year": [1985, 2024],
            "Abbreviated Indication(s)": [
                "palliative treatment of advanced prostatic cancer",
                None,
            ],
            "Approved Use(s)": [
                None,
                "Treatment of cystic fibrosis in eligible patients.",
            ],
        }
    )

    monkeypatch.setattr(
        fda,
        "convert_polars_to_spark",
        lambda polars_df, spark: polars_df,
    )

    def fake_extract_disease_entities(
        spark,
        df,
        input_col,
        output_col,  # noqa: ARG001
    ):
        assert df[input_col].to_list() == [
            "palliative treatment of advanced prostatic cancer",
            "Treatment of cystic fibrosis in eligible patients.",
        ]
        return _FakeSparkDataFrame(
            df.with_columns(
                pl.Series(output_col, [["prostatic cancer"], ["cystic fibrosis"]])
            )
        )

    monkeypatch.setattr(fda, "extract_disease_entities", fake_extract_disease_entities)

    reports = fda.extract_clinical_report(raw_df, spark=object()).df.sort("id")

    assert reports["id"].to_list() == ["nda19010", "nda218730"]
    assert reports["clinicalStage"].to_list() == [
        ClinicalStageCategory.APPROVAL.value,
        ClinicalStageCategory.APPROVAL.value,
    ]
    assert reports["phaseFromSource"].to_list() == ["NDA", "NDA"]
    assert reports["year"].to_list() == [1985, 2024]
    assert reports["source"].to_list() == [
        "FDA NME Compilation",
        "FDA NME Compilation",
    ]
    assert reports["provider"].to_list() == ["FDA", "FDA"]
    assert reports["countries"].to_list() == [["United States"], ["United States"]]
    assert sorted(
        drug["drugFromSource"] for drug in reports.row(1, named=True)["drugs"]
    ) == ["deutivacaftor", "tezacaftor", "vanzacaftor"]
    assert reports.row(0, named=True)["diseases"] == [
        {"diseaseFromSource": "prostatic cancer", "diseaseId": None}
    ]
