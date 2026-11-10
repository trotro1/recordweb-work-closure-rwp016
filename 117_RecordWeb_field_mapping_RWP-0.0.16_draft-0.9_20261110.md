# Work Closure — RWP 0.0.16 Root CaseRecord Mapping

Version: `draft-0.9`  
Date: 2026-11-10  
Status: Non-normative application mapping; not an RWP extension or conformance claim

## 1. Fixed baseline

| Source | Fixed version |
|---|---|
| RecordWeb Protocol | `0.0.16`, commit `1823691d1c4bd097e2d911354db55f9011746815` |
| Root CaseRecord Schema | `sha256:3622a965594d5b9970f2e5c92c66f878ccfb5a972f61ac3b46ef41dbfa1116e9` |
| Root AssertionRecord Schema | `sha256:fe06970166343fd7ca1c7c948617c7f1869d2273727a66333aa459cd7a123ef4` |
| Work Closure Core | `draft-0.3`, 2026-11-07 |

## 2. Architectural placement

The candidate is a SchemaRecord whose `subClassOf` is a hard link to the Root CaseRecord Schema version fixed above. It adds application requirements but does not remove or reinterpret any Root CaseRecord field.

The CaseRecord remains a view linking autonomous Records. It does not contain the linked Records. The examples are JSON-LD/PROV-O projections that place the linked Records in one test graph only to make cross-record constraints reproducible.

## 3. Root field mapping

| Work Closure role | RWP 0.0.16 field | Treatment |
|---|---|---|
| mandate | `trigger` | one Mandate Record; its criteria remain in that Record |
| authorization decision | `trigger` | one Authorization Decision Record; authorization is a precondition that triggers or blocks processing |
| execution record | `process` | zero for `denied`; one or more for work that began |
| observed effect | `context` | actual effect Record relevant to evaluating and closing the work; placement is based on the maintainer's initial mapping and is raised again in the Issue because `result` is also plausible |
| supporting evidence | `context` | autonomous evidence Records; integrity does not imply sufficiency or truth |
| criterion evaluation | `decision` | criterion-level Evaluation Records |
| work acceptance or rejection | `decision` | one Work Acceptance Record, distinct from authorization |
| acknowledged open obligation | `result` | zero or more Obligation Records with owner, successor work, acknowledgement and evidence |
| pending action | `result` | explicit unfinished action required when effect finality is provisional |
| finite work closure | `result` | one Closure Record carrying the business terminal state |

RWP permits a Record to appear in more than one field, but this candidate uses the single primary placement above to keep the test vectors deterministic.

## 4. Specific relationship semantics

The Root CaseRecord field names provide only their general descriptions. The application therefore projects the following specific roles as separate AssertionRecords created after the CaseRecord Version is finalized:

| Predicate placeholder | Subject | Object | Expected field of object |
|---|---|---|---|
| `wce:hasMandate` | Work Closure CaseRecord | Mandate Record | `trigger` |
| `wce:hasAuthorization` | Work Closure CaseRecord | Authorization Decision Record | `trigger` |
| `wce:hasExecution` | Work Closure CaseRecord | Execution Record | `process` |
| `wce:hasObservedEffect` | Work Closure CaseRecord | Observed Effect Record | `context` |
| `wce:hasEvidence` | Work Closure CaseRecord | Evidence Record | `context` |
| `wce:hasEvaluation` | Work Closure CaseRecord | Criterion Evaluation Record | `decision` |
| `wce:hasWorkAcceptance` | Work Closure CaseRecord | Work Acceptance Record | `decision` |
| `wce:hasOpenObligation` | Work Closure CaseRecord | Open Obligation Record | `result` |
| `wce:hasPendingAction` | Work Closure CaseRecord | Pending Action Record | `result` |
| `wce:hasClosure` | Work Closure CaseRecord | Closure Record | `result` |
| `wce:hasStopEvidence` | Work Closure CaseRecord | Evidence Record | `context` |

These IRIs are placeholders. RWP 0.0.16 requires each non-core predicate to have a versioned, resolvable declaration. The included declaration document specifies the intended semantics but is not yet a public resolver. Consequently, the test AssertionRecords must not be represented as finalized RWP AssertionRecords.

The AssertionRecords are deliberately not linked from the CaseRecord. The sequencing is:

1. finalize every Record linked by the CaseRecord;
2. finalize the CaseRecord Version using only hard links to those finalized Records;
3. after the predicates are published, create role AssertionRecords whose `subject` is a hard link to that finalized CaseRecord Version; and
4. run the application-level Work Closure validation over the CaseRecord Version, linked Records and separate AssertionRecords.

This avoids a finalization cycle. It also means that RWP finalization of the CaseRecord alone does not establish the complete Work Closure role semantics.

### 4.1 Assertion discovery and authority selection

