"""Source-specific HTML/JSON extraction with a shared canonical output."""

from __future__ import annotations

import html as html_module
import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from ..io import SOURCE_LANGUAGE, utc_now
from ..labels import FiveLevelLabel, normalize_label, to_binary


def _soup(html: str):
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install collector dependencies with: pip install -e '.[collect]'") from exc
    return BeautifulSoup(html, "html.parser")


def _meta(soup, key: str) -> str:
    node = soup.select_one(f'meta[property="{key}"]') or soup.select_one(f'meta[name="{key}"]')
    return str(node.get("content", "")).strip() if node else ""


def _jsonld_nodes(soup):
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            value = json.loads(tag.string or tag.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, dict) and isinstance(item.get("@graph"), list):
                yield from item["@graph"]
            else:
                yield item


def _links(soup, base_url: str) -> list[str]:
    result = []
    own_domain = urlparse(base_url).netloc.removeprefix("www.")
    for node in soup.select("article a[href], main a[href]"):
        url = urljoin(base_url, node.get("href", "")).split("#")[0]
        parsed = urlparse(url)
        if (
            parsed.scheme in {"http", "https"}
            and parsed.netloc.removeprefix("www.") != own_domain
            and url not in result
        ):
            result.append(url)
    return result


def _record(
    *, source: str, source_id: str, claim: str, source_label: str, explanation: str,
    image_url: str, fact_check_url: str, published_at: str, keywords: list[str],
    evidence_urls: list[str], claim_source_url: str = ""
) -> dict:
    label = normalize_label(source_label)
    return {
        "id": f"{source}-{source_id}",
        "source": source,
        "language": SOURCE_LANGUAGE[source],
        "claim": re.sub(r"\s+", " ", html_module.unescape(claim)).strip(),
        "label_five": label.value,
        "label_binary": None if label is FiveLevelLabel.UNKNOWN else to_binary(label),
        "label_source": source_label,
        "explanation": re.sub(r"\s+", " ", html_module.unescape(explanation)).strip(),
        "image_url": image_url,
        "fact_check_url": fact_check_url,
        "published_at": published_at,
        "claim_source_url": claim_source_url,
        "keywords": [x for x in keywords if x],
        "tags": [],
        "evidence_urls": evidence_urls,
        "evidence_domains": sorted({urlparse(x).netloc.removeprefix("www.") for x in evidence_urls}),
        "collected_at": utc_now(),
        "quality_flags": (["unknown_label"] if label is FiveLevelLabel.UNKNOWN else [])
        + (["missing_explanation"] if not explanation.strip() else []),
        "source_num": source_id,
    }


def parse_snopes(html: str, url: str) -> dict:
    soup = _soup(html)
    article: dict[str, Any] = {}
    review: dict[str, Any] = {}
    for node in _jsonld_nodes(soup):
        if not isinstance(node, dict):
            continue
        kind = node.get("@type")
        if kind in {"Article", "NewsArticle"}:
            article = node
        elif kind == "ClaimReview":
            review = node
    rating = review.get("reviewRating", {})
    source_label = rating.get("alternateName", "") if isinstance(rating, dict) else ""
    claim = review.get("claimReviewed") or article.get("description")
    image = article.get("thumbnailUrl") or _meta(soup, "og:image")
    if isinstance(image, list):
        image = image[0] if image else ""
    paragraphs = [x.get_text(" ", strip=True) for x in soup.select("article p")]
    paragraphs = [x for x in paragraphs if x and x.lower() != "about this rating"]
    keywords = article.get("keywords", "")
    if isinstance(keywords, str):
        keywords = [x.strip() for x in keywords.split(",")]
    source_id = urlparse(url).path.rstrip("/").split("/")[-1]
    return _record(
        source="snopes", source_id=source_id, claim=str(claim or ""),
        source_label=str(source_label), explanation=" ".join(paragraphs),
        image_url=str(image or ""), fact_check_url=url,
        published_at=str(review.get("datePublished") or article.get("datePublished") or ""),
        keywords=list(keywords or []), evidence_urls=_links(soup, url),
    )


def parse_poligrafo(html: str, url: str) -> dict:
    soup = _soup(html)
    title = soup.select_one("h1")
    claim = title.get_text(" ", strip=True) if title else _meta(soup, "og:title")
    rating = soup.select_one(".fact-check-result")
    source_label = rating.get_text(" ", strip=True) if rating else ""
    paragraphs = [x.get_text(" ", strip=True) for x in soup.select("article p, .elementor-widget-container p")]
    boilerplate = "O primeiro jornal português de Fact-Checking"
    paragraphs = [x for x in paragraphs if x and x != boilerplate]
    published = ""
    for node in _jsonld_nodes(soup):
        if isinstance(node, dict) and node.get("datePublished"):
            published = str(node["datePublished"])
            break
    source_id = urlparse(url).path.rstrip("/").split("/")[-1]
    return _record(
        source="poligrafo", source_id=source_id, claim=claim,
        source_label=source_label, explanation=" ".join(paragraphs),
        image_url=_meta(soup, "og:image"), fact_check_url=url,
        published_at=published, keywords=[], evidence_urls=_links(soup, url),
    )


