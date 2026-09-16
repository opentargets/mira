# Mira documentation

<p align="center">
  <img src="assets/brand/mira-logo.svg" alt="MIRA — Multi-source Indication and Report Analytics" width="560">
</p>

> Open Targets Mira (Multi-source Indication and Report Analytics) harmonises clinical trials, regulatory records, drug indications, and safety evidence into consistent datasets for drug-discovery analysis.

The documentation is being developed around three questions:

1. What are a Clinical Report and a Clinical Indication?
2. How does Open Targets generate them with Mira's default workflow?
3. How can a user change the YAML configuration for a different use case?

> [!TIP]
> Start with [How Mira works](concepts.md) for the complete path from provider data to Clinical Reports, mapped entities, and Clinical Indications.

## :lucide-database: Data documentation

<div class="grid cards" markdown>

-   :lucide-book-open:{ .lg .middle } __How Mira works__

    ---

    Follow the complete path from provider data to mapped Clinical Reports and Clinical Indications.

    [:lucide-arrow-right: Read the overview](concepts.md)

-   :lucide-file-text:{ .lg .middle } __Clinical Report__

    ---

    Understand one traceable evidence record, its clinical stage, source, provider, and core fields.

    [:lucide-arrow-right: Explore Clinical Reports](clinical-report.md)

-   :lucide-layers:{ .lg .middle } __Clinical Indication__

    ---

    See how Mira groups reports into drug–disease relationships and derives their maximum clinical stage.

    [:lucide-arrow-right: Explore Clinical Indications](clinical-indication.md)

-   :lucide-link:{ .lg .middle } __Entity mapping__

    ---

    Learn how source labels become ChEMBL and EFO identifiers, including the NER fallback paths.

    [:lucide-arrow-right: Follow entity mapping](entity-mapping.md)

</div>

## :lucide-network: Providers

- [AACT](providers/aact.md)
- [ChEMBL](providers/chembl.md)
- [TTD](providers/ttd.md)
- [EMA](providers/ema.md)
- [PMDA](providers/pmda.md)

Each provider page explains what that source contributes and the selection rules applied before its records enter the shared Clinical Report dataset.

## :lucide-terminal: Using Mira

<div class="grid cards" markdown>

-   :lucide-braces:{ .lg .middle } __Generate with Python__

    ---

    Call provider, mapping, and aggregation functions directly to make the data flow visible.

    [:lucide-arrow-right: Use the Python API](generate-with-python.md)

-   :lucide-terminal:{ .lg .middle } __Run recipes__

    ---

    Use the CLI and YAML recipes for repeatable runs and deployment-specific configuration.

    [:lucide-arrow-right: Configure the CLI](cli-and-configuration.md)

-   :lucide-database:{ .lg .middle } __Prepare the inputs__

    ---

    Find the upstream releases, database tables, file formats, and expected local layout.

    [:lucide-arrow-right: Review data inputs](data-inputs.md)

</div>
