#!/usr/bin/env python3
"""Generate four non-normative RWP 0.0.16 JSON-LD/PROV-O projections."""

from __future__ import annotations

import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
OUT = BASE / "examples_recordweb_r9"
CONTEXT = "../122_work_closure_context_draft-0.9.jsonld"
VERIFICATION_FIXTURE = BASE / "116_assertion_proof_verification_fixture_draft-0.9.json"
WCE = "https://example.org/ns/work-closure#"

CASE_PROOF_TIMES = {
    "case-completed": "2026-11-10T01:10:35Z",
    "case-partial": "2026-11-10T02:25:35Z",
    "case-denied": "2026-11-10T03:01:15Z",
    "case-aborted": "2026-11-10T04:05:35Z",
}

FORGED_SIGNER_ASSERTION_ID = "did:rwp:attacker.example:assert-forged-signer:sha256:" + "8" * 64
AUTHORIZED_CONFLICT_ASSERTION_ID = "did:rwp:example.org:assert-authorized-conflict:sha256:" + "7" * 64
STALE_DUPLICATE_ASSERTION_ID = "did:rwp:example.org:assert-completed-10:sha256:" + "6" * 64
UNTRUSTED_CONFLICT_ASSERTION_ID = "did:rwp:attacker.example:assert-conflict:sha256:" + "9" * 64
DUPLICATE_MANDATE_ASSERTION_ID = "did:rwp:example.org:assert-duplicate-mandate:sha256:" + "5" * 64
WRONG_KIND_ASSERTION_ID = "did:rwp:example.org:assert-wrong-kind:sha256:" + "4" * 64


def version_parts(version_did: str) -> tuple[str, str]:
    record_did, digest = version_did.rsplit(":sha256:", 1)
    return record_did, f"sha256:{digest}"


def verified_version(
    version_did: str,
    *,
    owner: str,
    signer: str,
    proof_created_at: str,
    parents: list[str] | None = None,
) -> dict:
    record_did, version_hash = version_parts(version_did)
    return {
        "proofVerified": True,
        "recordDid": record_did,
        "versionHash": version_hash,
        "state": "finalized",
        "parents": parents or [],
        "recordOwner": owner,
        "verificationMethodController": signer,
        "proofCreatedAt": proof_created_at,
    }


def hard(record_id: str, hex_char: str) -> str:
    return f"did:rwp:example.org:{record_id}:sha256:{hex_char * 64}"


def record(identifier: str, *types: str, **properties: object) -> dict:
    return {"@id": identifier, "@type": ["rw:Record", *types], **properties}


def assertion(identifier: str, case: str, predicate: str, obj: str, asserted_at: str) -> dict:
    return record(
        identifier,
        "wce:RoleAssertionRecord",
        subject=case,
        predicate=f"{WCE}{predicate}",
        object=obj,
        assertedBy="did:rwp:example.org:agent-record-authority",
        assertedAt=asserted_at,
    )


def assertions(case: str, roles: list[tuple[str, str]], stamp: str, prefix: str) -> tuple[list[str], list[dict]]:
    ids: list[str] = []
    nodes: list[dict] = []
    digits = "123456789abcdef"
    for index, (predicate, obj) in enumerate(roles):
        identifier = hard(f"assert-{prefix}-{index + 1:02d}", digits[index % len(digits)])
        ids.append(identifier)
        nodes.append(assertion(identifier, case, predicate, obj, stamp))
    return ids, nodes


