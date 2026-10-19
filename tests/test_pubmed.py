"""Tests for PubMed publication fetching utilities."""

from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import parse_qs

import httpx

from mira.provider.pubmed import (
    build_publications_map,
    fetch_publications,
)

# ---------------------------------------------------------------------------
# Sample efetch XML responses
# ---------------------------------------------------------------------------


def _article(pmid: str, title: str, abstract_chunks: list[str] | None) -> str:
    abstract = ""
    if abstract_chunks is not None:
        texts = "".join(
            f"<AbstractText>{chunk}</AbstractText>" for chunk in abstract_chunks
        )
        abstract = f"<Abstract>{texts}</Abstract>"
    return (
        "<PubmedArticle><MedlineCitation>"
        f'<PMID Version="1">{pmid}</PMID>'
        f"<Article><ArticleTitle>{title}</ArticleTitle>{abstract}</Article>"
        "</MedlineCitation></PubmedArticle>"
    )


def _article_set(*articles: str) -> bytes:
    return f"<PubmedArticleSet>{''.join(articles)}</PubmedArticleSet>".encode()


SINGLE_ARTICLE = _article_set(_article("12345678", "Paper A", ["Abstract", "A."]))

TWO_ARTICLES = _article_set(
    _article("12345678", "Paper A", ["Abstract", "A."]),
    _article("99999999", "Paper B", ["Abstract", "B."]),
)


@contextmanager
def _mock_efetch(*responses):
    """Serve *responses* in order from efetch; exceptions are raised instead of returned."""
    calls: list[httpx.Request] = []
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        response = queue.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    real_client = httpx.Client
    with (
        patch(
            "mira.provider.pubmed.httpx.Client",
            lambda **kwargs: real_client(
                transport=httpx.MockTransport(handler), **kwargs
            ),
        ),
        patch("mira.provider.pubmed.time.sleep"),
    ):
        yield calls


# ---------------------------------------------------------------------------
# fetch_publications
# ---------------------------------------------------------------------------


def test_fetch_publications_empty_list():
    assert fetch_publications([]) == {}


def test_fetch_publications_success():
    with _mock_efetch(httpx.Response(200, content=TWO_ARTICLES)) as calls:
        result = fetch_publications([12345678, 99999999])

    assert result["12345678"]["title"] == "Paper A"
    assert result["12345678"]["abstractText"] == "Abstract A."
    assert result["99999999"]["title"] == "Paper B"
    assert result["99999999"]["abstractText"] == "Abstract B."
    params = parse_qs(calls[0].content.decode())
    assert params["id"] == ["12345678,99999999"]
    assert params["email"] == ["data@opentargets.org"]


def test_fetch_publications_missing_abstract_becomes_empty_string():
    no_abstract = _article_set(_article("11111111", "Title only", None))
    with _mock_efetch(httpx.Response(200, content=no_abstract)):
        result = fetch_publications([11111111])

    assert result["11111111"]["title"] == "Title only"
    assert result["11111111"]["abstractText"] == ""


def test_fetch_publications_keeps_text_inside_inline_markup():
    markup = _article_set(
        _article("22222222", "Effect of <i>TP53</i>", ["CO<sub>2</sub> levels."])
    )
    with _mock_efetch(httpx.Response(200, content=markup)):
        result = fetch_publications([22222222])

    assert result["22222222"]["title"] == "Effect of TP53"
    assert result["22222222"]["abstractText"] == "CO2 levels."


def test_fetch_publications_batches_requests():
    with _mock_efetch(
        httpx.Response(200, content=_article_set(_article("1", "One", ["A"]))),
        httpx.Response(200, content=_article_set(_article("2", "Two", ["B"]))),
    ) as calls:
        result = fetch_publications([1, 2], batch_size=1)

    assert set(result) == {"1", "2"}
    assert len(calls) == 2


def test_fetch_publications_retries_on_transport_error():
    with _mock_efetch(
        httpx.RemoteProtocolError("incomplete read"),
        httpx.Response(200, content=SINGLE_ARTICLE),
    ) as calls:
        result = fetch_publications([12345678], max_retries=2)

    assert result["12345678"]["title"] == "Paper A"
    assert len(calls) == 2


def test_fetch_publications_retries_on_server_error():
    with _mock_efetch(
        httpx.Response(503),
        httpx.Response(200, content=SINGLE_ARTICLE),
    ) as calls:
        result = fetch_publications([12345678], max_retries=2)

    assert result["12345678"]["title"] == "Paper A"
    assert len(calls) == 2


def test_fetch_publications_does_not_retry_client_error(capsys):
    with _mock_efetch(httpx.Response(400)) as calls:
        result = fetch_publications([12345678], max_retries=2)

    assert result == {}
    assert len(calls) == 1
    assert "efetch failed" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# build_publications_map
# ---------------------------------------------------------------------------


def test_build_publications_map_basic():
    records = [
        {
            "id": "NCT00000001",
            "trialLiterature": [
                {"id": "12345678", "type": "result"},
                {"id": "99999999", "type": "background"},
            ],
        },
        {
            "id": "NCT00000002",
            "trialLiterature": [{"id": "12345678", "type": "result"}],
        },
        {"id": "NCT00000003", "trialLiterature": None},
    ]
    pub_data = {
        "12345678": {"title": "Paper A", "abstractText": "Abstract A"},
        "99999999": {"title": "Paper B", "abstractText": "Abstract B"},
    }
    with patch("mira.provider.pubmed.fetch_publications", return_value=pub_data):
        result = build_publications_map(records, max_pubs=2)

    assert len(result["NCT00000001"]) == 2
    assert result["NCT00000001"][0]["title"] == "Paper A"
    assert len(result["NCT00000002"]) == 1
    assert result.get("NCT00000003") is None


def test_build_publications_map_respects_max_pubs():
    records = [
        {
            "id": "NCT00000001",
            "trialLiterature": [{"id": str(i), "type": "result"} for i in range(1, 6)],
        }
    ]
    pub_data = {
        str(i): {"title": f"Paper {i}", "abstractText": f"Abs {i}"} for i in range(1, 6)
    }
    with patch("mira.provider.pubmed.fetch_publications", return_value=pub_data):
        result = build_publications_map(records, max_pubs=3)

    assert len(result["NCT00000001"]) == 3


def test_build_publications_map_deduplicates_pmids():
    records = [
        {
            "id": "NCT00000001",
            "trialLiterature": [
                {"id": "111", "type": "result"},
                {"id": "222", "type": "background"},
            ],
        },
        {
            "id": "NCT00000002",
            "trialLiterature": [
                {"id": "222", "type": "result"},
                {"id": "333", "type": "result"},
            ],
        },
    ]
    with patch(
        "mira.provider.pubmed.fetch_publications", return_value={}
    ) as mock_fetch:
        build_publications_map(records, max_pubs=3)

    assert mock_fetch.call_count == 1
    assert set(mock_fetch.call_args[0][0]) == {"111", "222", "333"}
