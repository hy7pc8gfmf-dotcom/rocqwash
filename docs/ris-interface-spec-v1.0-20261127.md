# Recursive Improvement System Interface Specification, version 1.0.

> **RISInterfaceSpecification**: the public contract that lets any participant
> read repository state and contribute to recursive improvement without
> private knowledge.
>
> Purpose.  Define the read surface, claim surface, tool surface, work-item
>   parameters, cycle parameters, layer boundary, writing parameter, and stop
>   parameters of the recursive improvement system, so that an idle-time
>   driver on any platform can implement participation from this document
>   alone.
>
> Interface.  Governs the public participation surface: the issue tracker, the
>   pull-request list, the repository documents, the rocqwash tool interface,
>   and version-controlled records. Command faces are cited from
>   `tools/count_guard.py` and `tools/contrib_intake.py`.
>
> Dependencies.  `docs/recursive-improvement-charter-v1.0-20261127.md`,
>   `docs/recursive-evolution-whitepaper-v1.0-20261121.md`, and the current
>   public improvement proposal in the cloud issue tracker.
>
> Evidence.  The registered names in `tools/mcp_server.py` and the documented
>   invocations in the two shell-fallback tools. Findings are cited from the
>   text-standard checks on this file.
>
> Exit-codes.  This document is a contract face and defines no process exit
>   code. Commands it cites keep the exit codes declared by their owning
>   tools.
>
> ## Purpose

This document defines the interface through which an external participant
reads the state of this repository and contributes to its recursive
improvement. It is the contract that an idle-time driver consumes. It is
written in international English so that any participant can implement it
without private knowledge.

This specification follows the standing charter and the recursive-evolution
whitepaper. Where those documents and this specification differ, the charter
governs the rules and the whitepaper governs the method.

## 1. Interface principle

There is no privileged application interface for recursive improvement. The
interface is the public surface of the repository:

- the cloud issue tracker for proposals, claims, and decisions;
- the cloud pull-request list for active claims and review state;
- the repository documents for rules, measurements, and method;
- the rocqwash tool interface for toolchain and audit checks;
- the version-controlled files for all persistent records.

An external participant needs only the ordinary right to read the repository
and to open a pull request. No special token, private endpoint, or local file
is part of this interface.

## 2. Read surface

A driver reads the following before choosing any work item.

| Source | Content | Use |
|---|---|---|
| Standing charter in `docs/` | Constraints, writing standard, cycle | Rules that govern all work |
| Recursive-evolution whitepaper in `docs/` | Layer law, parallel-safety rules, queue format | Method and next-round candidates |
| This specification | Interface and parameters | How to read, claim, and verify |
| Current public improvement proposal | Roles, work-item fields, review rules | Participation process |
| Contribution isolation protocol in `docs/` | Lane isolation | Scope for outside contributors |
| Feedback-loop and scheduling documents in `docs/` | Derived items and measurements | Current state of improvement |
| Open issues and pull requests in the cloud tracker | Active claims and decisions | Collision avoidance |
| Recent commit history | Landed changes and their authors | Visibility and continuity |

All reads are taken from the cloud repository. A local copy that may be stale
is not a valid source. If a source changes during a run, the driver re-reads
it before continuing.

## 3. Claim surface

A claim is published as a pull-request title in this exact form:

```
[actor] subject date
```

| Field | Rule |
|---|---|
| actor | The participant account, exactly as it appears on the pull request |
| subject | A short description of the work item, unique among active claims |
| date | The calendar date in `YYYY-MM-DD` form |

Rules:

1. A title collision stops the work. The participant chooses another subject
   or waits for the active claim to close.
2. A claim reserves a subject and its file domain, not a permanent ownership.
3. A claim must name one direction. A direction is unavailable while another
   active claim names it.
4. A claim is released when its pull request closes or is parked.
5. No file-domain reservation exists inside an idle-task template. Reservations
   exist only in the cloud claim record.

## 4. Tool surface

The rocqwash tool interface is the preferred way to reach the toolchain and
the audit chain. Use the name registered in that interface. Do not guess a
tool name.

Registered faces relevant to this interface include: document consistency,
text style, text-standard detection, internationalisation verification,
capability measurement, axiom audit, tree audit, statement probe, kernel
verification, gate-four comment guard, and anchor guard.

Two checks have no registered interface at this revision:

| Check | Invocation |
|---|---|
| Count reconciliation | `python3 -I tools/count_guard.py --repo DIR` |
| Contribution intake | `python3 -I tools/contrib_intake.py --contrib-repo PATH --contrib-ref REF --base-repo PATH` |

A driver that uses the shell fallback records the reason "no registered
interface for this check" in the work item.

## 5. Work-item parameter set

A work item is valid only when all seven parameters are present:

| Parameter | Content |
|---|---|
| objective | One measurable outcome |
| evidence | Path or command that shows the need |
| scope | Files and directories the change may touch |
| exclusion | Files and directories the change must not touch |
| acceptance | Check that must pass for completion |
| direction | Area of the repository the item advances |
| dependencies | Items that must be completed first |

An item lacking evidence or an acceptance check is a question for the
proposal, not a work item.

## 6. Cycle parameter set

Each cycle records six parameters in the participant ledger:

| Parameter | Content |
|---|---|
| detect | Evidence path and objective of the item |
| ceremony | Main-line commit, capability readings, direction |
| construct | Clean worktree, change inside claimed scope |
| verify | Tool names, invocations, observed results |
| land | Pull-request number, title, acceptance result |
| record | Decision, main-line commit, measurement that changed |

The ledger is a local record kept by the participant. The public record is the
pull request and the repository documents.

## 7. Layer boundary

| Layer | Automatic action allowed |
|---|---|
| Data tier, ledger appends and readings | Yes, with retry and deduplication |
| Code tier, a proposed change | Prepare only; review and gate decide |
| Constitution tier, charter, whitepaper, this specification | No; separate item and human review |

A driver never weakens a check, approves its own change, assigns an item to
itself, or merges its own pull request.

## 8. Writing parameter

Every text surface added or changed must use international English and
standard terminology: comment text, file headers, statement headers, proof
introductions, and text inside proofs. Local shorthand, engineering slang,
colloquial wording, and generated phrasing that adds no information are
excluded. A project-specific term is defined on first use and spelled
consistently. An outcome statement names the check that establishes it.

## 9. Stop and report parameters

A run stops when the agreed duration elapses, two derivation rounds produce no
evidenced item and two auxiliary surveys are clean, three consecutive items
are parked, a claim collision cannot be resolved, or a governing document
changes in a way that invalidates the driver.

The closing report states start and end time, one line per item with its pull
request number and decision, the ledger path, incomplete items and reasons,
derived items, final capability readings, and any surface not verified.

## 10. Version and change control

This specification is versioned. A change requires its own work item, review,
and a version increment. A driver reads the current version from the cloud
repository at run time and does not embed a copy of this specification.
