# Two-pass code review and quality gates

## Pass A — behavior and safety

Check requested behavior, before/after contract, bad input, auth/authorization, secret exposure, file operations, concurrency, race/transaction boundaries, public API breakage, migrations and rollback. Use actual source references and real failure paths, not generic warnings.

## Pass B — maintainability

Check abstraction coherence, coupling, data flow, duplication, comprehensible names, error semantics, tests and observable metrics. Prefer changes that reduce maintenance cost **without introducing new behavior**. Check that the patch changes only justified files.

## Severity levels

- **P0 Blocker**: active credential leakage, irreversible data loss, bypass of a security boundary, dangerous unintended execution.
- **P1 High**: reproducible functional regression, unsafe error handling on critical paths, likely integrity failure.
- **P2 Medium**: meaningful maintainability or reliability flaw, missing critical edge-case test, unjustified coupling.
- **P3 Low**: small clarity and style improvement, no urgent correctness impact.

A finding must include `file:line`, failure scenario, impact, and a recommended bounded fix. If uncertain, mark **hypothesis, not verified**.

## Finish report template

```text
Change: <what, why, constraints>
Scope: <files, modules, API/schema changes>
Verification:
  PASS: <actual command + observed result>
  FAIL: <actual command + failure evidence>
  NOT RUN: <reason; do not imply success>
Findings: [P0/P1/P2/P3, location, evidence, fix] or "No confirmed findings under checks performed"
Residual risks: <unknowns / omitted checks>
Approval needed: <external side effect / high-risk change / none>
```

## Quality gates

- G0: explicit user acceptance criteria; no violation of hard security/data constraints.
- G1: code compiles/type-checks when applicable; affected unit tests pass.
- G2: regression cases cover real edge conditions; integration/smoke tests as needed.
- G3: pass A/B review; no unaddressed P0/P1; document P2 exceptions.
- G4: change log/release/rollback plan for API/schema/operational changes.

Do not suppress test failures or fabricate their resolution. If a check cannot run, mark it `NOT RUN`.
