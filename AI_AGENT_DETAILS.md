# AI_AGENT_DETAILS.md — Agent Roles, Contracts, and Orchestration

## Core architecture principle

Agents are bounded reasoning and orchestration components around deterministic audit services. They do not independently determine authoritative arithmetic, sample IDs, legal conclusions, or final audit opinions. Persist every run's ID, engagement, actor identity, input artifact/version fingerprints, model/workflow version, tools called, output schema, errors, and timestamps.

## Workflow state machine

`draft → files_received → ingestion_complete → validation_complete → sufficiency_assessed → population_frozen → sampling_complete → evidence_collection → tests_complete → findings_pending_review → human_review → report_generated → approved_final`

States may branch to `blocked`, `needs_more_evidence`, or `superseded`. Enforce valid transitions in backend services. A new client data version after population freeze creates a change event and impact assessment; it must not erase prior states or reports.

## 1. Data Sufficiency Agent

**Purpose:** assess whether each planned procedure can be run on the available data.

- **Inputs:** engagement period/scope, file metadata, parsed schema, validation results, available source-system/lifecycle records, evidence metadata, required inputs per check.
- **Tools:** read schema/validation summaries and engagement configuration; propose missing-information requests.
- **Output:** `sufficient | conditionally_sufficient | insufficient`, per-check readiness, blockers, missing fields/files, requested evidence, limitations and source IDs.
- **Guardrails:** parsing success is not audit sufficiency; numeric validity is deterministic; absent source-of-truth data is a limitation, not presumed agreement.

## 2. Sample Review Agent

**Purpose:** explain and request reproducible sampling; the deterministic sampling service selects the actual records.

- **Inputs:** validated population snapshot, deterministic risk-factor results, related-party matches, configured strata/coverage rules, seed, algorithm version.
- **Tools:** invoke sampling service, read population and sample history, export selected IDs.
- **Output:** sample IDs, transaction IDs, selection reasons, risk factors, strata, seed, algorithm/config version, population fingerprint, coverage summary and shortfalls.
- **Guardrails:** hybrid risk ranking + mandatory coverage + seeded random fill. Default Sales TOD target is 30; respect the approximate 25–35 brief range where feasible. Never select from a truncated population silently or invent IDs. Cut-off selection is separately documented around 31 March.

## 3. Primary Evaluation Agent

**Purpose:** orchestrate permitted deterministic audit tests and summarize their outcomes.

- **Inputs:** scope, sufficiency result, snapshot, samples, transaction/lifecycle/ledger data, evidence links, rule outputs and compliance checklist.
- **Tools:** invoke named deterministic checks; read permitted records/evidence; create proposed findings in the audit-results store.
- **Checks may include, when relevant data exists:** register-to-source reconciliation; invoice-to-order/dispatch/delivery trace; revenue/tax journal linkage; missing physical movement; cut-off; related parties; duplicate/reused documents; discounts/promotions; tax-document mismatches; credit notes after year-end; period-end concentration; source journal without originating sale; post-snapshot changes.
- **Output:** typed check results (`pass`, `exception`, `insufficient_evidence`, `not_applicable`, `needs_review`), rule ID/version, source IDs, calculation references, limitations, proposed findings and unresolved conflicts.
- **Guardrails:** code calculates and compares; LLM explains. Missing evidence is not proof of fraud. Fraud/circular-trading language remains a signal for investigation, not a conclusion.

## 4. Compliance Checker Agent

**Purpose:** track compliance with the configured audit procedure checklist and the completeness of evidence/workpapers.

- Identify applicable, completed, blocked, incomplete, not-applicable and human-review-required procedures.
- Link each checklist item to a controlled reference record: authority/standard, title, version/effective date, clause/paragraph, source URI/document ID, applicability rationale and verification status.
- Identify unsupported conclusions, missing procedures/evidence, limitations, and mismatches between reported conclusions and underlying workpapers.
- Never invent statutory citations, silently apply outdated law, or claim statutory compliance solely because all checklist items show complete.
- Output a compliance coverage matrix and explicit disclaimer/limitations for human auditor review.

## 5. Report Brief Agent

**Purpose:** prepare report narrative and exports from persisted structured results.

- May summarize reviewed findings, risk themes, evidence, impact fields, limitations and follow-up.
- Must not invent findings, figures, legal references, evidence, or approval status.
- Keep draft/pending-review labels until a Human Auditor approves the exact version.
- Reports include scope, method, snapshot/version, sample methodology, procedures performed, exceptions, evidence, impact categories, limitations, proposed adjustments, reviewer decision and audit-trail reference.

## Orchestrator responsibilities

- Validate requested transition and actor permissions.
- Run services in a deterministic, traceable sequence.
- Persist status before/after each stage and log failures.
- Use bounded retries/timeouts for transient model/service errors.
- Make model failure degrade gracefully to deterministic outputs and templates.
- Prevent loops, unbounded tool calls, privilege escalation and arbitrary agent-to-agent tool delegation.
- Never mark blocked/unknown tests as pass.
- Re-run affected procedures after source corrections and mark affected previous outputs `superseded` or `potentially_superseded`, retaining their history.

## Required user-role boundaries

- **Client Employee:** upload originals/evidence and submit corrections as new versions; no approval rights.
- **Independent AI Auditor:** read business data; run allowed checks; create proposed audit results only in a separate store; cannot mutate business records or approve findings.
- **Human Auditor:** review evidence and calculations; approve/reject/request evidence/reopen; decisions bound to exact finding/report version; cannot edit source business data.
- **Platform Administrator:** manage accounts, integrations, settings and service health; no implicit business-data mutation, audit-history rewrite, or audit-conclusion approval rights.

## MCP tool contract

Expose only narrow typed tools, for example:
`get_engagement`, `get_ingestion_status`, `search_transactions`, `get_transaction_trace`, `get_related_parties`, `get_population_snapshot`, `run_sampling`, `get_sampling_results`, `get_evidence_status`, `run_audit_test`, `get_findings`, `get_finding_calculation`, `generate_workpaper`, `verify_audit_integrity`, `get_change_history`, `get_compliance_coverage`.

Every tool must:
- Resolve identity from trusted server context, not user-supplied role strings.
- Check engagement scope and tool-specific permission server-side.
- Validate all arguments and bound result size.
- Log actor/tool/target/time/result status without secrets or full sensitive content.
- Return structured errors and never offer arbitrary SQL, shell, filesystem paths, or code execution.
- Deny AI Auditor attempts to mutate source business data or approve findings.

## Shared finding schema

At minimum: finding ID/version, engagement ID, snapshot ID, rule ID/version, affected transaction/sample IDs, evidence/source IDs, expected vs observed, rationale, severity, uncertainty, status, amount-under-review, potential-misstatement amount, confirmed-misstatement amount, proposed adjustment, approved adjustment, currency, no-double-count grouping key, created-by/run ID, human decision/version, limitations, timestamps.

## Audit event schema

At minimum: event ID, UTC timestamp, actor ID/role, engagement ID, action, target type/ID/version, input fingerprint, result fingerprint, previous event hash, event hash, correlation/run ID. Verify the chain; do not imply hashing alone authenticates actors.
