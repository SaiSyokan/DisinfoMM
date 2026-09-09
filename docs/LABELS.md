# Label harmonization

DisinfoMM preserves each website verdict in `label_source` and maps it to one of five shared labels: `True`, `Mostly True`, `Incomplete`, `Mostly False`, and `False`. Unresolved live records are emitted as `Unknown` and must be reviewed before binary training.

The source-specific mappings are encoded in `src/disinfomm/labels.py`. They include the mappings used by the historical collector, including Snopes-specific categories and the Portuguese Polígrafo labels. Historical spelling variants such as `Moslty false or misleading` are normalized without changing the underlying category.

For new binary manifests, `True` and `Mostly True` map to authentic (`0`); `Incomplete`, `Mostly False`, and `False` map to disinformation (`1`). The exact paper manifests preserve their stored historical `falsified` value and are authoritative for reproducing the reported experiments. This distinction matters because the old preparation script compared `Mostly true` case-sensitively and therefore did not treat every capitalization variant identically.

Pagella Politica did not expose a consistent structured verdict for every entry. The historical pipeline used translated keyword rules followed by DistilBERT sentiment thresholds. Live collection now prefers deterministic Italian keyword rules and marks ambiguous records `Unknown`, because automatic sentiment-based guessing is difficult to audit and can change with translator/model versions.
