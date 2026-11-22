# S07_projection_reanchor_E5.md: recipe face: statement-surface projection re-anchoring, recipe E5 (the magic-zero recipe for the six-piece batch) · original title: `处方件 — S07 投影重锚（E5·magic 六件判例文档化）`

> Purpose.  Recipe E5 cures the false-carrier defect: when a `Class` field projection carries a statement surface, extraction floods the extracted face with `Obj.magic`. The treatment re-anchors the statement-surface relation names (`req` / `lt` / `le`) onto their concrete `Real -> Real -> Set` definitions (`real_eq` / `real_lt` / `real_le`) through three exact-string mappings, changing zero proof-body characters and zero comment lines. Scope: statement faces (signatures and assert type faces) of the six-piece batch; the `Class` field definitions in `S07_RealSetoidExpLog.v` are read-only and untouched.
>
> Interface.  Document face only; no runtime interface. The three mappings are expressible as exact-string ledger entries for `wash/wash_engine.py` (`{"tag":"req2real_eq","old":"req ","new":"real_eq ","expect":N}`); the pre-compile world assertion rides `wash/world_hook.py` (`--world <dir> --manifest <certified-generation-account>`); close-out verification rides `verify/verify_gate6.py` and `wrapper/gate7_probe.sh`; piece selection rides `tools/select_audit.py`. The original Chinese text is preserved in the sibling `.zh.md` archive.
>
> Dependencies.  Read-only precedent sources, verified present in the tree at documentation time: `sandbox/seat_reanchor/账/迁移账-六件重锚.md`, the `sandbox/seat_magic6/` ledger, and `seat_reanchor/账/重锚diff-96行.patch`; the concrete-face entities live in `S02_CauchyComplete.v` and the `Class` in `S07_RealSetoidExpLog.v`.
>
> Evidence.  This recipe face was documented November 1, 2026, in `recipes/`, as the fourth piece polished by the five-lesson feedback round. The UpReqSampling case, measured October 31, 2026, carries the four acceptance checks recorded in section 2: first compile rc=0 (vo md5 `10d393bd3bc3641f1aa7e4fbf91be4e6`, 50826B); `gate7` extraction probe magic=0 against baseline 293 (51 names, missing=0); `mac_stmt_names` statement-name census ordered-equal at 51=51 (67=67 with `Let`); `gate4` + CJK + admission-form checks all passing. The case record holds every command the re-anchoring agent ran, with the json/log records in the migration account.
>
> Exit-codes.  Not applicable to a document face; the referenced tools keep their implemented exit-code semantics unchanged.

## 0. At a glance

| item | value |
|---|---|
| recipe number | **E5** (statement-surface projection re-anchor; the magic-zero recipe) |
| defect name | a `Class` field projection carries the statement surface → the extracted face floods with `Obj.magic` (the false-carrier defect) |
| case piece | UpReqSampling.v (one of the six-piece batch; baseline magic=**293** → **0** after re-anchoring) |
| six-piece batch | UpAblMetaWorld3 / UpDebtSqrtAbsReq / UpEntropyGainReq / UpFirewallReq / UpReqTempEntropy / UpReqSampling (leaf pieces newly registered under `M34`; shared `work` world, same-address record) |
| invariants | statement surfaces (signatures + assert type faces) re-anchor onto the concrete faces; proof-body tactics/terms change by **zero characters**; comments **untouched** |

## 1. The defect (root-cause chain, transcribed from the case record)

1. **The three relation fields of the `Class` carry `Set`-valued ranges**: `Class RealInterfaceEnhancedSetoid`
   (`S07_RealSetoidExpLog.v:8075`) declares fields `req / lt / le : Real -> Real -> Set`.
   After extraction the fields collapse to `type req = __` (an empty type that cannot be matched on).
2. **Instance bindings are concrete**: `RealEnhancedReal` (`S07_RealSetoidExpLog.v:8740`) binds
   `req:=real_eq` / `lt:=real_lt` / `le:=real_le`.
3. **Statement surfaces write bare projection names**: the pieces' statement faces are written entirely
   over field projections (bare names after `Import RealInterfaceEnhancedMod`
   plus `Notation R := Real`, with no `Let` anchor), while the proof bodies and the dependency chain
   (UpReqAlgebra/UpReqDist/S02) all go through the concrete faces; crossing the two representation
   systems is what yields `Obj.magic`.
   Measured: before re-anchoring the CI probe read magic=293 (recorded in the `sandbox/seat_magic6/`
   ledger, section 1, row P1).
4. **Healthy in-tree precedent** (same defect, already cured): the in-tree `UpReqAlgebra.v`
   (`req_plus_zero_r : forall a : R, real_eq (plus a zero) a`, source near line 48) keeps the same
   `Import` plus `Notation R := Real` plus bare plus/mult field names and uses concrete names
   **only on the relation faces**; in-tree magic=0.

## 2. The recipe (E5 three mappings: statement surfaces re-anchor onto the concrete faces)

Concrete-face entities (all in `S02_CauchyComplete.v`, all `Real -> Real -> Set`):

| projection (defect face) | concrete face (cured face) | defined at | edits in the UpReqSampling case |
|---|---|---|---|
| `req` | `real_eq` | S02:411 | 58 occurrences |
| `lt` | `real_lt` | S02:480 | 22 occurrences |
| `le` | `real_le` | S02:484 | 38 occurrences |

