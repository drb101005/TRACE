# PS_REFERENCE.md — Problem Statement Reference

> Working summary of the supplied *Elevate 1.0 — Hackathon Problem Statements*, Problem Statement 04, pages 8–10. This is a project reference summary, not a substitute for the official brief. Verify wording and exact template layouts against the source PDF.

## Core problem

A mid-size manufacturer may record approximately 6,000–8,000 sales annually while statutory testing examines a limited sample. Spreadsheet-only testing and manual evidence collection can miss fictitious invoices, circular trading, period-end revenue manipulation, undisclosed related parties and post-year-end reversals.

## Core requirements represented in this project

1. Client uploads sales ledger/register and related-party details.
2. Preserve client-provided data exactly; never silently clean or overwrite the source.
3. Match customers to related-party details with traceable reasoning.
4. Select approximately 25–35 Sales TOD samples with risk and coverage across customers, high-value items, and related/non-related parties.
5. Select cut-off items around 31 March: approximately last 10 before year-end and first 10–15 after.
6. Request supporting evidence such as invoices, e-way bills and lorry receipts (LR).
7. Test the underlying transaction trail, not just the exported register.
8. Produce Sales Register, Sales TOD, Sales Cut-off TOD, Credit Note TOD, findings memo with impact/proposed adjustments, and tamper-evident audit trail.
9. Ground procedures in applicable Standards on Auditing, accounting requirements and indirect-tax requirements; a qualified human auditor validates conclusions.

## Beyond-core capabilities and judging signals

- Commercial lifecycle/system of record spanning customer interaction, commitment/pricing, physical movement, revenue/tax recognition, settlement and promotions.
- Double-entry ledger with controls against silent alteration.
- Locally hosted MCP server for external agent access.
- Identity-based permissions: client can perform permitted client actions; independent auditor can inspect but cannot change business data.
- Detect post-testing client changes and map their impact to selected samples and outputs.
- Every discrepancy between exported register and available system of record is a finding/exception, not a cleaning task.
- Investigate late/undisclosed related parties, shared identifiers, sales without physical movement, unusual period-end concentration, discounts, tax-document mismatches, journals not originating from sales, evidence mismatches and post-period credit notes.
- Reproducible, explainable sampling and an engagement-ready workpaper.
- Judges can use their own agent without requiring code changes.

## Project decisions layered on top of the brief

- Default Sales TOD target is **30**, using hybrid deterministic risk ranking, mandatory coverage rules and seeded random fill. This implements the brief's approximate 25–35 range; it does not replace it.
- Four logins: Client Employee, Independent AI Auditor, Human Auditor, Platform Administrator.
- Synthetic manufacturing data with planted anomalies; ground-truth manifest is kept separate from agent inputs.
- PDF text extraction plus OCR fallback is included in ingestion design.
- Compliance coverage is tracked against configured, versioned references; references must not be invented and legal interpretations require human review.
- Human approval is required for final conclusions, and decisions are bound to exact versions.
- n8n is optional; MCP is a required project capability.

## Compliance interpretation safeguard

This project can report procedure coverage and reference mappings. It must not claim complete statutory compliance merely because a checklist is complete. Applicable requirements and citations must be sourced, versioned, checked for period applicability and reviewed by a qualified auditor.

## Core design question

How much of a real statutory revenue audit can an AI agent run end to end against a business it cannot alter and evidence it cannot blindly trust, while producing workpapers a qualified auditor can review and sign?
