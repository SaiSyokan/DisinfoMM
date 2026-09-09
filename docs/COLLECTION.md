# Collection and continuous expansion

The paper’s historical pipeline used Scrapy plus source-specific helpers. It crawled Snopes and Polígrafo archive pages, queried Pagella Politica’s WordPress API, extracted article fields, and built three evidence-domain lists:

1. all cited links;
2. domains cited more than 100 times;
3. high-frequency domains cited more than 300 times for extra keyword enrichment.

The release implementation retains the same source coverage and provenance fields but separates extraction from orchestration. It uses structured JSON-LD where available, performs sequential rate-limited requests, appends only unseen fact-check URLs, and never deletes a previous snapshot. This makes update behavior easier to test and audit.

```bash
python -m pip install -e '.[collect]'
export DISINFOMM_CONTACT='mailto:your-address@example.org'
disinfomm collect snopes --output collected/snopes.jsonl --pages 1 --delay 2
```

Run the command separately for `poligrafo` and `pagella`, then validate and review `Unknown` labels. Do not merge a live run directly into an archival paper snapshot.

## Operational rules

- Read and follow each source’s current terms and robots policy.
- Use an identifiable user agent and conservative delay.
- Keep `fact_check_url`, `published_at`, and `collected_at` unchanged.
- Treat parser failures and unknown labels as review items, not negative examples.
- Do not commit downloaded images or raw page archives to GitHub.
- Pin a dated snapshot before an experiment; never train against a moving live file.

Selectors and APIs can change. Offline adapter tests protect the current structured extraction contract, but a live smoke test is still required before a large update.