def _pagella_label(article: dict) -> str:
    acf = article.get("acf") or {}
    verdict = acf.get("verdetto") or {}
    text = verdict.get("testo", "") if isinstance(verdict, dict) else str(verdict)
    title = html_module.unescape(str((article.get("title") or {}).get("rendered", "")))
    supporting = str(article.get("_supporting_text", ""))
    combined = f"{title} {text} {supporting}".lower()
    if any(x in combined for x in ("non è vero", "falso", "panzana", "pinocchio")):
        return "False"
    if any(x in combined for x in ("fuorviante", "imprecis", "ingannevol", "nì", "nì")):
        return "Mostly False"
    if any(
        x in combined
        for x in (
            "esagerat",
            "quasi vero",
            "c'eri quasi",
            "parzialmente",
            "corretti, ma",
            "corretto, ma",
            "corretta, ma",
            "ha ragione, ma",
            "troppo netto",
        )
    ):
        return "Mostly True"
    if any(x in combined for x in ("è vero", "ha ragione", "vero")):
        return "True"
    return "Unknown"


def enrich_pagella(article: dict, linked_post: dict) -> dict:
    """Attach the matching article section when the declaration endpoint is sparse."""

    enriched = dict(article)
    claim = str((article.get("acf") or {}).get("sentenza") or "")
    claim_tokens = set(re.findall(r"\w+", claim.lower()))
    best_score = -1.0
    best_html = ""
    for section in (linked_post.get("acf") or {}).get("editor") or []:
        if not isinstance(section, dict) or section.get("acf_fc_layout") != "paragrafo":
            continue
        section_html = str(section.get("testo") or "")
        section_text = _soup(section_html).get_text(" ", strip=True)
        section_tokens = set(re.findall(r"\w+", section_text.lower()))
        overlap = len(claim_tokens & section_tokens) / max(1, len(claim_tokens))
        contains = bool(claim and claim.lower() in section_text.lower())
        score = overlap + (2.0 if contains else 0.0)
        if score > best_score:
            best_score = score
            best_html = section_html
    if best_html and best_score >= 0.25:
        enriched["_supporting_html"] = best_html
        enriched["_supporting_text"] = _soup(best_html).get_text(" ", strip=True)
    enriched["_linked_post"] = linked_post
    return enriched


def parse_pagella(article: dict) -> dict:
    acf = article.get("acf") or {}
    claim = acf.get("sentenza") or (article.get("title") or {}).get("rendered", "")
    explanation = ""
    verdict = acf.get("verdetto") or {}
    if isinstance(verdict, dict):
        explanation = str(verdict.get("testo") or "")
        short = verdict.get("in_breve")
        if isinstance(short, list):
            explanation += " " + " ".join(str(x.get("testo", "")) for x in short if isinstance(x, dict))
    if not explanation.strip():
        explanation = str(article.get("_supporting_text", ""))
    media = (article.get("_embedded") or {}).get("wp:featuredmedia") or []
    if not media:
        media = (
            (article.get("_linked_post") or {}).get("_embedded") or {}
        ).get("wp:featuredmedia") or []
    image = media[0].get("source_url", "") if media else ""
    terms = (article.get("_embedded") or {}).get("wp:term") or []
    keywords = [
        str(term.get("name", ""))
        for group in terms if isinstance(group, list)
        for term in group if isinstance(term, dict) and term.get("taxonomy") == "post_tag"
    ]
    linked_article = acf.get("articolo") or {}
    fact_url = article.get("link", "")
    if isinstance(linked_article, dict) and linked_article.get("post_name"):
        fact_url = f"https://pagellapolitica.it/articoli/{linked_article['post_name']}"
    supporting_html = str(article.get("_supporting_html", ""))
    evidence_urls = _links(_soup(f"<article>{supporting_html}</article>"), str(fact_url))
    return _record(
        source="pagella", source_id=str(article.get("id", "")), claim=str(claim),
        source_label=_pagella_label(article), explanation=explanation,
        image_url=image, fact_check_url=str(fact_url),
        published_at=str(article.get("date", "")), keywords=keywords,
        evidence_urls=evidence_urls, claim_source_url=str(acf.get("link") or ""),
    )
