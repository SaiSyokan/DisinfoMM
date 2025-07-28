# DisinfoMM

**DisinfoMM** is a multilingual and multimodal dataset for disinformation and out-of-context (OOC) detection, released with our ICMI 2025 paper. The dataset includes fact-checked claims with paired images and multilingual evidence, supporting five-level veracity classification and evidence-aware model training.

📄 **Paper**: [A Multilingual, Multimodal Dataset for Disinformation and Out-of-Context Analysis with Rich Supportive Information (ICMI 2025)](https://doi.org/10.1145/3716553.3750813)

---

## 📦 Dataset Overview

- **Languages**: English, Italian, Portuguese
- **Modalities**: Text (claim), Image
- **Veracity Labels**: `True`, `Mostly True`, `Incomplete`, `Mostly False`, `False`
- **Supportive Information**:
  - Explanation texts
  - Debunking source metadata (verdict, timestamp, keywords, article links)
  - External links and multilingual evidence

---

## 🧪 Tasks Supported

- Multimodal disinformation detection
- Out-of-context image–text analysis
- Evidence-aware veracity classification
- Multilingual generalization benchmarking

---

## 🛠️ Repository Structure

```bash
DisinfoMM/
├── data/                  # (Coming soon) Dataset files, organized by language or split
├── code/                  # (Planned) Baseline models and preprocessing scripts
├── LICENSE
└── README.md
```

## 🚧 Status

This repository is under preparation. The dataset and code will be released soon.

Please ⭐️ star or watch the repo to stay updated.

---

## 📬 Contact

If you have questions or would like early access, feel free to contact:

**Shuhan Cui**  
The University of Tokyo  
📧 syokan [at] g.ecc.u-tokyo.ac.jp
