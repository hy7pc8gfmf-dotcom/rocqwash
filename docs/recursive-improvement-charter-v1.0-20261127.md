# Recursive Improvement Charter

Version 1.0 — 2026-11-27

## Purpose

This charter is the standing instruction for every participant in this
repository, including participants who join later. It records the constraints
and the working method for sustained, self-supporting improvement. It is
written in international English so that any participant can read and apply it
without local knowledge.

This charter follows the public proposal in issue 102. Where this charter and
that proposal differ, the proposal governs.

## 1. Standing constraints

1. Evidence before claims. Every statement about the state of the repository
   is supported by a command result, a stored measurement, or a file path.
2. Tools report; people decide. Automation may prepare items, run checks, and
   report results. Automation may not approve its own work, assign an item to
   itself, or merge a change.
3. Isolated work. Each change is prepared in its own branch from the current
   main line. Uncommitted work in a personal directory is never modified,
   removed, or cleaned by automation.
4. One landing path. Changes reach the main line through a reviewable proposal
   and a passing automated check. No direct write to the main line.
5. Persistence. Operating rules that must outlive one session belong in this
   repository, not only in a local note.

## 2. Toolchain and audit chain

Work is prepared and checked through the repository's own instruments.

- The tool entry point is the unified command interface and the standard
  shell entry. Use the documented invocation for each instrument.
- The audit chain consists of the conformance checks, the document consistency
  check, the count reconciliation, the contribution intake check, and the
  continuous-integration gate. Run the checks relevant to a change before
  proposing it.
- The tool interface exposes these instruments to external participants.
  When a check is invoked through that interface, record the tool name and
  the observed result so another participant can repeat the check.

A participant may not replace a mechanical check with a written assertion.

## 3. Writing standard for all text surfaces

The following surfaces must use international English, standard terminology,
and a consistent form:

- comment text in source files;
- file headers and module descriptions;
- statement headers and proof introductions;
- text inside proofs, including comments and explanatory notes.

The following are excluded from these surfaces:

- local shorthand and project-only jargon;
- engineering slang and colloquial expressions;
- generated wording that adds no information;
- phrases that announce an action without stating its result.

When a term is specific to the project, define it on first use and use one
spelling throughout. When a sentence states an outcome, name the check that
establishes that outcome.

## 4. Work items and iteration

- A work item states its objective, evidence, scope, exclusion, acceptance
  check, direction, and dependencies.
- Iterations are fixed periods with a published plan. Each item has one owner
  and one state.
- A claim is made in public. A participant holds at most two open items.
- A stalled item is returned to the open list after a status request and a
  reply window, both recorded in the item.

## 5. Main line and auxiliary work

Continuous construction of real work items is the primary activity. A periodic
survey of repository state is an auxiliary activity. The survey supports the
main line by finding items; it does not replace work on those items.

The recurring cycle is:

1. detect an improvement opportunity from measured evidence;
2. perform the anchoring ceremony for that generation of work, so the
   reference point is explicit;
3. prepare the smallest change that resolves the opportunity;
4. verify the change through the relevant audit chain;
5. land the change through the single landing path;
6. record the new measurement and return to step 1.

Each completed cycle advances the visible record. This is what makes the
process self-supporting.

## 6. Visibility and continuity

Each landed item records its author, reviewer, acceptance result, and the
measurement that changed. These records are the basis for participation and
for the capability record. They let a new participant see which directions
are open and which checks must pass.

This charter is versioned. A change to these rules requires its own work item
and its own review. Participants who join later read this file before opening
their first item.

## 7. Scope

This charter governs working method and written communication. It does not
grant repository write access, define automatic merging, or override the
continuous-integration gate.
