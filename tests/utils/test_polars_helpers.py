import datetime as dt

import polars as pl
import pytest
from pyspark.sql import SparkSession

from mira.utils.polars_helpers import convert_polars_to_spark


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[1]")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


def _collect(df: pl.DataFrame, spark: SparkSession, chunk_size: int) -> list[tuple]:
    rows = convert_polars_to_spark(df, spark, chunk_size=chunk_size).collect()
    return sorted((tuple(r) for r in rows), key=lambda r: r[0] or "")


@pytest.mark.parametrize("chunk_size", [100, 2], ids=["direct", "chunked"])
def test_convert_polars_to_spark_keeps_null_strings(spark, chunk_size):
    """Null strings reach spark as nulls, not as "nan" strings (pandas 3)."""
    df = pl.DataFrame({"s": ["a", None, "c"], "t": [None, "x", None]})

    assert _collect(df, spark, chunk_size) == [(None, "x"), ("a", None), ("c", None)]


@pytest.mark.parametrize("chunk_size", [100, 2], ids=["direct", "chunked"])
def test_convert_polars_to_spark_keeps_nulls_in_other_types(spark, chunk_size):
    df = pl.DataFrame(
        {
            "s": ["a", None, "c"],
            "i": [1, None, 3],
            "f": [1.5, None, 2.5],
            "b": [True, None, False],
            "d": [dt.date(2020, 1, 2), None, dt.date(1999, 12, 31)],
        }
    )

    assert _collect(df, spark, chunk_size) == [
        (None, None, None, None, None),
        ("a", 1, 1.5, True, dt.date(2020, 1, 2)),
        ("c", 3, 2.5, False, dt.date(1999, 12, 31)),
    ]
