# Recursive Improvement System Whitepaper Supplement, version 1.0.

> **RISWhitepaperSupplement**: the participation layer of recursive evolution,
> connecting the base whitepaper to an open, cloud-driven process.
>
> Purpose.  Define how an external participant joins recursive evolution
> through the public repository surface: the claim mechanism, the mapping of
> the five parallel-safety rules, the cycle and recursion, text as an interface,
> visibility, and the scope limit.
>
> Interface.  Governs the participation face documented in
>   `docs/ris-interface-spec-v1.0-20261127.md` and parameterised in
>   `docs/ris-interface-parameters-v1.0-20261127.json`.
>
> Dependencies.  `docs/recursive-evolution-whitepaper-v1.0-20261121.md` supplies
>   the layer law, the seven laws, the seven pillars, and the recursive-output
>   format. `docs/recursive-improvement-charter-v1.0-20261127.md` supplies the
>   standing rules.
>
> Evidence.  The five parallel-safety rules in section 3 of the base whitepaper
>   and the six-step cycle in the standing charter. Findings are cited from the
>   text-standard checks on this file.
>
> Exit-codes.  This document is a method face and defines no process exit code.
>
> ## Purpose

This supplement connects the existing recursive-evolution whitepaper to the
public participation process. The base whitepaper defines recursive evolution
inside one working group. This supplement defines how an external participant
joins that evolution through the cloud repository, without private knowledge
and without a dedicated private channel.

The base whitepaper remains authoritative for the layer law, the seven laws,
the seven pillars, and the recursive-output format. This supplement adds the
participation surface only.

## 1. Definition

Recursive improvement is a cycle in which the repository produces its own next
work items from measured evidence, and any participant may carry one item from
detection to a recorded result. The cycle is self-supporting because each
landed item changes a measurement that becomes evidence for the next item.

The system has three necessary conditions:

1. a public, versioned rule set that outlives one session;
2. a claim mechanism that prevents two participants from doing the same item;
3. an audit chain that decides results independently of the participant.

## 2. Public surface

The system uses the ordinary public surface of the repository. There is no
private application interface for participation.

| Surface | Role |
|---|---|
| Issue tracker | Proposal, claims, decisions, questions |
| Pull-request list | Active claims, review state, landed changes |
| Repository documents | Rules, method, measurements |
| rocqwash tool interface | Toolchain and audit checks |
| Version control | Persistent records and continuity |

The interface specification and its parameter file define how these surfaces
are read and written. See `ris-interface-spec-v1.0-20261127.md` and
`ris-interface-parameters-v1.0-20261127.json`.

## 3. Relation to the base whitepaper

The base whitepaper states five parallel-safety rules. This supplement maps
them to the public surface:

| Base rule | Public implementation |
|---|---|
| Ledger append retry loop | Participant ledger uses read head, replay, re-read on failure |
| Deduplication by actor and fingerprint | Item record carries actor and semantic fingerprint |
| Separate plan state per executor | Each participant keeps a private plan-state file |
| PR title as claim | `[actor] subject date`; title collision stops work |
| Canonical-only tier | Constitution-tier changes are never automatic |

The three-tier layer law is unchanged. Data-tier appends may be automatic with
retry. Code-tier changes are prepared and then decided by review and gate.
The constitution tier is never changed automatically.

## 4. Claim as coordination

Coordination is achieved through the claim title, not through a task list
embedded in an idle-time template. A participant reads active claims from the
cloud pull-request list, publishes a claim in the prescribed form, and stops
if the title collides.

This design has two consequences:

1. A template can be identical for every participant. It carries protocol,
   never a reserved direction.
2. A direction is reserved only while its claim is active. When the claim
   closes, the direction becomes available again.

## 5. Cycle and recursion

Each cycle has six steps: detect, ceremony, construct, verify, land, record.
The ceremony step records the main-line commit and the capability readings so
that the beginning of the cycle is reproducible. The record step produces the
next candidate in the format defined by section 6 of the base whitepaper.

A run ends when the agreed duration elapses or a stop condition holds. An
auxiliary survey is permitted only while no claimed item is in progress. It
finds items; it does not replace work on a claimed item.

## 6. Writing as an interface

Text is part of the interface. A participant who writes an unreadable item
produces an item that cannot be reviewed. Therefore all participant-facing
text uses international English and standard terminology across comments,
file headers, statement headers, proof introductions, and text inside proofs.
Local shorthand, engineering slang, colloquial wording, and generated
informationless phrasing are excluded. This rule is a contract, not a style
preference.

## 7. Visibility and incentive

Each landed item changes a recorded measurement and names its author and
reviewers. A parked item keeps its reason. These records give participants a
visible reason to continue: progress is attributed, open directions are
visible, and earlier attempts are not repeated.

## 8. Scope limit

This supplement does not grant write access, define automatic merging, or
override the continuous-integration gate. It does not create a private channel
outside the repository. It adds no task list; every item is derived from the
cloud state at run time.

## 9. Change control

This supplement is versioned. A change requires a work item and review. The
interface specification and parameter file are changed under the same rule.
A driver reads the current versions from the cloud repository at run time.
