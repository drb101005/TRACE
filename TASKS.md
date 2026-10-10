# TASKS.md — Implementation Plan and Definition of Done

Use checkboxes to track progress. The backend is in `backend/` at the project root; the six specification Markdown files remain at the root.

## P0 — foundation and contracts

- [ ] Read `AGENT.md`, `IDEA.md`, `OBJECTIVES.md`, `PS_REFERENCE.md`, `AI_AGENT_DETAILS.md`, and `SYSTEM_PROMPT_BACKEND.md`.
- [ ] Create `backend/` with package configuration, application entry point, `.env.example` at root, README/startup instructions and `.gitignore`.
- [ ] Define schemas for users/roles, engagements, uploads/artifacts, source versions, normalized transactions, evidence, snapshots, samples, checks, findings, approvals, compliance references, agent runs and audit events.
- [ ] Define backend-enforced role/permission matrix for all four roles.
- [ ] Define workflow states and valid transitions.
- [ ] Create synthetic manufacturing dataset and separate ground-truth anomaly manifest.

## P1 — ingestion and validation

- [ ] Implement CSV and XLSX upload, file-type/size validation and safe filenames.
- [ ] Implement text-based PDF extraction and OCR fallback for scanned PDF/images where dependencies are available.
- [ ] Preserve original bytes, SHA-256, upload metadata and source version.
- [ ] Store normalized/extracted data separately with sheet/page/row/cell provenance and OCR/extraction confidence where available.
- [ ] Validate schema, types, dates, period coverage, duplicate candidates, totals, missing fields and cross-file references.
- [ ] Implement per-procedure sufficiency assessment and explicit blockers.
- [ ] Add tests for malformed, empty, oversized, unsupported and partially extractable files.

## P1 — deterministic audit services

- [ ] Implement exact related-party matching, explainable fuzzy candidates and review-required status.
- [ ] Implement versioned risk factors with unknown values distinguished from zero risk.
- [ ] Implement hybrid sampling: risk-ranked selections + mandatory coverage + seeded random fill.
- [ ] Default Sales TOD target = 30; support 25–35 when feasible and report population/coverage shortfalls.
- [ ] Implement cut-off selection: approximate last 10 eligible pre-31 March and first 10–15 eligible post-31 March.
- [ ] Implement reconciliation and transaction-trail checks when required data exists.
- [ ] Implement dispatch/delivery, revenue traceability, tax/document linkage, period-end concentration, discounts, duplicate evidence and post-period credit-note checks.
- [ ] Persist formulas, inputs, rule versions, output statuses, source IDs and limitations.
- [ ] Prevent double counting across finding impact categories.
- [ ] Add tests against planted anomaly expected results.

## P1 — versioning, review, and integrity

- [ ] Freeze population snapshots with source version IDs, inclusion/exclusion rules, totals and fingerprint.
- [ ] Make client corrections append new source versions rather than overwrite originals.
- [ ] Map changed records to affected samples, checks, findings and reports; re-run impacted tests and mark old results superseded where appropriate.
- [ ] Implement append-only hash-linked audit events and chain verification.
- [ ] Implement human decisions bound to exact finding/report versions.
- [ ] Deny AI Auditor self-approval and source-business-data writes.

## P1 — agents and orchestration

- [ ] Implement Data Sufficiency Agent.
- [ ] Implement Sample Review Agent that calls deterministic hybrid sampling.
- [ ] Implement Primary Evaluation Agent using named deterministic checks.
- [ ] Implement Compliance Checker Agent and compliance coverage matrix.
- [ ] Implement Report Brief Agent using persisted structured outputs only.
- [ ] Implement explicit workflow state machine, bounded retries/timeouts, run IDs and failure handling.
- [ ] Provide deterministic fallback if the model API is unavailable.
- [ ] Treat uploaded content/OCR as untrusted data; defend against prompt injection.
- [ ] Persist model/provider and prompt/workflow version when applicable.

## P1 — MCP and authorization

- [ ] Implement locally hosted MCP server with narrow typed tools.
- [ ] Include engagement/status, transaction search/trace, related parties, snapshot, sampling, evidence status, audit test, findings/calculations, workpaper generation, compliance coverage, integrity verification and change-history tools as appropriate.
- [ ] Resolve actor identity from trusted server context; never trust role supplied in tool arguments.
- [ ] Enforce permissions in every tool handler and service.
- [ ] Deny source-data mutation and conclusion approval for AI Auditor.
- [ ] Add tests proving forbidden operations fail and allowed reads succeed.
- [ ] Log tool calls without secrets or full sensitive content.

## P2 — API and reporting

- [ ] Implement health/readiness endpoints and versioned API routes.
- [ ] Implement engagement, uploads, validation, sufficiency, snapshots, sampling, evidence, audit runs, findings, review decisions, compliance, exports and audit-trail APIs.
- [ ] Export Sales Register, Sales TOD, Sales Cut-off TOD, Credit Note TOD, findings memo and tamper-evident audit trail.
- [ ] Render reports from structured persisted records, label draft/final status correctly, and include limitations/version metadata.
- [ ] Implement useful error responses, pagination and request validation.

## P2 — tests and security

- [ ] Unit tests for validation, risk factors, sampling, reconciliation, findings and compliance coverage.
- [ ] API tests for all four roles and cross-engagement access denial.
- [ ] Tests for immutable originals, source versioning, audit hash chain, version-bound approvals and change impact.
- [ ] MCP authorization tests, including denied write/approval attempts.
- [ ] End-to-end test from upload through evidence, findings, human review and export.
- [ ] Ensure no secrets, real client data or ground-truth manifest are exposed in logs/API/model context.

## P3 — demo readiness

- [ ] Seed synthetic data and planted anomalies reproducibly.
- [ ] Provide simple local startup and documented environment variables.
- [ ] Verify end-to-end workflow on the demo machine.
- [ ] Demonstrate post-snapshot correction impact.
- [ ] Demonstrate external MCP read access and denied mutation.
- [ ] Demonstrate Human Auditor approval/rejection on a specific version.
- [ ] Prepare a 3–5 minute demo and explain false positives, limitations and human oversight.

## Release gate

Do not mark a task complete merely because files exist. A feature is complete only when implemented, tested, permission-checked, documented and demonstrated or its limitation is explicitly recorded.
