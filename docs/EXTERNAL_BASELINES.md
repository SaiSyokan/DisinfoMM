# External evidence-based baseline

The final ICMI paper compares against the method from:

> Sahar Abdelnabi, Rakibul Hasan, and Mario Fritz. “Open-Domain, Content-based, Multi-modal Fact-checking of Out-of-Context Images via Online Resources.” CVPR 2022.

Upstream project: [S-Abdelnabi/OoC-multi-modal-fc](https://github.com/S-Abdelnabi/OoC-multi-modal-fc)

This is a separate comparison method. It searches online resources, gathers textual and visual evidence, computes evidence features, and trains its Consistency-Checking Network. It is not the same as this paper’s `proposed_with_evidence` model, which uses the `Explanation` already present in `Dataset.csv` as a training-only teacher signal.

To reproduce the external comparison:

1. Follow the upstream project’s environment and evidence-collection instructions.
2. Generate the desired balanced DisinfoMM subset with `experiments/prepare_data.py`.
3. Convert the generated records to the upstream query/evidence schema using its documented preparation pipeline.
4. Run online retrieval with your own API credentials and record the retrieval date, because search results change.
5. Train and evaluate in the upstream environment; report overall, authentic, and disinformation accuracy.

The external repository and retrieved evidence are not vendored here. This avoids presenting third-party code, search results, or credentials as part of DisinfoMM and makes the boundary between the paper’s own method and the comparison method explicit.