def completed() -> dict:
    case = hard("case-completed", "0")
    mandate = hard("mandate-completed", "a")
    authorization = hard("authorization-completed", "b")
    execution = hard("execution-completed", "c")
    effect = hard("effect-completed", "d")
    evidence_diff = hard("evidence-diff-completed", "e")
    evidence_test = hard("evidence-test-completed", "f")
    evaluation_tests = hard("evaluation-tests-completed", "1")
    evaluation_review = hard("evaluation-review-completed", "2")
    acceptance = hard("acceptance-completed", "3")
    closure = hard("closure-completed", "4")
    work_activity = "urn:uuid:10000000-0000-4000-8000-000000000001"
    eval_activity_tests = "urn:uuid:10000000-0000-4000-8000-000000000002"
    eval_activity_review = "urn:uuid:10000000-0000-4000-8000-000000000003"

    role_ids, role_nodes = assertions(case, [
        ("hasMandate", mandate),
        ("hasAuthorization", authorization),
        ("hasExecution", execution),
        ("hasObservedEffect", effect),
        ("hasEvidence", evidence_diff),
        ("hasEvidence", evidence_test),
        ("hasEvaluation", evaluation_tests),
        ("hasEvaluation", evaluation_review),
        ("hasWorkAcceptance", acceptance),
        ("hasClosure", closure),
    ], "2026-11-10T01:10:40Z", "completed")

    graph = [
        record(
            case,
            "wce:WorkClosureCaseRecord",
            testVector=True,
            title="Completed bounded work",
            trigger=[mandate, authorization],
            context=[effect, evidence_diff, evidence_test],
            process=[execution],
            decision=[evaluation_tests, evaluation_review, acceptance],
            result=[closure],
        ),
        record(mandate, "prov:Plan", "wce:MandateRecord", criterion=["tests-pass", "review-recorded"]),
        record(
            authorization,
            "wce:AuthorizationDecisionRecord",
            outcome="allow",
            decidedBy="did:rwp:example.org:pdp-engineering",
            decidedAt="2026-11-10T01:01:00Z",
        ),
        record(
            execution,
            "wce:ExecutionRecord",
            documentsActivity=work_activity,
            **{"prov:wasGeneratedBy": {"@id": work_activity}},
        ),
        {
            "@id": work_activity,
            "@type": "prov:Activity",
            "prov:qualifiedAssociation": {
                "@type": "prov:Association",
                "prov:agent": {"@id": "spiffe://example.org/agent/coding-01"},
                "prov:hadPlan": {"@id": mandate},
            },
        },
        record(
            effect,
            "wce:ObservedEffectRecord",
            outcome="applied",
            evidence=[evidence_diff],
            **{"prov:wasGeneratedBy": {"@id": work_activity}},
        ),
        record(evidence_diff, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:git-service"}}),
        record(evidence_test, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:ci-service"}}),
        record(
            evaluation_tests,
            "wce:CriterionEvaluationRecord",
            criterion="tests-pass",
            outcome="met",
            **{
                "prov:wasGeneratedBy": {"@id": eval_activity_tests},
                "prov:wasDerivedFrom": {"@id": evidence_test},
            },
        ),
        {"@id": eval_activity_tests, "@type": "prov:Activity", "prov:wasAssociatedWith": {"@id": "did:rwp:example.org:ci-service"}},
        record(
            evaluation_review,
            "wce:CriterionEvaluationRecord",
            criterion="review-recorded",
            outcome="met",
            **{
                "prov:wasGeneratedBy": {"@id": eval_activity_review},
                "prov:wasDerivedFrom": {"@id": evidence_diff},
            },
        ),
        {"@id": eval_activity_review, "@type": "prov:Activity", "prov:wasAssociatedWith": {"@id": "did:rwp:example.org:reviewer-7"}},
        record(
            acceptance,
            "wce:WorkAcceptanceRecord",
            workAcceptanceStatus="accepted",
            decidedBy="did:rwp:example.org:maintainer-42",
            decidedAt="2026-11-10T01:10:25Z",
        ),
        record(
            closure,
            "wce:ClosureRecord",
            closureStatus="completed",
            effectCompleteness="complete",
            effectFinality="settled",
            closedBy="did:rwp:example.org:closure-authority-1",
            closedAt="2026-11-10T01:10:30Z",
        ),
        *role_nodes,
    ]
    return {"@context": CONTEXT, "@graph": graph}


def partial() -> dict:
    case = hard("case-partial", "0")
    mandate = hard("mandate-partial", "a")
    authorization = hard("authorization-partial", "b")
    execution = hard("execution-partial", "c")
    effect = hard("effect-partial", "d")
    evidence_diff = hard("evidence-diff-partial", "e")
    evidence_test = hard("evidence-test-partial", "f")
    evidence_transfer = hard("evidence-transfer-partial", "1")
    evaluation_a = hard("evaluation-a-partial", "2")
    evaluation_b = hard("evaluation-b-partial", "3")
    acceptance = hard("acceptance-partial", "4")
    obligation = hard("obligation-partial", "5")
    closure = hard("closure-partial", "6")
    work_activity = "urn:uuid:20000000-0000-4000-8000-000000000001"
    eval_activity_a = "urn:uuid:20000000-0000-4000-8000-000000000002"
    eval_activity_b = "urn:uuid:20000000-0000-4000-8000-000000000003"

    role_ids, role_nodes = assertions(case, [
        ("hasMandate", mandate), ("hasAuthorization", authorization),
        ("hasExecution", execution), ("hasObservedEffect", effect),
        ("hasEvidence", evidence_diff), ("hasEvidence", evidence_test),
        ("hasEvidence", evidence_transfer), ("hasEvaluation", evaluation_a),
        ("hasEvaluation", evaluation_b), ("hasWorkAcceptance", acceptance),
        ("hasOpenObligation", obligation), ("hasClosure", closure),
    ], "2026-11-10T02:25:40Z", "partial")

    graph = [
        record(
            case, "wce:WorkClosureCaseRecord", testVector=True,
            title="Partially accepted bounded work",
            trigger=[mandate, authorization],
            context=[effect, evidence_diff, evidence_test, evidence_transfer],
            process=[execution], decision=[evaluation_a, evaluation_b, acceptance],
            result=[obligation, closure],
        ),
        record(mandate, "prov:Plan", "wce:MandateRecord", criterion=["module-a-pass", "module-b-pass"]),
        record(authorization, "wce:AuthorizationDecisionRecord", outcome="allow", decidedBy="did:rwp:example.org:pdp-engineering", decidedAt="2026-11-10T02:01:00Z"),
        record(execution, "wce:ExecutionRecord", documentsActivity=work_activity, **{"prov:wasGeneratedBy": {"@id": work_activity}}),
        {"@id": work_activity, "@type": "prov:Activity", "prov:qualifiedAssociation": {"@type": "prov:Association", "prov:agent": {"@id": "spiffe://example.org/agent/coding-02"}, "prov:hadPlan": {"@id": mandate}}},
        record(effect, "wce:ObservedEffectRecord", outcome="applied", evidence=[evidence_diff], **{"prov:wasGeneratedBy": {"@id": work_activity}}),
        record(evidence_diff, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:git-service"}}),
        record(evidence_test, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:ci-service"}}),
        record(evidence_transfer, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:team-platform"}}),
        record(evaluation_a, "wce:CriterionEvaluationRecord", criterion="module-a-pass", outcome="met", **{"prov:wasGeneratedBy": {"@id": eval_activity_a}, "prov:wasDerivedFrom": {"@id": evidence_test}}),
        {"@id": eval_activity_a, "@type": "prov:Activity", "prov:wasAssociatedWith": {"@id": "did:rwp:example.org:ci-service"}},
        record(evaluation_b, "wce:CriterionEvaluationRecord", criterion="module-b-pass", outcome="notMet", **{"prov:wasGeneratedBy": {"@id": eval_activity_b}, "prov:wasDerivedFrom": {"@id": evidence_test}}),
        {"@id": eval_activity_b, "@type": "prov:Activity", "prov:wasAssociatedWith": {"@id": "did:rwp:example.org:ci-service"}},
        record(acceptance, "wce:WorkAcceptanceRecord", workAcceptanceStatus="partiallyAccepted", decidedBy="did:rwp:example.org:maintainer-42", decidedAt="2026-11-10T02:25:00Z"),
        record(obligation, "wce:OpenObligationRecord", owner="did:rwp:example.org:team-platform", successorWork="urn:uuid:20000000-0000-4000-8000-000000000004", acknowledgedBy="did:rwp:example.org:team-platform", acknowledgedAt="2026-11-10T02:25:10Z", evidence=[evidence_transfer]),
        record(closure, "wce:ClosureRecord", closureStatus="partial", effectCompleteness="complete", effectFinality="settled", closedBy="did:rwp:example.org:maintainer-42", closedAt="2026-11-10T02:25:30Z"),
        *role_nodes,
    ]
    return {"@context": CONTEXT, "@graph": graph}


def denied() -> dict:
    case = hard("case-denied", "0")
    mandate = hard("mandate-denied", "a")
    authorization = hard("authorization-denied", "b")
    acceptance = hard("acceptance-denied", "c")
    closure = hard("closure-denied", "d")
    role_ids, role_nodes = assertions(case, [
        ("hasMandate", mandate), ("hasAuthorization", authorization),
        ("hasWorkAcceptance", acceptance), ("hasClosure", closure),
    ], "2026-11-10T03:01:20Z", "denied")
    graph = [
        record(case, "wce:WorkClosureCaseRecord", testVector=True, title="Denied bounded work", trigger=[mandate, authorization], context=[], process=[], decision=[acceptance], result=[closure]),
        record(mandate, "prov:Plan", "wce:MandateRecord", criterion=["deployment-authorized"]),
        record(authorization, "wce:AuthorizationDecisionRecord", outcome="deny", decidedBy="did:rwp:example.org:pdp-production", decidedAt="2026-11-10T03:01:00Z"),
        record(acceptance, "wce:WorkAcceptanceRecord", workAcceptanceStatus="rejected", decidedBy="did:rwp:example.org:maintainer-42", decidedAt="2026-11-10T03:01:05Z"),
        record(closure, "wce:ClosureRecord", closureStatus="denied", effectCompleteness="complete", effectFinality="notApplicable", closedBy="did:rwp:example.org:maintainer-42", closedAt="2026-11-10T03:01:10Z"),
        *role_nodes,
    ]
    return {"@context": CONTEXT, "@graph": graph}


def aborted() -> dict:
    case = hard("case-aborted", "0")
    mandate = hard("mandate-aborted", "a")
    authorization = hard("authorization-aborted", "b")
    execution = hard("execution-aborted", "c")
    effect_applied = hard("effect-applied-aborted", "d")
    effect_reverted = hard("effect-reverted-aborted", "e")
    evidence_change = hard("evidence-change-aborted", "f")
    evidence_stop = hard("evidence-stop-aborted", "1")
    evidence_revert = hard("evidence-revert-aborted", "2")
    pending = hard("pending-action-aborted", "3")
    acceptance = hard("acceptance-aborted", "4")
    closure = hard("closure-aborted", "5")
    work_activity = "urn:uuid:40000000-0000-4000-8000-000000000001"
    role_ids, role_nodes = assertions(case, [
        ("hasMandate", mandate), ("hasAuthorization", authorization),
        ("hasExecution", execution), ("hasObservedEffect", effect_applied),
        ("hasObservedEffect", effect_reverted), ("hasEvidence", evidence_change),
        ("hasEvidence", evidence_stop), ("hasEvidence", evidence_revert),
        ("hasStopEvidence", evidence_stop), ("hasPendingAction", pending),
        ("hasWorkAcceptance", acceptance), ("hasClosure", closure),
    ], "2026-11-10T04:05:40Z", "aborted")
    graph = [
        record(case, "wce:WorkClosureCaseRecord", testVector=True, title="Aborted bounded work", trigger=[mandate, authorization], context=[effect_applied, effect_reverted, evidence_change, evidence_stop, evidence_revert], process=[execution], decision=[acceptance], result=[pending, closure]),
        record(mandate, "prov:Plan", "wce:MandateRecord", criterion=["migration-completes"]),
        record(authorization, "wce:AuthorizationDecisionRecord", outcome="allow", decidedBy="did:rwp:example.org:pdp-engineering", decidedAt="2026-11-10T04:01:00Z"),
        record(execution, "wce:ExecutionRecord", documentsActivity=work_activity, **{"prov:wasGeneratedBy": {"@id": work_activity}}),
        {"@id": work_activity, "@type": "prov:Activity", "prov:qualifiedAssociation": {"@type": "prov:Association", "prov:agent": {"@id": "spiffe://example.org/agent/coding-04"}, "prov:hadPlan": {"@id": mandate}}},
        record(effect_applied, "wce:ObservedEffectRecord", outcome="applied", evidence=[evidence_change], **{"prov:wasGeneratedBy": {"@id": work_activity}}),
        record(effect_reverted, "wce:ObservedEffectRecord", outcome="reverted", priorEffect=effect_applied, evidence=[evidence_revert], **{"prov:wasGeneratedBy": {"@id": work_activity}}),
        record(evidence_change, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:secret-manager"}}),
        record(evidence_stop, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:security-signal-receiver"}}),
        record(evidence_revert, "wce:EvidenceRecord", **{"prov:wasAttributedTo": {"@id": "did:rwp:example.org:recovery-controller"}}),
        record(pending, "wce:PendingActionRecord", actionId="health-check-after-recovery", owner="did:rwp:example.org:team-sre", dueCondition="credential-recovery-confirmed"),
        record(acceptance, "wce:WorkAcceptanceRecord", workAcceptanceStatus="escalated", decidedBy="did:rwp:example.org:maintainer-42", decidedAt="2026-11-10T04:05:20Z"),
        record(closure, "wce:ClosureRecord", closureStatus="aborted", effectCompleteness="partial", effectFinality="provisional", closedBy="did:rwp:example.org:maintainer-42", closedAt="2026-11-10T04:05:30Z"),
        *role_nodes,
    ]
    return {"@context": CONTEXT, "@graph": graph}


def verification_fixture(examples: dict[str, dict]) -> dict:
    """Simulated output from proof verification, never production proof material."""
    versions: dict[str, dict] = {}
    for data in examples.values():
        case = next(
            item for item in data["@graph"]
            if "wce:WorkClosureCaseRecord" in item.get("@type", [])
        )
        proof_time = next(
            value for key, value in CASE_PROOF_TIMES.items() if key in case["@id"]
        )
        versions[case["@id"]] = verified_version(
            case["@id"],
            owner="did:rwp:example.org:case-owner",
            signer="did:rwp:example.org:case-owner",
            proof_created_at=proof_time,
        )
        for item in data["@graph"]:
            if "wce:RoleAssertionRecord" not in item.get("@type", []):
                continue
            versions[item["@id"]] = verified_version(
                item["@id"],
                owner=item["assertedBy"],
                signer=item["assertedBy"],
                proof_created_at=item["assertedAt"],
            )

    closure_current = next(
        version_id for version_id in versions
        if "assert-completed-10:sha256:" in version_id
    )
    versions[closure_current]["parents"] = ["sha256:" + "6" * 64]
    versions[FORGED_SIGNER_ASSERTION_ID] = verified_version(
        FORGED_SIGNER_ASSERTION_ID,
        owner="did:rwp:attacker.example:issuer-1",
        signer="did:rwp:attacker.example:issuer-1",
        proof_created_at="2026-11-10T01:10:45Z",
    )
    versions[AUTHORIZED_CONFLICT_ASSERTION_ID] = verified_version(
        AUTHORIZED_CONFLICT_ASSERTION_ID,
        owner="did:rwp:example.org:secondary-record-authority",
        signer="did:rwp:example.org:secondary-record-authority",
        proof_created_at="2026-11-10T01:10:46Z",
    )
    versions[STALE_DUPLICATE_ASSERTION_ID] = verified_version(
        STALE_DUPLICATE_ASSERTION_ID,
        owner="did:rwp:example.org:agent-record-authority",
        signer="did:rwp:example.org:agent-record-authority",
        proof_created_at="2026-11-10T01:10:38Z",
    )
    versions[UNTRUSTED_CONFLICT_ASSERTION_ID] = verified_version(
        UNTRUSTED_CONFLICT_ASSERTION_ID,
        owner="did:rwp:attacker.example:issuer-1",
        signer="did:rwp:attacker.example:issuer-1",
        proof_created_at="2026-11-10T01:10:45Z",
    )
    versions[DUPLICATE_MANDATE_ASSERTION_ID] = verified_version(
        DUPLICATE_MANDATE_ASSERTION_ID,
        owner="did:rwp:example.org:secondary-record-authority",
        signer="did:rwp:example.org:secondary-record-authority",
        proof_created_at="2026-11-10T01:10:47Z",
    )
    versions[WRONG_KIND_ASSERTION_ID] = verified_version(
        WRONG_KIND_ASSERTION_ID,
        owner="did:rwp:example.org:agent-record-authority",
        signer="did:rwp:example.org:agent-record-authority",
        proof_created_at="2026-11-10T01:10:48Z",
    )
    return {
        "fixtureVersion": "draft-0.9",
        "warning": "Simulated proof-verification output for tests only; not cryptographic evidence.",
        "versions": versions,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    examples = {
        "01_completed_work_closure_rwp-0.0.16.test.jsonld": completed(),
        "02_partial_work_closure_rwp-0.0.16.test.jsonld": partial(),
        "03_denied_work_closure_rwp-0.0.16.test.jsonld": denied(),
        "04_aborted_work_closure_rwp-0.0.16.test.jsonld": aborted(),
    }
    for name, data in examples.items():
        (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(name)
    VERIFICATION_FIXTURE.write_text(
        json.dumps(verification_fixture(examples), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(VERIFICATION_FIXTURE.name)


if __name__ == "__main__":
    main()
