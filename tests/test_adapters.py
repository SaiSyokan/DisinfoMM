import json

from disinfomm.collection.adapters import (
    enrich_pagella,
    parse_pagella,
    parse_poligrafo,
    parse_snopes,
)


def test_parse_snopes_jsonld():
    article = {
        "@context": "https://schema.org", "@type": "Article", "description": "A claim",
        "thumbnailUrl": "https://example.org/image.jpg", "datePublished": "2025-01-01",
        "keywords": "one, two",
    }
    review = {
        "@context": "https://schema.org", "@type": "ClaimReview", "claimReviewed": "A claim",
        "reviewRating": {"alternateName": "False"}, "datePublished": "2025-01-01",
    }
    html = f'<html><script type="application/ld+json">{json.dumps(article)}</script><script type="application/ld+json">{json.dumps(review)}</script><article><p>Explanation.</p><a href="https://evidence.example/a">source</a></article></html>'
    row = parse_snopes(html, "https://www.snopes.com/fact-check/example/")
    assert row["label_five"] == "False"
    assert row["label_binary"] == 1
    assert row["evidence_domains"] == ["evidence.example"]


def test_parse_poligrafo_markup():
    html = '<html><meta property="og:image" content="https://example.org/i.jpg"><h1>Uma alegação</h1><div class="fact-check-result"><span>Verdadeiro</span></div><article><p>Explicação.</p></article></html>'
    row = parse_poligrafo(html, "https://poligrafo.sapo.pt/fact-check/example/")
    assert row["language"] == "pt"
    assert row["label_binary"] == 0


def test_parse_pagella_api():
    article = {
        "id": 12, "date": "2025-01-01", "link": "https://backend.example/12",
        "title": {"rendered": "Non è vero"},
        "acf": {"sentenza": "Una dichiarazione", "link": "https://claim.example/", "verdetto": {"testo": "Non è vero", "in_breve": False}},
        "_embedded": {"wp:featuredmedia": [{"source_url": "https://example.org/i.jpg"}], "wp:term": []},
    }
    row = parse_pagella(article)
    assert row["language"] == "it"
    assert row["label_five"] == "False"


def test_pagella_sparse_declaration_uses_linked_article_section():
    article = {
        "id": 12,
        "date": "2026-01-01",
        "title": {"rendered": "Una dichiarazione"},
        "acf": {
            "sentenza": "Il costo è cento euro",
            "link": "https://claim.example/",
            "verdetto": {"testo": "", "in_breve": False},
            "articolo": {"ID": 99, "post_name": "fact-checking-costo"},
        },
        "_embedded": {"wp:term": []},
    }
    linked = {
        "acf": {
            "editor": [
                {
                    "acf_fc_layout": "paragrafo",
                    "titolo": "Il costo",
                    "testo": (
                        "<p>Il costo è cento euro. Il dato è corretto, ma necessita "
                        "di contesto. <a href='https://evidence.example/a'>Fonte</a></p>"
                    ),
                }
            ]
        },
        "_embedded": {
            "wp:featuredmedia": [{"source_url": "https://example.org/i.jpg"}]
        },
    }
    row = parse_pagella(enrich_pagella(article, linked))
    assert row["label_five"] == "Mostly True"
    assert row["image_url"] == "https://example.org/i.jpg"
    assert row["evidence_domains"] == ["evidence.example"]
