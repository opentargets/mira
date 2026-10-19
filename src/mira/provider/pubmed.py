"""PubMed publication fetching utilities using the NCBI E-utilities API."""

import sys
import time
import xml.etree.ElementTree as ET

import httpx
from loguru import logger

EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
# Contact address NCBI asks E-utilities clients to send alongside the tool name.
CONTACT_EMAIL = "data@opentarget.org"


def _iter_batches(items: list[int | str], batch_size: int) -> list[list[int | str]]:
    """Split a list into contiguous batches."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def _is_retryable(exc: Exception) -> bool:
    """Whether a failed efetch call is worth retrying (network or server-side error)."""
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


def _element_text(element: ET.Element | None) -> str:
    """Return all text of an element, including text nested in inline markup."""
    if element is None:
        return ""
    return "".join(element.itertext())


def _parse_articles(xml: bytes) -> dict[str, dict]:
    """Extract title and abstractText per PMID from a PubmedArticleSet document."""
    publications = {}
    for article in ET.fromstring(xml).iterfind("PubmedArticle"):
        citation = article.find("MedlineCitation")
        if citation is None:
            continue
        pmid = citation.findtext("PMID", default="")
        article_data = citation.find("Article")
        title = _element_text(
            article_data.find("ArticleTitle") if article_data is not None else None
        )
        abstract_chunks = (
            article_data.iterfind("Abstract/AbstractText")
            if article_data is not None
            else []
        )
        abstract = " ".join(_element_text(chunk) for chunk in abstract_chunks)
        publications[pmid] = {
            "title": title,
            "abstractText": abstract,
        }
    return publications


def fetch_publications(
    pmids: list[int | str], batch_size: int = 1_000, max_retries: int = 2
) -> dict[str, dict]:
    """Fetch title and abstractText from the E-utilities API for a list of PubMed IDs."""
    if not pmids:
        return {}

    publications = {}
    total_batches = (len(pmids) + batch_size - 1) // batch_size
    with httpx.Client(timeout=60.0) as client:
        for idx, batch in enumerate(
            _iter_batches(pmids, batch_size=batch_size), start=1
        ):
            for attempt in range(1, max_retries + 1):
                try:
                    # POST, as large ID lists do not fit in a GET query string.
                    response = client.post(
                        EFETCH_URL,
                        data={
                            "db": "pubmed",
                            "id": ",".join(str(pmid) for pmid in batch),
                            "rettype": "medline",
                            "retmode": "xml",
                            "tool": "opentargets-mira",
                            "email": CONTACT_EMAIL,
                        },
                    )
                    response.raise_for_status()
                    publications.update(_parse_articles(response.content))

                    logger.info(
                        "Fetched PubMed batch {}/{} (size={}, cumulative={})",
                        idx,
                        total_batches,
                        len(batch),
                        len(publications),
                    )
                    break
                except Exception as exc:
                    if not _is_retryable(exc):
                        print(
                            f"Warning: efetch failed for batch {idx}/{total_batches} "
                            f"(size={len(batch)}): {exc}",
                            file=sys.stderr,
                        )
                        break
                    logger.warning(
                        "efetch failed for batch {}/{} (size={}) attempt {}/{}: {}",
                        idx,
                        total_batches,
                        len(batch),
                        attempt,
                        max_retries,
                        exc,
                    )
                    if attempt < max_retries:
                        time.sleep(attempt)
                    else:
                        print(
                            f"Warning: efetch failed for batch {idx}/{total_batches} "
                            f"(size={len(batch)}): {exc}",
                            file=sys.stderr,
                        )

    return publications


def build_publications_map(
    records: list[dict],
    max_pubs: int = 1,
) -> dict[str, list[dict]]:
    """Pre-fetch selected publications for a list of records.

    Selects up to max_pubs PMIDs per trial, batch-fetches only those
    unique PMIDs, then returns {nct_id: [pub_dict, ...]}.
    """
    if max_pubs <= 0:
        return {}

    selected_pmids_by_trial: dict[str, list[str]] = {}
    selected_pmids: set[str] = set()
    for record in records:
        nct_id = record["id"]
        trial_pmids = [
            str(ref["id"]) for ref in (record.get("trialLiterature") or [])[:max_pubs]
        ]
        if trial_pmids:
            selected_pmids_by_trial[nct_id] = trial_pmids
            selected_pmids.update(trial_pmids)

    if not selected_pmids:
        return {}

    logger.info(
        "Preparing publication fetch for {} selected unique PMIDs across {} records (max_pubs={})",
        len(selected_pmids),
        len(records),
        max_pubs,
    )

    pub_lookup = fetch_publications(list(selected_pmids))

    result: dict[str, list[dict]] = {}
    for nct_id, pmids in selected_pmids_by_trial.items():
        pubs = [pub_lookup[pmid] for pmid in pmids if pmid in pub_lookup]
        if pubs:
            result[nct_id] = pubs
    return result
