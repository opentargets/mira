import polars as pl
from pyspark.sql.types import ArrayType, StringType

from clinical_mining.utils.polars_helpers import (
    _polars_to_pandas,
    polars_to_spark_type,
)


def test_polars_list_type_maps_to_spark_array_type():
    assert polars_to_spark_type(pl.List(pl.String)) == ArrayType(
        StringType(), containsNull=True
    )


def test_polars_list_cells_are_python_lists_for_spark():
    polars_df = pl.DataFrame(
        {"ingredients": [["leuprolide acetate"], ["vanzacaftor", "tezacaftor"]]}
    )

    pandas_df = _polars_to_pandas(polars_df)

    assert isinstance(pandas_df["ingredients"].iloc[0], list)
    assert pandas_df["ingredients"].to_list() == [
        ["leuprolide acetate"],
        ["vanzacaftor", "tezacaftor"],
    ]
