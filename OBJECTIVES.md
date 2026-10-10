# OBJECTIVES.md — Outcomes and Acceptance Criteria

## Primary objective

Deliver a working, explainable AI-assisted statutory revenue audit prototype that preserves source evidence, enforces auditor independence, supports compliance-procedure coverage, and requires human approval of conclusions.

## Functional acceptance criteria

- [ ] Create engagement, reporting period, and workflow state.
- [ ] Support four separate roles: Client Employee, Independent AI Auditor, Human Auditor, Platform Administrator.
- [ ] Upload CSV/XLSX registers and related-party details; support PDF/image evidence extraction and OCR fallback for scanned content.
- [ ] Preserve uploaded bytes and SHA-256; store extracted/normalized representations separately with provenance and version IDs.
- [ ] Surface invalid/missing columns, missing values, duplicate candidates, date coverage, totals, reconciliation differences, and extraction limitations.
- [ ] Provide `sufficient`, `conditionally_sufficient`, or `insufficient` per procedure, with reasons and blockers.
- [ ] Match related parties with traceable exact/fuzzy candidate reasoning, effective dates where available, and human review for uncertainty.
- [ ] Freeze a population snapshot with source versions, inclusion/exclusion criteria, totals and fingerprint.
- [ ] Select Sales TOD using deterministic risk ranking + mandatory coverage + seeded random fill; default target 30, within 25–35 when feasible.
- [ ] Select cut-off TOD around 31 March using the approximate last-10-before / first-10-to-15-after approach; disclose shortages.
- [ ] Store seed, algorithm/config version, population fingerprint, sample IDs and per-sample reasons.
- [ ] Track evidence requested/uploaded/extracted/matched/mismatched/missing/unreadable/review-required.
- [ ] Produce structured audit test results with status, rule version, calculations, source/evidence IDs and limitations.
- [ ] Include a compliance coverage matrix tied to versioned, approved reference metadata; flag unverified citations and never infer compliance from checklist completion alone.
- [ ] Findings distinguish amount under review, potential/confirmed misstatement, proposed adjustment and approved adjustment; prevent double counting.
- [ ] Human Auditor can approve/reject/reopen/request evidence; each decision binds to exact finding/report version.
- [ ] Independent AI Auditor cannot mutate source business data or approve its own findings.
- [ ] Platform Administrator cannot silently edit source records, rewrite audit history or approve conclusions by default.
- [ ] Client corrections create new versions and map impact to samples/tests/findings/reports; prior results remain available and may be marked superseded.
- [ ] Export Sales Register, Sales TOD, Sales Cut-off TOD, Credit Note TOD, findings memo and tamper-evident audit trail.
- [ ] Run a locally hosted MCP server with typed tools and server-side authorization; judge agent can inspect without code changes.
- [ ] Seed synthetic records and known anomalies; keep ground truth unavailable to the audit agent.
- [ ] Run from a documented local setup; tests cover core workflow and permissions.

## Quality objectives

- **Correctness:** deterministic code owns arithmetic, reconciliation, risk scoring, sampling and defined rules.
- **Traceability:** each result points to source artifacts, records, evidence, checks, agent runs and review events.
- **Security:** server-side least privilege; untrusted-upload handling; secrets in environment.
- **Resilience:** malformed files, OCR failures, unavailable LLM and partial evidence degrade safely.
- **Reproducibility:** same snapshot, seed and algorithm/config versions reproduce samples and calculations.
- **Explainability:** show what was checked, why, the evidence used and limitations.
- **Integrity:** append-only hash-linked events and immutable original uploads.
- **Demo reliability:** synthetic data and deterministic fallback allow a demo without external client systems.

## Explicit non-goals

- Replacing a qualified statutory auditor or issuing an autonomous audit opinion.
- Claiming a document is definitively forged from an LLM/OCR mismatch alone.
- Integrating live ERP/GST systems without suitable APIs, permissions and validation.
- Covering every accounting standard, tax rule or industry case.
- Claiming legal/statutory compliance merely because software checks pass.
- Production-grade multi-tenant deployment during the hackathon.