118 relation-name tokens in total. The change pulse is **96 lines**
(86 diff hunks, each hunk mechanically re-verified as a pure three-mapping edit with
0 unexpected changes; `seat_reanchor/账/重锚diff-96行.patch` is on record).

### Edit scope, three parts (what changes, what must not change)

| face | disposition | case basis |
|---|---|---|
| signature statements (Theorem/Lemma/Variable/Hypothesis slots · 51 items) | three-mapping re-anchor | affected statements 61 = 51 signature + 10 in-body assert faces |
| in-body assert type faces (local statements inside `Proof` · 10 items) | treated the same (type faces migrate with them) | assert faces do not land as separate extraction export names, but their type faces share the defect and take the same cure |
| proof-body tactics/terms | **zero character changes** | the E5 acceptance criterion: the edited face compiled in a single pass (rc=0 on the first compile) |
| comment lines carrying bare tokens (14 lines: source lines 2/16/20/65/66/77/88/145/146/641/668/696/720/1011) | **untouched** | comments never enter the extraction face; touching them would break the purity of the diff pulse |
| the `Notation R := Real` bridge | **kept** | kept, matching the in-tree UpReqAlgebra precedent |
| the `Class` field definitions themselves (the S07 original) | **must not be touched** (read-only in the Set repository) | re-anchoring touches piece faces only, never library faces |
| premise/binder positions | **untouched** (same source as non-negotiable constraint 2, the lawful-keep rule) | the `nw6` precedent states the same rule: premise/binder positions accept no hard repair |

### Four acceptance checks of the case (measured on UpReqSampling, October 31, 2026)

| check | criterion | measured |
|---|---|---|
| first compile | RC=0 + `.vo` magic header `436f7121 00015ff4` + `.vo` newer than `.v` | RC=0, passed in a single attempt (vo md5 `10d393bd3bc3641f1aa7e4fbf91be4e6` · 50826B) |
| `gate7` extraction probe | **magic=0 (hard acceptance)** | magic_ml=0 / magic_mli=0 (51 names · missing=0); baseline 293→0; an independent re-check of `Obj.magic` over the `.ml`/`.mli` faces returned zero on both |
| cross-check against the reference (statement names) | `mac_stmt_names` ordered equality | census 51=51, with `Let` 67=67 · ordered equality PASS (product md5 `45ce11a7283926051698a46ebc012a09` vs source `4dba5385…`) |
| `gate4` + CJK + admission forms | PASS=1 FAIL=0; CJK=0; admission forms=0 | all met (the 30-line header carries all five fields; `Admitted`/`admit`/`Abort` word-boundary counts are 0) |

Signature-stability note: the six pieces are leaf pieces newly registered under `M34`, with zero
in-tree downstream consumers (per the `sandbox/seat_magic6/` ledger, section 2.4)
→ no downstream adaptation surface; the registered face md5 changes
(`4dba5385…`→`45ce11a7…`) → the `M34` registration anchor moves with the registration
work stream (registration belongs to orchestration, not to the re-anchoring agent). `.vo`
generation: after re-anchoring, the `.vo` digest differs from the registered defective-face
`.vo` (`817f2929…`); the defective-face `.vo` was removed from the re-anchoring agent's
world, and the compile purity is preserved.

## 3. Wiring into the rocqwash tooling (the three pieces in this repository, each in place)

1. **ledger sanitize** (`wash/wash_engine.py` · frozen, in service): the three mappings are naturally
   exact-string ledger entries; one entry per mapping,
   `{"tag":"req2real_eq","old":"req ","new":"real_eq ","expect":N}`
   (`expect` takes the measured count; word-boundary exceptions; comment lines, premise positions,
   proof bodies; are pinned by sufficient context inside the entry's `old` string; a bare
   whole-word replace-all is **forbidden**).
2. **pre-compile world assertion** (`wash/world_hook.py` · new piece 1): `--world <dir> --manifest
   <certified-generation-account>` asserts before the compile that the world equals the certified
   generation (the `nw5` tripwire).
3. **close-out verification**: the `gate6` side is `verify/verify_gate6.py`
   (new piece 3; a thin caller over the canonical verifier, packaged for case checking);
   the `gate7` magic=0 hard-acceptance side belongs to `wrapper/gate7_probe.sh`
   (the existing canonical launch layer).
4. **piece selection** (`tools/select_audit.py` · new piece 2): the six-piece batch is a
   multi-agent shared `work`-world record (migration account, section 5.1); before selecting a
   batch, audit the full tree `order.txt` table for duplicates and cross-batch name collisions
   (the `enbig7` precedent).

## 4. When the recipe does not apply (boundaries; no forced fit)

- The statement surfaces already use concrete names, yet magic is non-zero → not an E5 defect
  (inspect the missing/exclusions faces of the `gate7` probe).
- The piece has in-tree downstream consumers → the migration account is no longer a light account:
  a signature re-anchor drags downstream adaptation with it; first establish the consumer faces
  (a `mac_stmt_names` cross-check against the reference plus a full-table `Require`-face grep)
  before editing.
- The `Class` field bodies themselves need changes → out of authority: the S07 original is
  read-only inside the Set repository; raise the change through orchestration; the recipe face
  does not act in its place.
