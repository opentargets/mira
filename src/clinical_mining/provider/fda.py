"""Extraction of FDA new molecular entity approval reports."""

import re
from io import BytesIO

import polars as pl
from loguru import logger
from ontoma.ner.disease import extract_disease_entities
from pyspark.sql import SparkSession

from clinical_mining.dataset import ClinicalReport
from clinical_mining.schemas import (
    ClinicalProvider,
    ClinicalReportOrigin,
    ClinicalReportType,
    ClinicalSource,
)
from clinical_mining.utils.polars_helpers import convert_polars_to_spark

DRUGS_AT_FDA_APPLICATION_URL = (
    "https://www.accessdata.fda.gov/scripts/cder/daf/"
    "index.cfm?event=overview.process&ApplNo="
)


def split_active_ingredients(value: str | None) -> list[str]:
    """Split combination products into their active ingredient or moiety names."""

    _INGREDIENT_SEPARATOR = re.compile(r"\s*(?:,|;|\band\b)\s*", re.IGNORECASE)
    _COPACKAGED_SEPARATOR = re.compile(r"\s*\(co-packaged\)\s*", re.IGNORECASE)

    if not value:
        return []
    ingredients = []
    for ingredient in _INGREDIENT_SEPARATOR.split(value):
        cleaned = _COPACKAGED_SEPARATOR.sub("", ingredient).strip().lower()
        if cleaned and cleaned not in ingredients:
            ingredients.append(cleaned)
    return ingredients


def extract_clinical_report(
    fda_input: str | bytes | BytesIO | pl.DataFrame,
    spark: SparkSession,
) -> ClinicalReport:
    """Extract original drug/indication approvals from the FDA NME compilation."""
    if isinstance(fda_input, pl.DataFrame):
        raw_df = fda_input
    else:
        source = BytesIO(fda_input) if isinstance(fda_input, bytes) else fda_input
        raw_df = pl.read_excel(source, sheet_id=1)

    df = (
        raw_df.rename(
            {column: re.sub(r"\s+", " ", column).strip() for column in raw_df.columns}
        )
        .with_columns(
            activeIngredients=pl.col("Active Ingredient/Moiety").map_elements(
                split_active_ingredients,
                return_dtype=pl.List(pl.String),
            ),
            indicationText=pl.coalesce("Abbreviated Indication(s)", "Approved Use(s)")
            .fill_null("")
            .str.strip_chars(),
        )
        .select(
            id=pl.concat_str(
                pl.col("NDA/BLA").str.to_lowercase(),
                pl.col("Application Number(1)").cast(pl.String),
            ),
            phaseFromSource=pl.col("NDA/BLA"),
            origin=pl.lit(ClinicalReportOrigin.REGULATORY.value),
            type=pl.lit(ClinicalReportType.INDICATION.value),
            year=pl.col("Approval Year").cast(pl.Int32, strict=False),
            source=pl.lit(ClinicalSource.FDA_NME_COMPILATION.value),
            provider=pl.lit(ClinicalProvider.FDA.value),
            countries=pl.lit(["United States"], dtype=pl.List(pl.String)),
            url=pl.concat_str(
                pl.lit(DRUGS_AT_FDA_APPLICATION_URL),
                pl.col("Application Number(1)").cast(pl.String),
            ),
            indicationText=pl.col("indicationText"),
            activeIngredients=pl.col("activeIngredients"),
        )
    )

    logger.info("(fda nme): apply ner to extract diseases from indications")
    reports = (
        pl.from_pandas(
            extract_disease_entities(
                spark,
                df=convert_polars_to_spark(df, spark=spark),
                input_col="indicationText",
                output_col="extracted_diseases",
            ).toPandas()
        )
        .explode("activeIngredients", empty_as_null=True)
        .explode("extracted_diseases", empty_as_null=True)
        .filter(
            pl.col("activeIngredients").is_not_null()
            & pl.col("extracted_diseases").is_not_null()
        )
        .with_columns(
            drug=pl.struct(
                pl.col("activeIngredients").alias("drugFromSource"),
                pl.lit(None, dtype=pl.String).alias("drugId"),
            ),
            disease=pl.struct(
                pl.lit(None, dtype=pl.String).alias("diseaseId"),
                pl.col("extracted_diseases")
                .str.strip_chars()
                .str.to_lowercase()
                .alias("diseaseFromSource"),
            ),
        )
        .drop("activeIngredients", "extracted_diseases", "indicationText")
        .unique()
    )

    return ClinicalReport(
        df=reports.group_by(
            [column for column in reports.columns if column not in ["disease", "drug"]]
        ).agg(
            pl.col("disease").unique().alias("diseases"),
            pl.col("drug").unique().alias("drugs"),
        )
    )