RWP Issue #37's proposed `RecordReferrers` service can discover finalized RelationRecords referring to a target within one namespace. References from other namespaces are explicitly out of scope, so cross-namespace assertions require another delivery or discovery channel. The Issue itself states that returned entries are pointers rather than evidence and must be resolved and validated before reliance. Discovery therefore does not decide which AssertionRecords are authoritative.

This application applies a fail-closed verifier policy before SHACL evaluation:

1. discover or otherwise receive candidate AssertionRecords;
2. resolve and validate the Case and each candidate Version, verify that each owner proof signer matches that Record's owner, and obtain the verified proof creation time and version-graph metadata;
3. select only assertions whose `assertedBy` equals that verified signer/controller and is authorized for the exact Case Version by an authenticated owner policy or authenticated mandate fixed before collection;
4. ignore assertions from all other issuers; and
5. require the selected trusted set to satisfy the role-completeness and consistency constraints.

The included `115_work_closure_assertion_trust_policy_draft-0.9.json` and `116_assertion_proof_verification_fixture_draft-0.9.json` are test fixtures. The latter simulates output from cryptographic proof verification; it is not itself a proof. A production policy must be authenticated and version-bound, and proof results must be derived from the resolved Versions. An untrusted contradictory assertion cannot invalidate the Case, while an untrusted or signer-mismatched assertion cannot satisfy a required role.

For Versions of the same Assertion Record DID, succession is determined only from the verified RWP `parents` graph. The unique latest finalized head is selected; an incomplete graph, branch without a unique head, or missing head fails closed. Proof time does not create or repair a version edge. A successor may change the asserted object and supersede the old Version.

Assertions issued as different Record DIDs are not treated as revisions of one another. Duplicate `(subject, predicate, object)` assertions are rejected. Different-object conflicts from authorized issuers remain visible to SHACL and fail closed under predicate cardinality, object-type and Case-link rules. Recovery therefore requires an RWP-valid successor/merge or an explicit future withdrawal mechanism; repeated publication of separate conflicting Records can keep the Case invalid.

## 5. PROV-O projection corrections

RWP treats a Record as a `prov:Entity`. This revision therefore does not type an Execution Record or Evaluation Record as `prov:Activity`.

- an Execution Record is an Entity `prov:wasGeneratedBy` a separate work Activity;
- the work Activity uses a qualified Association containing `prov:agent` and `prov:hadPlan`;
- an Observed Effect Record may be `prov:wasGeneratedBy` the work Activity;
- an Evidence Record may be `prov:wasAttributedTo` its producer;
- an Evaluation Record is `prov:wasGeneratedBy` a separate evaluation Activity and `prov:wasDerivedFrom` its evidence.

This avoids attaching Activity-domain predicates directly to a Record Entity.

## 6. Terminal-state constraints

`finalized` remains an RWP Version state. The following are application payload values carried by the linked Closure Record:

- `completed`
- `denied`
- `partial`
- `aborted`

The SHACL layer validates, among other rules:

- criterion coverage and evidence for `completed`;
- acceptance, effect completeness/finality, and absence of residual obligations for `completed`;
- no execution/effect/evaluation for `denied`;
- an acknowledged obligation or non-met criterion for `partial`;
- execution, stop evidence, and an effect/obligation/pending action for `aborted`;
- a pending action when finality is `provisional`; and
- retained applied history when an effect is `reverted`.
- the declared object Record type for every predicate;
- exactly one selected `hasMandate`, `hasAuthorization`, `hasWorkAcceptance`, and `hasClosure`; and
- no duplicate selected `(subject, predicate, object)` assertions from separate Records.

## 7. What this does not claim

The reviewed RWP material supplies identity, linking, schema inheritance, version finalisation, integrity and attributable assertions. This candidate adds only an application constraint set that correlates the linked Records for one bounded unit of work. It does not claim that RWP lacks those mechanisms or that this constraint set is novel outside the reviewed materials.

## 8. Maintainer reply evidence and placement question

The received reply states verbatim: “Mandate and authorization map to trigger. Execution maps to process. Observed effect and evidence map to context or process.” It then assigns criterion evaluation and acceptance/rejection to `decision`, and obligation and closure to `result`.

The draft follows that initial mapping. Because RWP also describes `decision` as documenting decisions and `result` as documenting outcomes, the GitHub Issue asks whether authorization should additionally appear in `decision` and whether observed effects should additionally appear in `result`. RWP 0.0.16 permits the same Record in more than one field.

The Issue also asks whether RWP assumes an authoritative-asserter selection rule beyond discovery, including signer-to-`assertedBy` binding, cross-namespace discovery, version-graph head selection and conflict/withdrawal semantics. This is separate from `RecordReferrers`: reverse lookup finds candidate referrers, whereas the application trust policy decides which proof-verified candidates may affect the Work Closure result.

