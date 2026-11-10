# RWP Work Closure Case — Application Subschema Candidate

Version: `draft-0.9`  
Date: 2026-11-10  
Status: Experimental application artifact; not an RWP specification, profile, extension, or conformance claim

## 1. Purpose

This candidate tests whether the finite closure of one bounded unit of work can be represented as an application-specific subclass of the RWP 0.0.16 Root CaseRecord Schema.

It follows the RecordWeb maintainer's initial recommendation to use the existing Root CaseRecord link groups and attributable AssertionRecords before considering any shared extension.

## 2. Schema relationship

The SchemaRecord content in `119_work_closure_case_schemarecord_content_draft-0.9.json`:

- hard-links `subClassOf` to Root CaseRecord Schema version `sha256:3622…16e9`;
- retains `draft` and `finalized`;
- retains owner-signature policy and JSON payload formats;
- requires all five Root CaseRecord arrays to be present, while permitting an empty array where the terminal state has no member for that group;
- requires hard-link-shaped DID strings in the five arrays;
- rejects application fields outside the six Root CaseRecord properties, preventing business status from being placed directly on the CaseRecord; and
- does not add a business outcome to the RWP Version state.

## 3. Link-group contract

- `trigger`: mandate and authorization
- `context`: effects and evidence
- `process`: execution Records
- `decision`: criterion evaluations and work acceptance/rejection
- `result`: obligations, pending actions and closure

The specific role of each linked Record is projected through a separate AssertionRecord after the CaseRecord Version is finalized. The AssertionRecord subject is a hard link to that specific CaseRecord Version. A role assertion is valid for this application only when its object is also present in the corresponding Root CaseRecord array.

Role AssertionRecords are not members of the CaseRecord. This avoids making CaseRecord finalization depend on AssertionRecords that cannot themselves be finalized before the non-core predicates are published.

Candidate assertions are not accepted merely because they refer to the Case. Before SHACL evaluation, the verifier verifies that the Case proof signer equals the Case owner. For each Assertion Version it verifies that the owner-proof signer equals both the Assertion Record owner and `assertedBy`; that DID must also be authorized for the exact Case Version. Unknown issuers, unverified proofs and signer-mismatched self-claims are ignored. The trusted selected set must independently satisfy all required-role constraints.

## 4. Business terminal states

The Closure Record carries one of:

- `completed`
- `denied`
- `partial`
- `aborted`

These values describe the represented work. They do not replace, extend, or interpret the RWP Version state `finalized`.

### 4.1 Completed

- authorization is `allow`;
- an execution Record is linked through `process`;
- every mandate criterion has one linked evaluation in `decision`;
- every evaluation is `met` and derived from evidence linked through `context`;
- each evaluation has evidence attributed to an identifier different from every execution actor identifier;
- work acceptance is `accepted`;
- each observed effect has a controlled outcome and evidence;
- effect completeness is `complete` and finality is `settled`;
- no open obligation or pending action remains; and
- the execution actor identifier differs from the evaluator, acceptance actor and closure actor identifiers.

### 4.2 Denied

- authorization is `deny`, `ask`, or `stop`;
- work acceptance is `rejected`;
- effect finality is `notApplicable`; and
- `process` is empty and no effect, evaluation, open obligation or pending action is linked.

### 4.3 Partial

- work acceptance is `partiallyAccepted`; and
- at least one criterion is not met or an acknowledged open obligation remains.

An open obligation names an owner, successor work, acknowledgement actor/time and evidence.

### 4.4 Aborted

- execution is linked through `process`;
- stop evidence is linked through `context`; and
- at least one actual effect, acknowledged obligation or pending action is linked.

For every terminal state, `provisional` effect finality requires at least one Pending Action Record. A `reverted` Observed Effect Record retains a link to the earlier `applied` effect.

## 5. Validation layers

1. **Root JSON Schema** validates the five CaseRecord fields and DID-shaped items.
2. **Application JSON Schema** adds presence, uniqueness and hard-link-shape requirements.
3. **Root and application AssertionRecord JSON Schemas** validate hard-linked subjects/objects, DID-form asserting agents and date-time syntax.
4. **SHACL Core and SHACL-SPARQL** validate the semantic projection and cross-record invariants.

Before layer 4, the verifier performs a separate **proof verification and trust-selection step** using an authenticated policy. The bundled policy and proof-verification result are illustrative test fixtures only. Reverse lookup such as RWP Issue #37 may supply same-namespace candidates but does not make them authoritative and does not discover cross-namespace referrers.

The Assertion Version's verified proof creation time must be strictly later than the Case Version's verified proof creation time. `assertedAt` remains syntax-checked metadata but is not the ordering authority. The validator fails closed if RFC 3339 format support is unavailable.

For Versions of the same Assertion Record DID, the unique finalized head is selected exclusively from the verified RWP `parents` graph. Incomplete, branched or missing-head graphs fail closed. Proof creation time is used only to require that the Assertion proof follows the Case proof; it does not determine version succession.

Separate Assertion Record DIDs are never silently collapsed. Duplicate semantic assertions, wrong predicate object types, violations of singular predicate counts, and different-object conflicts fail closed. An issuer mistake may therefore keep the Case invalid until a valid version-graph successor/merge or an explicit supported withdrawal mechanism resolves it.

Passing all layers does not establish production RWP finalisation, resolvability, proof validity, evidence truth, authority, institutional independence or legal effect.

## 6. Publication prerequisites

Before any finalized RWP implementation or conformance statement:

- publish the non-core predicate declarations at stable, versioned, resolvable IRIs;
- replace all illustrative DIDs and hash components;
- verify every CaseRecord link as a resolvable hard link to a finalized Version;
- validate actual Records against the complete type chains; and
- apply an explicit trust policy for agents, evidence producers, acceptance and closure authority.

The CaseRecord itself may be finalized before the role AssertionRecords. Until the predicate declarations are published and the AssertionRecords are finalized, however, the application must report the Work Closure role-validation status as incomplete and must not claim complete Work Closure validation.

The application must authenticate the assertion-selection policy, bind it to the exact Case Version, verify Case-owner and Assertion-owner proofs, bind the Assertion signer to `assertedBy`, select the unique finalized version-graph head, and reject a result when trusted assertions are incomplete, duplicated or conflicting. Assertions by unlisted or signer-mismatched issuers are ignored rather than treated as evidence or allowed to invalidate an otherwise valid Case.

