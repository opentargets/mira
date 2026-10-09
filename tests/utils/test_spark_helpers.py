from types import SimpleNamespace

from mira.utils import spark_helpers


def _fake_spark_session(submitted):
    return SimpleNamespace(
        builder=SimpleNamespace(getOrCreate=lambda: submitted),
        getActiveSession=lambda: None,
    )


def test_spark_submit_keeps_the_submitted_session(monkeypatch):
    submitted = object()
    monkeypatch.setenv("PYSPARK_GATEWAY_PORT", "12345")
    monkeypatch.setattr(spark_helpers, "SparkSession", _fake_spark_session(submitted))

    def fail(**_):
        raise AssertionError("sparknlp.start must not replace a submitted session")

    monkeypatch.setattr(spark_helpers.sparknlp, "start", fail)

    assert spark_helpers.spark_session() is submitted


def test_plain_python_starts_a_local_spark_nlp_session(monkeypatch):
    started = object()
    monkeypatch.delenv("PYSPARK_GATEWAY_PORT", raising=False)
    monkeypatch.setattr(spark_helpers, "SparkSession", _fake_spark_session(object()))
    monkeypatch.setattr(spark_helpers, "get_device", lambda: "cpu")
    monkeypatch.setattr(spark_helpers.sparknlp, "start", lambda **_: started)

    assert spark_helpers.spark_session() is started
