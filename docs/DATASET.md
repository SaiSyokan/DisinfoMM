# Dataset

## Snapshot

The source snapshot supplied for this release contains 25,752 CSV records:

| Source | Language | Records |
|---|---|---:|
| Snopes | English | 16,730 |
| Polígrafo | Portuguese | 7,270 |
| Pagella Politica | Italian | 1,752 |

This is the approximately 25,000-record dataset described in the paper. The historical experiment export contains 19,887 image–claim entries after the original media-availability and caption-length filters. The exact English and multilingual paper manifests contain 7,052 and 10,368 examples respectively; the paper reports these rounded as 7,000 and 10,000.

## Canonical release schema

`Dataset.csv` is the canonical release. Its 14 columns are:

| Field | Meaning |
|---|---|
| `Num` | Unique historical record identifier |
| `Website`, `Date` | Fact-checking source and source publication date |
| `Image`, `Claim` | Source image URL and assessed claim |
| `Evaluation` | Harmonized five-level evaluation |
| `Label` | Original source-specific verdict |
| `Keywords`, `Tags` | Source and evidence enrichment metadata |
| `Article Link` | Fact-checking article URL |
| `Declaration Link` | Original statement/content URL when available |
| `Explanation` | Supportive explanation used by the enhanced method |
| `Article sources` | Cited evidence URLs |
| `Process` | Evidence domains retained by the frequency filter |

Experiment JSONL is a generated convenience format, not a second dataset. Run `disinfomm prepare-experiments Dataset.csv OUTPUT ...` to create it together with an audit file.

## Media

The materials recovered for this release contain media URLs but no complete image collection: both supplied historical `images/` directories are empty. Consequently, the release contains the original CSV and a resumable downloader. Downloaded files are accompanied by a SHA-256 index and a failure log. URL availability can change over time.

Paper reproduction requires the images corresponding to the selected manifests. When an original URL is unavailable, recover the media only from an authorized archive or an author-held backup and preserve the record ID.

## Rights and responsible use

CC BY 4.0 covers author-created annotations and metadata only. Source article text and media retain third-party rights. The public code repository intentionally excludes images. Consult `DATA_LICENSE.md` and `THIRD_PARTY.md`; do not treat the dataset license as permission to redistribute source media.

The dataset may contain misinformation, references to public controversies, and names of individuals. It is intended for research and evaluation, not as a source of factual claims without the accompanying verdict and provenance.
