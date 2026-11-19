# Engineering principles — source-to-rule traceability

This document **adapts ideas** from Steve McConnell, *Code Complete, 2nd Edition* and its supplementary checklists. It does not reproduce book chapters. The 2004 content is a conceptual basis, **not a current security or framework standard**.

| Source chapter | Engineering principle | Operational rule for Codex | Verification evidence |
|---|---|---|---|
| Ch.3/4 checklists | Prerequisites and construction choices | Define acceptance criteria, risk, environment, architecture and build/test tools before material changes | Requirement→test trace and commands |
| Ch.5 full excerpt | Manage complexity, information hiding | Split by cohesive responsibilities; hide volatile data formats, business rules and external integrations behind limited interfaces | Module boundary audit, dependency graph |
| Ch.6 full excerpt | Effective abstractions and encapsulation | Prefer a consistent public interface with minimal leakage; avoid needless inheritance and anemic wrappers | API review + affected callers |
| Ch.7 checklist | High-quality routines | One clear responsibility; naming matches behavior; stable input/output contract and understandable parameters | Method-level review, direct tests |
| Ch.8 checklist | Defensive programming | Validate at trust boundaries, define exceptions/error results, avoid swallowing failures; balance robustness with correct behavior | Malformed-input and failure-path tests |
| Ch.9 full excerpt | Pseudocode programming process | For nontrivial algorithms sketch steps first; revise design before translating to code | Design note and edge-case test |
| Ch.10–13 checklists | Variables and data representation | Small scopes, initialized values, domain names, appropriate numeric types and safe ranges | Compiler/typechecker & boundary tests |
| Ch.14–19 excerpt | Control flow and table-driven methods | Make normal path obvious; simplify nesting; use decision tables where business conditions warrant | Truth table and case coverage |
| Ch.20 checklist | Software quality | Set explicit quality attributes and measurable release criteria | Quality gate results |
| Ch.21 checklist | Collaborative construction | Check proposed changes independently, focusing on defects with evidence | Recorded review findings |
| Ch.22 checklist | Developer testing | Cover requirements, boundaries, invalid values and regression paths | Executed tests / failure logs |
| Ch.23 checklist | Debugging | Reproduce → form hypothesis → isolate → fix root cause → verify | Minimal reproducer & regression test |
| Ch.24 full excerpt | Safe refactoring | Save a versioned baseline; small behavior-preserving steps and test after each | Focused commits and passing tests |
| Ch.25/26 full excerpt | Performance tuning | Profile before optimizing; prove benefit and verify correctness | Before/after benchmark |
| Ch.27/28 excerpt | Scale and construction management | Right-size architectural rigor, configuration and integration strategy to project risk | Dependency and change review |
| Ch.29 checklist | Integration | Incremental integration, frequent build and smoke tests | CI run / integration test |
| Ch.31/32 checklists | Readable layout and self-documenting code | Name by intent, format consistently, explain **why** in non-obvious comments | Lint/style and reader walkthrough |

## Trade-offs

- Simple solutions are preferable **when they meet actual requirements**. Do not confuse simplicity with ignoring essential edge cases.
- Loose coupling is valuable, but moving every function into its own layer raises accidental complexity.
- Not every parameter or function-size heuristic is a hard limit; defend exceptions with readability and tests.
- Refactoring must not be mixed indiscriminately with behavior changes; keep rollback straightforward.
- Do not measure engineering quality by code volume, test counts alone, or a single arbitrary coverage threshold.

## Source links

- Steve McConnell, *Code Complete, 2nd Ed.*, Microsoft Press: https://www.microsoftpressstore.com/store/code-complete-9780735691254
- Supplementary checklists: https://www.matthewjmiller.net/files/cc2e_checklists.pdf
- OpenAI Skills design: https://developers.openai.com/api/docs/guides/tools-skills
- OpenAI skill evals: https://developers.openai.com/blog/eval-skills
- GitHub Actions security: https://docs.github.com/en/actions/reference/security/secure-use
