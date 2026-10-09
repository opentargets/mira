import os

import sparknlp
from ontoma.ner._pipelines import get_device
from pyspark.sql import SparkSession


def spark_session() -> SparkSession:
    """OnToma works on Spark dataframes.

    Under spark-submit (e.g. a Dataproc job), the submitted session is returned, so the
    job keeps the master, resources and jars it was submitted with. Otherwise a local
    Spark NLP session is started.
    """
    if "PYSPARK_GATEWAY_PORT" in os.environ:
        return SparkSession.builder.getOrCreate()
    active = SparkSession.getActiveSession()
    if active is not None:
        active.stop()
    params = {
        "spark.driver.memory": "10g",
        "spark.driver.maxResultSize": "4g",
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        "spark.kryoserializer.buffer.max": "512m",
        "spark.sql.shuffle.partitions": "50",
        "spark.default.parallelism": "4",
        "spark.sql.adaptive.enabled": "true",
        "spark.ui.enabled": "false",
    }
    is_apple_silicon = get_device() == "mps"
    return sparknlp.start(params=params, apple_silicon=is_apple_silicon)
