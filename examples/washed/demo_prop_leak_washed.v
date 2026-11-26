(* examples/washed/demo_prop_leak_washed.v — WASH-TARGET SPECIMEN
 *
 * Canonical mapping applied (README "Seven Canonical Steps", step 3):
 *   conclusion-position bare =  -> Id nat ... (proved via id_refl)
 *   conclusion-position nat <=  -> NatLe ... (proved via natle_ok)
 * Premise-position Prop forms may stay (lawful keep, scanner EXEMPT).
 * The statement-name list is unchanged: N=N with the original
 * (asserted by: mac_stmt_names.py demo_prop_leak.v --compare ...).

Purpose.  Full-chain demo specimen: one self-contained Coq file with five statement faces.
Interface.  `make demo` in this directory; no arguments.
Mission.  Demonstrate the full scan -> names -> wash -> verify chain on one specimen; every stage reports its own real verdict.
Dependencies.  The repo's Python 3 tool faces; rocq/coqc optional (printed SKIP when absent, never a pass).
References.  examples/README.md (the demo chain) and the repository docs.
Evidence.  Each stage prints its own RUN/SKIP verdict; the wash stage asserts byte-identity against the washed reference (cmp).
Exit-codes.  Not applicable to a data face; `make demo` fails loud on any FAIL marker.
Constructivity.  The canonical wash targets are Set-carried (Id, NatLe); red conclusions in the pre-wash original are demonstration material, scanned read-only.
Build.  `make verify` runs the compile step (on the washed reference) under tools/cpu_guard.sh when rocq/coqc exists; absent, printed SKIP, never a pass.

 *
 * NOTE: compile-ability of this specimen has NOT been verified
 * (no rocq/coqc on the authoring machine). `make verify` runs the
 * compile step automatically on a rocq-equipped machine.
 *)

(* Set-carried equality carrier (wash target of a bare "=" conclusion). *)
Inductive Id (A : Type) (x : A) : A -> Set :=
  id_refl : Id A x x.

(* Set-carried order carrier (wash target of a bare "<=" conclusion). *)
Inductive NatLe : nat -> nat -> Set :=
  natle_ok : forall n : nat, NatLe n n.

(* 1. x <= x  ->  NatLe x x *)
Lemma demo_le_self : forall x : nat, NatLe x x.
Proof.
  intros x. apply natle_ok.
Qed.

(* 2. x = x  ->  Id nat x x *)
Lemma demo_eq_self : forall x : nat, Id nat x x.
Proof.
  intros x. apply id_refl.
Qed.

(* 3. conclusion y = x -> Id nat y x; premise x = y stays lawful Prop *)
Lemma demo_eq_sym : forall x y : nat, x = y -> Id nat y x.
Proof.
  intros x y H. rewrite H. apply id_refl.
Qed.

(* 4. premise <= -> NatLe; conclusion = -> Id *)
Lemma demo_le_eq : forall x : nat, NatLe x x -> Id nat x x.
Proof.
  intros x H. apply id_refl.
Qed.

(* 5. both sides <= -> NatLe *)
Lemma demo_mixed : forall x : nat, NatLe x x -> NatLe x x.
Proof.
  intros x H. exact H.
Qed.
