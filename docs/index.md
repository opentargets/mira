# Mira documentation

<p align="center">
  <img src="../assets/brand/mira-logo.svg" alt="MIRA — Multi-source Indication and Report Analytics" width="560">
</p>

Mira harmonises clinical trials, regulatory records, drug indications, and safety evidence into consistent datasets for drug-discovery analysis.

The documentation is being developed around three questions:

1. What are a Clinical Report and a Clinical Indication?
2. How does Open Targets generate them with Mira's default workflow?
3. How can a user change the YAML configuration for a different use case?

The first complete path will serve an Open Targets colleague. The same concepts and an offline introductory example will provide a friendly entry point for external researchers; Open Targets-only data and access requirements will be identified explicitly.

> [!TIP]
> Start with [How Mira works](concepts.md) for the complete path from provider data to Clinical Reports, mapped entities, and Clinical Indications.

## Data documentation

- [How Mira works](concepts.md)
- [Clinical Report](clinical-report.md)
- [Clinical Indication](clinical-indication.md)
- [Entity mapping](entity-mapping.md)

## Providers

- [AACT](providers/aact.md)
- [ChEMBL](providers/chembl.md)
- [TTD](providers/ttd.md)
- [EMA](providers/ema.md)
- [PMDA](providers/pmda.md)

Each provider page explains what that source contributes and the selection rules applied before its records enter the shared Clinical Report dataset.

## Project documentation

- [Handover and usability checklist](handover-checklist.md)
- [Decision log](decision-log.md)

## Using Mira

- [Generate data with Python](generate-with-python.md)
- [CLI and YAML configuration](cli-and-configuration.md)
- [Data inputs](data-inputs.md)

Start with the Python guide to see the data flow directly. Use the CLI guide for repeatable recipe-driven runs and configuration changes.

## Authoring and publication

Write the source documentation as Markdown files in this directory. This keeps it readable in GitHub, easy to review with code changes, and portable between documentation tools.

The preferred publication direction is MkDocs with the Material theme and, if permitted by the Open Targets GitHub configuration, GitHub Pages. The hosting choice remains open until repository ownership and publication permissions are confirmed. A documentation build should be added before substantial content accumulates so navigation, links, and examples can be checked continuously.
