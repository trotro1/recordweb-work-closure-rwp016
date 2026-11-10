# Provisional Work Closure predicate declarations

Version: `draft-0.9`  
Status: Local design declaration only; the `https://example.org/` IRIs are not published or resolvable

These declarations document the meaning used by the test vectors. They do not satisfy RWP 0.0.16's publication requirement until issued at stable, versioned, resolvable IRIs.

All predicates have a hard link to a finalized Work Closure CaseRecord Version as subject and a hard link to an RWP Record Version as object. Each AssertionRecord must contain the Root AssertionRecord fields `subject`, `predicate`, `object`, `assertedBy`, and `assertedAt`.

Application acceptance additionally requires cryptographic verification of that AssertionRecord Version's owner proof, equality between the verified signer/controller and `assertedBy`, and authorization of that DID for the exact Case Version. These are verifier-policy requirements, not additional RWP Root AssertionRecord fields.

When one Assertion Record has multiple Versions, only the unique latest finalized head identified by the RWP `parents` graph is considered. The validator enforces each declared object kind, each singular cardinality, and the absence of duplicate selected assertions from separate Record DIDs.

| Predicate | Direction and meaning | Object kind | Validation requirement |
|---|---|---|---|
| `wce:hasMandate` | case → mandate governing the bounded work | Mandate Record | object is in `trigger`; exactly one |
| `wce:hasAuthorization` | case → authorization decision evaluated before execution | Authorization Decision Record | object is in `trigger`; exactly one |
| `wce:hasExecution` | case → record documenting work execution | Execution Record | object is in `process`; absent for denied |
| `wce:hasObservedEffect` | case → record of an effect that actually occurred or was checked | Observed Effect Record | object is in `context` |
| `wce:hasEvidence` | case → evidence used by effect or evaluation claims | Evidence Record | object is in `context` |
| `wce:hasEvaluation` | case → criterion-level evaluation | Criterion Evaluation Record | object is in `decision` |
| `wce:hasWorkAcceptance` | case → acceptance/rejection decision distinct from authorization | Work Acceptance Record | object is in `decision`; exactly one |
| `wce:hasOpenObligation` | case → acknowledged residual obligation | Open Obligation Record | object is in `result` |
| `wce:hasPendingAction` | case → unfinished action required by provisional finality | Pending Action Record | object is in `result` |
| `wce:hasClosure` | case → finite business closure decision | Closure Record | object is in `result`; exactly one |
| `wce:hasStopEvidence` | case → evidence supporting an aborted stop | Evidence Record | object is in `context`; required for aborted |

The declaration does not create acceptance, authority, storage duties, reciprocity or modification of either subject or object. Each AssertionRecord remains attributable to its asserting agent. The AssertionRecords are separate Records and are not linked from the CaseRecord whose Version they describe.

