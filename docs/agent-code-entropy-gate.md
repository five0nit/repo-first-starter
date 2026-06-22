# Agent Code Entropy Gate

Repo-first selection is not complete when the code merely works. Agent-written changes should reduce or preserve future reasoning cost.

## Prime directive

Avoid creating systems that only make sense inside the chat session that produced them.

The codebase must explain itself after the agent, prompt, and conversation history are gone.

## Gate checklist

Before accepting a repo-first implementation, check that the change avoids these failure modes:

| Gate | Avoid | Acceptance question |
|---|---|---|
| Hidden truth | Business rules buried in UI code, magic env vars, undocumented flags, assumptions only in prompts/comments | Can a maintainer find the authoritative rule without archaeology? |
| Duplicate business logic | Multiple definitions/calculations/validation rules across layers | Does each business rule have one clear owner? |
| Pattern drift | New architectural style per feature, random helper/event/repository patterns | Does the change follow the existing system pattern unless there is a documented reason not to? |
| Abstraction without tension | Interfaces with one implementation, factories that never vary, generic frameworks for specific problems | Is the abstraction cheaper than the duplication/volatility it replaces? |
| Indirection chains | Service → Manager → Handler → Processor → Provider → Repository → Utility | Does every layer enforce a boundary, isolate volatility, protect an invariant, simplify testing, or model a real domain concept? |
| Context bombs | 1,000-line files, god services, broad utility modules, unrelated responsibilities | Can a human or agent understand each unit within practical context limits? |
| Clever runtime behavior | `eval`, dynamic imports, monkey patching, reflection-heavy dispatch, runtime codegen, opaque decorator stacks | Is behavior inspectable statically, or is the runtime magic strongly justified? |
| Silent failure | Swallowed exceptions, retries without logging, background jobs with no audit trail, disappearing validation failures | Does every important failure leave evidence? |
| Undebuggable success | Only logging failures, no decision trail for critical workflows | Can the system explain important successes: inputs, rule, rule version, actor/process, downstream action? |
| Temporal coupling | Hidden initialization/order assumptions, tribal deployment sequences, undocumented state transitions | If order matters, is it encoded explicitly? |
| Non-idempotent operations without guards | Retry-unsafe inserts, payments/emails without idempotency keys, rerun-unsafe migrations, destructive ops without dry-run/confirmation | Can retries/reruns avoid corrupting state? |
| Test theatre | Tests that only assert mocks, duplicate implementation, skip edge/failure cases, pass when rule is wrong | Does each meaningful test protect an invariant? |
| Dependency inflation | Packages for one-line utilities, frameworks where libraries/native code suffice | Is each dependency worth its maintenance/security/upgrade risk? |
| Config masquerading as logic | Business branching in unvalidated YAML/JSON/metadata/low-code flows | Is config governed like code: schema, tests, ownership, docs? |
| Premature distribution | Microservices/queues/events/network calls without team/throughput/volatility pressure | Is distribution justified by real boundaries or pressure? |
| Security as a later patch | Missing authz, trusting client validation, logging secrets, broad permissions, unsafe defaults | Is security part of the code shape, not bolted on later? |
| Orphaned code | Dead functions, stale flags, deprecated endpoints with no removal plan, commented-out code | Can stale paths be deleted or clearly scheduled for removal? |
| Local correctness breaking global coherence | Immediate task passes but creates hidden state, pattern drift, weak observability, unclear ownership | Would another agent understand and safely extend this without the original conversation? |

## Final rule

Every AI-generated change should reduce or preserve system entropy.

If a change adds functionality but also adds hidden state, duplicate logic, inconsistent patterns, weak observability, and unclear ownership, it is not complete. It is merely a future incident with syntax highlighting.
