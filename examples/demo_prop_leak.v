(* examples/demo_prop_leak.v — rocqwash full-chain demo specimen (ORIGINAL, pre-wash)
 *
 * Single-file demo for the scan -> names -> wash -> verify chain.
 * Run `make demo` in this directory (see ./Makefile).

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
 *   scan   : expects conclusion-position RED hits (P4_bareeq / P5_le channels);
 *            premise-position hits are EXEMPT (lawful keep) per red-line-2.
 *   names  : expects exactly 5 top-level statements (N=5).
 *   wash   : the wash-target form is provided as washed/demo_prop_leak_washed.v
 *            (canonical mapping: conclusion bare = -> Id, conclusion nat <= -> NatLe).
 *   verify : the compile step runs under tools/cpu_guard.sh when rocq/coqc exists.
 *
 * Self-contained: Coq prelude only, no Require.
 *)

(* Set-carried equality carrier (wash target of a bare "=" conclusion). *)
Inductive Id (A : Type) (x : A) : A -> Set :=
  id_refl : Id A x x.

(* Set-carried order carrier (wash target of a bare "<=" conclusion). *)
Inductive NatLe : nat -> nat -> Set :=
  natle_ok : forall n : nat, NatLe n n.

(* 1. bare <= in conclusion position -> scanner RED (P5_le) *)
Lemma demo_le_self : forall x : nat, x <= x.
Proof.
  intros x. apply le_n.
Qed.

(* 2. bare = in conclusion position -> scanner RED (P4_bareeq) *)
Lemma demo_eq_self : forall x : nat, x = x.
Proof.
  intros x. reflexivity.
Qed.

(* 3. premise = stays lawful (EXEMPT); conclusion = -> RED (P4_bareeq) *)
Lemma demo_eq_sym : forall x y : nat, x = y -> y = x.
Proof.
  intros x y H. exact (eq_sym H).
Qed.

(* 4. mixed statement: premise <= (EXEMPT) + conclusion = (RED) *)
Lemma demo_le_eq : forall x : nat, x <= x -> x = x.
Proof.
  intros x H. reflexivity.
Qed.

(* 5. <= on both sides: premise EXEMPT, conclusion RED (P5_le) *)
Lemma demo_mixed : forall x : nat, x <= x -> x <= x.
Proof.
  intros x H. exact H.
Qed.
