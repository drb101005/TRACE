# IDEA.md — AI-Run Statutory Revenue Audit

## Product concept

A web-based AI-assisted statutory revenue audit workspace for a manufacturing business. It ingests sales and related-party data plus supporting documents, assesses data sufficiency, selects explainable risk-based samples, tests transaction trails, manages findings and human review, and produces audit workpapers.

The goal is to move from “testing a spreadsheet” to “interrogating the transaction trail” while keeping the auditor independent from client business data.

## Users and permissions

1. **Client Employee:** uploads initial files/evidence and submits versioned corrections.
2. **Independent AI Auditor:** read-only business-record access; may run checks and create proposed results in a separate audit store; cannot change client source records or approve its own conclusions.
3. **Human Auditor:** reviews calculations/evidence/findings and approves, rejects, reopens, or requests more evidence. Decisions bind to exact versions.
4. **Platform Administrator:** manages accounts, integrations, settings and health; no implicit authority to alter source records/history or approve conclusions.

All permissions are backend-enforced across HTTP APIs, services and MCP.

## End-to-end workflow

1. Create engagement and reporting period.
2. Upload sales register, related-party master, and any available ledger/lifecycle data and evidence.
3. Preserve original bytes and SHA-256; create separately versioned parsed/normalized artifacts.
4. Extract CSV/XLSX/PDF/image content. Use direct PDF text extraction first and OCR for scanned/image-only content where available; retain provenance and extraction limitations.
5. Validate schema, period coverage, completeness, types, duplicates, totals, cross-file references and extraction confidence.
6. Produce a per-procedure data-sufficiency assessment; block or qualify tests with missing prerequisites.
7. Reconcile the register against available source-of-truth records; every discrepancy is an exception, never silent cleanup.
8. Freeze a versioned population snapshot and fingerprint.
9. Match related parties using effective dates and traceable matching reasons; uncertain matches require review.
10. Select Sales TOD with **hybrid deterministic risk ranking + mandatory coverage + seeded random fill**, target **30** (within approximately 25–35 where feasible).
11. Separately select cut-off items around 31 March: approximately last 10 eligible pre-year-end and first 10–15 post-year-end invoices, subject to availability.
12. Request sample-specific evidence (invoice, e-way bill, LR, dispatch/delivery proof, ledger/tax links, credit notes as relevant).
13. Run deterministic checks and use AI only to interpret/explain supported outputs.
14. Store structured findings, amounts, evidence, limitations and proposed actions.
15. Run compliance/coverage checks against a versioned, approved reference checklist.
16. Generate the Sales Register, Sales TOD, Sales Cut-off TOD, Credit Note TOD, findings memo and tamper-evident audit trail.
17. Human Auditor reviews the exact finding/report versions and approves/rejects/requests evidence.
18. If client data changes after snapshot, create a new version and impact map to affected samples, tests, findings and reports; re-run affected tests and mark previous outputs appropriately.

## MVP

- Engagement and reporting-period management.
- CSV/XLSX sales register and related-party ingestion.
- PDF/image evidence extraction with OCR fallback.
- Immutable originals, hashes, versioned normalized records and provenance.
- Data validation and sufficiency assessment.
- Related-party matching with explainable confidence and review status.
- Hybrid reproducible sample selection and cut-off TOD.
- Evidence upload, status tracking and matching.
- Deterministic audit checks plus AI explanations.
- Compliance coverage matrix with verified reference metadata.
- Findings review and version-bound human approval.
- Six workpaper/report outputs.
- Append-only hash-linked audit events and post-snapshot change impact tracking.
- Four roles with backend-enforced permissions.
- Locally hosted MCP server for an external judge/agent; no code changes needed for read-only evaluation.
- Synthetic demo data with planted anomalies and separate ground-truth manifest.

## Stretch features

- Internal sales lifecycle system of record and double-entry postings.
- Relationship graph/circular-trading indicators.
- Stronger evidence duplicate/authenticity signals.
- Multi-entity, regional-language and on-premise support.
- Optional n8n notifications/reminders; n8n is not core authority.

## Product principles

- Evidence before conclusions.
- Preserve original inputs; no silent cleanup.
- Deterministic arithmetic and reproducible sampling.
- Least privilege and auditor independence.
- Human sign-off for final conclusions.
- Explainable findings linked to source IDs.
- Explicit uncertainty, blocked tests and limitations.
- No claim of complete statutory compliance without qualified human validation.

## Demo narrative

Use synthetic manufacturing records with planted irregularities, e.g. invoice without dispatch evidence, post-year-end credit note, late/undisclosed related party, register/system mismatch and cut-off exception. Demonstrate upload → extraction/validation → sufficiency → reconciliation → snapshot → sampling → evidence → tests → findings/compliance coverage → workpaper export → post-snapshot correction impact → MCP inspection with denied write → Human Auditor decision.
