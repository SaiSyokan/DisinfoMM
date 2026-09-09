# Dataset

## Snapshot

The source snapshot supplied for this release contains 25,752 CSV records:

| Source | Language | Records |
|---|---|---:|
| Snopes | English | 16,730 |
| Polígrafo | Portuguese | 7,270 |
| Pagella Politica | Italian | 1,752 |

This is the approximately 25,000-record dataset described in the paper. The historical experiment export contains 19,887 image–claim entries after the original media-availability and caption-length filters. The exact English and multilingual paper manifests contain 7,052 and 10,368 examples respectively; the paper reports these rounded as 7,000 and 10,000.

## Canonical schema

Each JSONL row contains:

| Field | Meaning |
|---|---|
| `id` | Stable release identifier |
| `source`, `language` | Fact-check source and ISO language code |
| `claim`, `image_url` | Multimodal model input and retrievable media URL |
| `label_source` | Original website-specific verdict |
| `label_five` | Harmonized five-level label |
| `label_binary` | Paper task label: 0 authentic, 1 disinformation |
| `explanation` | Supportive explanation used by the enhanced method |
| `fact_check_url` | Original fact-check article |
| `claim_source_url` | Original declaration/content link when available |
| `evidence_urls`, `evidence_domains` | Cited external sources and normalized domains |
| `published_at`, `collected_at` | Source and collection timestamps |
| `keywords`, `tags` | Source and enrichment metadata |
| `quality_flags` | Missing or unresolved fields requiring review |

Run `disinfomm validate FILE.jsonl` after every conversion or download.

## Media

The materials recovered for this release contain media URLs but no image files: both historical `images/` directories are empty. Consequently, the release is metadata-first and includes a resumable downloader. Downloaded files are accompanied by a SHA-256 index and a failure log. URL availability can change over time.

Paper reproduction requires the images corresponding to the exact manifests. When an original URL is unavailable, recover the media only from an authorized archive or an author-held backup and preserve the manifest ID.

## Rights and responsible use

CC BY 4.0 covers author-created annotations and metadata only. Source article text and media retain third-party rights. The public code repository intentionally excludes images. Consult `DATA_LICENSE.md` and `THIRD_PARTY.md`; do not treat the dataset license as permission to redistribute source media.

The dataset may contain misinformation, references to public controversies, and names of individuals. It is intended for research and evaluation, not as a source of factual claims without the accompanying verdict and provenance.
