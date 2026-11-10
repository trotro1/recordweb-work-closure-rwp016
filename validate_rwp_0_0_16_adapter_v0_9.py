#!/usr/bin/env python3
"""Validate the RWP 0.0.16 Work Closure application-subschema candidate."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path

try:
    from rfc3339_validator import validate_rfc3339
except ImportError as exc:
    raise SystemExit(
        "FATAL: rfc3339-validator is required; refusing to run without RFC 3339 date-time validation"
    ) from exc

from jsonschema import Draft202012Validator, FormatChecker
from pyshacl import validate
from rdflib import Graph, Namespace, RDF, URIRef


BASE = Path(__file__).resolve().parent
EXAMPLE_DIR = BASE / "examples_recordweb_r9"
if not EXAMPLE_DIR.exists():
    EXAMPLE_DIR = BASE / "examples_positive"
NEGATIVE_DIR = BASE / "negative_recordweb_r9"
if not NEGATIVE_DIR.exists() and (BASE / "examples_negative").exists():
    NEGATIVE_DIR = BASE / "examples_negative"
SECURITY_DIR = BASE / "security_recordweb_r9"
if not SECURITY_DIR.exists() and (BASE / "examples_security").exists():
    SECURITY_DIR = BASE / "examples_security"
SHAPES_PATH = BASE / "123_work_closure_shapes_draft-0.9.ttl"
SUBSCHEMA_PATH = BASE / "119_work_closure_case_schemarecord_content_draft-0.9.json"
ROLE_SUBSCHEMA_PATH = BASE / "120_work_closure_role_assertion_schemarecord_content_draft-0.9.json"
TRUST_POLICY_PATH = BASE / "115_work_closure_assertion_trust_policy_draft-0.9.json"
VERIFICATION_FIXTURE_PATH = BASE / "116_assertion_proof_verification_fixture_draft-0.9.json"
SOURCE_DIR = BASE / "rwp_0_0_16_primary_sources"
if not SOURCE_DIR.exists() and (BASE / "primary_sources").exists():
    SOURCE_DIR = BASE / "primary_sources"
if not SOURCE_DIR.exists():
    SOURCE_DIR = BASE.parent / "primary_sources"
ROOT_CASE_PATH = SOURCE_DIR / "root-caserecord_3622a965.json"
ROOT_ASSERTION_PATH = SOURCE_DIR / "root-assertionrecord_fe069701.json"
EXAMPLE_PATHS = sorted(EXAMPLE_DIR.glob("*.jsonld"))

PROV = Namespace("http://www.w3.org/ns/prov#")
RW = Namespace("https://w3id.org/recordweb/ontology#")
WCE = Namespace("https://example.org/ns/work-closure#")

FORGED_SIGNER_ASSERTION_ID = "did:rwp:attacker.example:assert-forged-signer:sha256:" + "8" * 64
AUTHORIZED_CONFLICT_ASSERTION_ID = "did:rwp:example.org:assert-authorized-conflict:sha256:" + "7" * 64
STALE_DUPLICATE_ASSERTION_ID = "did:rwp:example.org:assert-completed-10:sha256:" + "6" * 64
UNTRUSTED_CONFLICT_ASSERTION_ID = "did:rwp:attacker.example:assert-conflict:sha256:" + "9" * 64
DUPLICATE_MANDATE_ASSERTION_ID = "did:rwp:example.org:assert-duplicate-mandate:sha256:" + "5" * 64
WRONG_KIND_ASSERTION_ID = "did:rwp:example.org:assert-wrong-kind:sha256:" + "4" * 64
NEW_MANDATE_ASSERTION_ID = "did:rwp:example.org:assert-completed-01:sha256:" + "b" * 64
NEW_MANDATE_RECORD_ID = "did:rwp:example.org:mandate-completed-v2:sha256:" + "b" * 64
UNTRUSTED_SUCCESSOR_ASSERTION_ID = "did:rwp:example.org:assert-completed-01:sha256:" + "c" * 64

CASE_FIELDS = ("title", "trigger", "context", "process", "decision", "result")
ASSERTION_FIELDS = ("subject", "predicate", "object", "assertedBy", "assertedAt", "effectiveAt")
ROOT_CASE_VERSION = "sha256:3622a965594d5b9970f2e5c92c66f878ccfb5a972f61ac3b46ef41dbfa1116e9"
ROOT_ASSERTION_VERSION = "sha256:fe06970166343fd7ca1c7c948617c7f1869d2273727a66333aa459cd7a123ef4"
ROOT_CASE_HARD_LINK = (
    "did:rwp:d2d14675-50c9-463d-b564-1ea50644c836:"
    "schema-root-caserecord:" + ROOT_CASE_VERSION
)
ROOT_ASSERTION_HARD_LINK = (
    "did:rwp:d2d14675-50c9-463d-b564-1ea50644c836:"
    "schema-root-assertionrecord:" + ROOT_ASSERTION_VERSION
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def root_json_schema(record_path: Path) -> dict:
    record = load(record_path)
    return record["payload"][0]["representations"][0]["content"]["jsonSchema"]


def graph_from_json(data: dict, base_path: Path) -> Graph:
    graph = Graph()
    graph.parse(data=json.dumps(data), format="json-ld", publicID=base_path.as_uri())
    return graph


def validate_shacl(data: dict, base_path: Path) -> tuple[bool, str, Graph]:
    graph = graph_from_json(data, base_path)
    conforms, _, report = validate(
        data_graph=graph,
        shacl_graph=str(SHAPES_PATH),
        shacl_graph_format="turtle",
        inference="none",
        advanced=True,
        abort_on_first=False,
        allow_infos=False,
        allow_warnings=False,
    )
    return bool(conforms), str(report), graph


def node(data: dict, *, identifier: str | None = None, type_name: str | None = None) -> dict:
    for item in data["@graph"]:
        types = item.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if identifier is not None and item.get("@id") == identifier:
            return item
        if type_name is not None and type_name in types:
            return item
    raise KeyError(identifier or type_name)


def nodes(data: dict, type_name: str) -> list[dict]:
    found: list[dict] = []
    for item in data["@graph"]:
        types = item.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if type_name in types:
            found.append(item)
    return found


def case_node(data: dict) -> dict:
    return node(data, type_name="wce:WorkClosureCaseRecord")


def case_payload(data: dict) -> dict:
    case = case_node(data)
    projection_only = {"@id", "@type", "testVector"}
    return {
        field: copy.deepcopy(value)
        for field, value in case.items()
        if field not in projection_only
    }


def assertion_payload(item: dict) -> dict:
    return {field: copy.deepcopy(item[field]) for field in ASSERTION_FIELDS if field in item}


def parse_rfc3339(value: str) -> datetime:
    if not isinstance(value, str) or not validate_rfc3339(value):
        raise ValueError(f"not a valid RFC 3339 date-time: {value!r}")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def select_trusted_assertions(
    data: dict,
    trust_policy: dict,
    verification_results: dict,
) -> tuple[dict, list[str], int]:
    """Select proof-bound, authorized heads from each RWP version graph."""
    selected = copy.deepcopy(data)
    case_id = case_node(selected)["@id"]
    rule = trust_policy.get("cases", {}).get(case_id)
    if rule is None:
        return selected, [f"no authenticated assertion-selection rule for {case_id}"], 0
    allowed = set(rule.get("authorizedAssertedBy", []))
    versions = verification_results.get("versions", {})
    case_proof = versions.get(case_id)
    if not case_proof or case_proof.get("proofVerified") is not True:
        return selected, [f"no verified proof result for Case Version {case_id}"], 0
    case_owner = case_proof.get("recordOwner")
    case_signer = case_proof.get("verificationMethodController")
    if not case_owner or case_signer != case_owner:
        return selected, ["verified Case proof signer does not match the Case owner"], 0
    try:
        case_proof_created = parse_rfc3339(case_proof["proofCreatedAt"])
    except (KeyError, ValueError) as exc:
        return selected, [f"invalid verified Case proof creation time: {exc}"], 0

    kept_non_assertions: list[dict] = []
    candidates: list[tuple[dict, dict]] = []
    ignored = 0
    errors: list[str] = []
    for item in selected["@graph"]:
        types = item.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if "wce:RoleAssertionRecord" not in types:
            kept_non_assertions.append(item)
            continue
        proof_result = versions.get(item.get("@id"))
        if not proof_result or proof_result.get("proofVerified") is not True:
            ignored += 1
            continue
        verified_signer = proof_result.get("verificationMethodController")
        record_owner = proof_result.get("recordOwner")
        expected_version_id = (
            f"{proof_result.get('recordDid')}:{proof_result.get('versionHash')}"
        )
        if expected_version_id != item.get("@id"):
            errors.append(f"verification result is not bound to Assertion Version {item.get('@id')}")
            continue
        if proof_result.get("state") != "finalized":
            ignored += 1
            continue
        if (
            verified_signer != record_owner
            or verified_signer != item.get("assertedBy")
            or verified_signer not in allowed
        ):
            ignored += 1
            continue
        try:
            assertion_proof_created = parse_rfc3339(proof_result["proofCreatedAt"])
        except (KeyError, ValueError) as exc:
            errors.append(f"trusted assertion {item.get('@id')} has invalid proof time: {exc}")
            continue
        if assertion_proof_created <= case_proof_created:
            errors.append(
                f"trusted assertion {item.get('@id')} proof was not created after the Case proof"
            )
            continue
        candidates.append((item, proof_result))

    # Version succession comes only from the RWP version graph. For each
    # Assertion Record DID, select its unique finalized head among candidates.
    grouped: dict[str, list[tuple[dict, dict]]] = {}
    for item, proof_result in candidates:
        grouped.setdefault(proof_result["recordDid"], []).append((item, proof_result))

    selected_assertions: list[dict] = []
    for record_did, candidate_group in grouped.items():
        graph_versions = {
            result["versionHash"]: result
            for result in versions.values()
            if result.get("proofVerified") is True
            and result.get("state") == "finalized"
            and result.get("recordDid") == record_did
            and result.get("verificationMethodController") == result.get("recordOwner")
            and result.get("recordOwner") in allowed
        }
        candidate_by_hash = {
            result["versionHash"]: item for item, result in candidate_group
        }
        referenced_parents = {
            parent
            for result in graph_versions.values()
            for parent in result.get("parents", [])
        }
        missing_parents = referenced_parents - set(graph_versions)
        if missing_parents:
            errors.append(f"incomplete version graph for {record_did}: {sorted(missing_parents)}")
            continue
        heads = set(graph_versions) - referenced_parents
        if len(heads) != 1:
            errors.append(f"version graph for {record_did} has {len(heads)} finalized heads")
            continue
        head_hash = next(iter(heads))
        head_item = candidate_by_hash.get(head_hash)
        if head_item is None:
            errors.append(f"latest finalized Version for {record_did} was not supplied")
            continue
        selected_assertions.append(head_item)
        ignored += len(candidate_group) - 1

    selected["@graph"] = kept_non_assertions + selected_assertions
    return selected, errors, ignored


def remove_role_assertion(data: dict, predicate_suffix: str, object_id: str | None = None) -> None:
    full_predicate = str(WCE[predicate_suffix])
    case = case_node(data)
    kept: list[dict] = []
    removed_ids: set[str] = set()
    for item in data["@graph"]:
        if item.get("predicate") == full_predicate and (object_id is None or item.get("object") == object_id):
            removed_ids.add(item["@id"])
        else:
            kept.append(item)
    data["@graph"] = kept
    case["context"] = [value for value in case["context"] if value not in removed_ids]


def context_semantic_failures(graph: Graph, example_name: str) -> list[str]:
    failures: list[str] = []
    cases = list(graph.subjects(RDF.type, WCE.WorkClosureCaseRecord))
    if len(cases) != 1:
        failures.append(f"{example_name}: expected one WorkClosureCaseRecord, got {len(cases)}")
    for record_node in graph.subjects(RDF.type, RW.Record):
        if (record_node, RDF.type, PROV.Activity) in graph:
            failures.append(f"{example_name}: Record is also typed prov:Activity: {record_node}")
    for activity, _, plan in graph.triples((None, PROV.hadPlan, None)):
        if (activity, RDF.type, PROV.Association) not in graph:
            failures.append(f"{example_name}: prov:hadPlan subject is not a prov:Association: {activity} -> {plan}")
    for case in cases:
        if not list(graph.objects(case, WCE.trigger)):
            failures.append(f"{example_name}: trigger did not expand through the supplied context")
    for assertion in graph.subjects(RDF.type, WCE.RoleAssertionRecord):
        predicate = graph.value(assertion, WCE.predicate)
        if not isinstance(predicate, URIRef) or not str(predicate).startswith(str(WCE)):
            failures.append(f"{example_name}: predicate did not expand to an absolute wce IRI: {assertion}")
    return failures


def schema_errors(validator: Draft202012Validator, payload: dict) -> list[str]:
    return [error.message for error in validator.iter_errors(payload)]


def build_mutations(examples: dict[str, dict]) -> list[tuple[str, dict, Path]]:
    completed_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("01_"))
    partial_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("02_"))
    denied_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("03_"))
    aborted_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("04_"))
    completed = examples[completed_path.name]
    partial = examples[partial_path.name]
    denied = examples[denied_path.name]
    aborted = examples[aborted_path.name]
    mutations: list[tuple[str, dict, Path]] = []

    mutation = copy.deepcopy(completed)
    case_node(mutation).pop("trigger")
    mutations.append(("01_missing_trigger_field", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    case_node(mutation)["trigger"].append(case_node(mutation)["trigger"][0])
    mutations.append(("02_duplicate_trigger_link", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    case_node(mutation)["context"][0] = "did:rwp:example.org:soft-link-without-version"
    mutations.append(("03_soft_link_in_case_field", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    remove_role_assertion(mutation, "hasMandate")
    mutations.append(("04_missing_mandate_role_assertion", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    assertion_node = next(item for item in nodes(mutation, "wce:RoleAssertionRecord") if item["predicate"].endswith("hasAuthorization"))
    assertion_node["subject"] = "did:rwp:example.org:other-case"
    mutations.append(("05_role_assertion_wrong_subject", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    acceptance_id = node(mutation, type_name="wce:WorkAcceptanceRecord")["@id"]
    assertion_node = next(item for item in nodes(mutation, "wce:RoleAssertionRecord") if item["predicate"].endswith("hasClosure"))
    assertion_node["object"] = acceptance_id
    mutations.append(("06_role_assertion_object_in_wrong_field", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    nodes(mutation, "wce:RoleAssertionRecord")[0].pop("assertedBy")
    mutations.append(("07_role_assertion_missing_asserted_by", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    execution_assertion = next(item for item in nodes(mutation, "wce:RoleAssertionRecord") if item["predicate"].endswith("hasExecution"))
    execution_assertion["subject"] = "did:rwp:example.org:case-completed"
    mutations.append(("08_role_assertion_subject_is_soft_link", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    node(mutation, type_name="wce:AuthorizationDecisionRecord")["outcome"] = "deny"
    mutations.append(("09_completed_with_denied_authorization", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    node(mutation, type_name="wce:WorkAcceptanceRecord")["workAcceptanceStatus"] = "rejected"
    mutations.append(("10_completed_with_rejected_acceptance", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    case_node(mutation)["process"] = []
    mutations.append(("11_completed_without_execution", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    review_eval = next(item for item in nodes(mutation, "wce:CriterionEvaluationRecord") if item["criterion"] == "review-recorded")
    case_node(mutation)["decision"].remove(review_eval["@id"])
    mutations.append(("12_completed_missing_criterion_evaluation", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    nodes(mutation, "wce:CriterionEvaluationRecord")[0].pop("prov:wasDerivedFrom")
    mutations.append(("13_completed_evaluation_without_evidence", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    eval_record = nodes(mutation, "wce:CriterionEvaluationRecord")[0]
    eval_activity = node(mutation, identifier=eval_record["prov:wasGeneratedBy"]["@id"])
    eval_activity["prov:wasAssociatedWith"] = {"@id": "spiffe://example.org/agent/coding-01"}
    mutations.append(("14_completed_executor_self_evaluates", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    evidence = next(item for item in nodes(mutation, "wce:EvidenceRecord") if "evidence-test" in item["@id"])
    evidence["prov:wasAttributedTo"] = {"@id": "spiffe://example.org/agent/coding-01"}
    mutations.append(("15_completed_executor_produced_evidence", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    node(mutation, type_name="wce:ClosureRecord")["effectFinality"] = "provisional"
    mutations.append(("16_provisional_without_pending_action", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    node(mutation, type_name="wce:ObservedEffectRecord")["outcome"] = "unknown"
    mutations.append(("17_completed_with_unknown_effect", mutation, completed_path))

    mutation = copy.deepcopy(partial)
    obligation = node(mutation, type_name="wce:OpenObligationRecord")
    case_node(mutation)["result"].remove(obligation["@id"])
    remove_role_assertion(mutation, "hasOpenObligation", obligation["@id"])
    for evaluation in nodes(mutation, "wce:CriterionEvaluationRecord"):
        evaluation["outcome"] = "met"
    mutations.append(("18_partial_without_obligation_or_nonmet_criterion", mutation, partial_path))

    mutation = copy.deepcopy(denied)
    node(mutation, type_name="wce:ClosureRecord")["effectFinality"] = "settled"
    mutations.append(("19_denied_with_settled_finality", mutation, denied_path))

    mutation = copy.deepcopy(aborted)
    remove_role_assertion(mutation, "hasStopEvidence")
    mutations.append(("20_aborted_without_stop_evidence_assertion", mutation, aborted_path))

    mutation = copy.deepcopy(aborted)
    reverted = next(item for item in nodes(mutation, "wce:ObservedEffectRecord") if item["outcome"] == "reverted")
    reverted.pop("priorEffect")
    mutations.append(("21_reverted_effect_without_prior_applied_effect", mutation, aborted_path))

    mutation = copy.deepcopy(completed)
    node(mutation, type_name="wce:ObservedEffectRecord")["outcome"] = "inventedOutcome"
    mutations.append(("22_effect_with_arbitrary_outcome", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    case_node(mutation)["closureStatus"] = "completed"
    mutations.append(("23_business_status_added_to_caserecord", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    nodes(mutation, "wce:RoleAssertionRecord")[0]["assertedBy"] = "Alice"
    mutations.append(("24_asserting_agent_is_not_did", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    nodes(mutation, "wce:RoleAssertionRecord")[0]["assertedAt"] = "yesterday"
    mutations.append(("25_asserted_at_is_not_datetime", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    closure_assertion = next(
        item for item in nodes(mutation, "wce:RoleAssertionRecord")
        if item["predicate"].endswith("hasClosure")
    )
    closure_assertion["assertedBy"] = "did:rwp:attacker.example:issuer-1"
    mutations.append(("26_only_untrusted_assertion_cannot_satisfy_role", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    mutations.append(("27_assertion_proof_before_case_proof", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    mandate_id = node(mutation, type_name="wce:MandateRecord")["@id"]
    remove_role_assertion(mutation, "hasMandate")
    mutation["@graph"].append({
        "@id": FORGED_SIGNER_ASSERTION_ID,
        "@type": ["rw:Record", "wce:RoleAssertionRecord"],
        "subject": case_node(mutation)["@id"],
        "predicate": str(WCE.hasMandate),
        "object": mandate_id,
        "assertedBy": "did:rwp:example.org:agent-record-authority",
        "assertedAt": "2026-11-10T01:10:45Z",
    })
    mutations.append(("28_forged_asserted_by_does_not_match_verified_signer", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    mandate_id = node(mutation, type_name="wce:MandateRecord")["@id"]
    mutation["@graph"].append({
        "@id": AUTHORIZED_CONFLICT_ASSERTION_ID,
        "@type": ["rw:Record", "wce:RoleAssertionRecord"],
        "subject": case_node(mutation)["@id"],
        "predicate": str(WCE.hasClosure),
        "object": mandate_id,
        "assertedBy": "did:rwp:example.org:secondary-record-authority",
        "assertedAt": "2026-11-10T01:10:46Z",
    })
    mutations.append(("29_authorized_issuers_conflict_fails_closed", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    mutations.append(("30_case_proof_signer_is_not_case_owner", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    authorization_id = node(mutation, type_name="wce:AuthorizationDecisionRecord")["@id"]
    remove_role_assertion(mutation, "hasMandate")
    mutation["@graph"].append({
        "@id": WRONG_KIND_ASSERTION_ID,
        "@type": ["rw:Record", "wce:RoleAssertionRecord"],
        "subject": case_node(mutation)["@id"],
        "predicate": str(WCE.hasMandate),
        "object": authorization_id,
        "assertedBy": "did:rwp:example.org:agent-record-authority",
        "assertedAt": "2026-11-10T01:10:48Z",
    })
    mutations.append(("31_predicate_object_kind_is_wrong", mutation, completed_path))

    mutation = copy.deepcopy(completed)
    mandate_id = node(mutation, type_name="wce:MandateRecord")["@id"]
    mutation["@graph"].append({
        "@id": DUPLICATE_MANDATE_ASSERTION_ID,
        "@type": ["rw:Record", "wce:RoleAssertionRecord"],
        "subject": case_node(mutation)["@id"],
        "predicate": str(WCE.hasMandate),
        "object": mandate_id,
        "assertedBy": "did:rwp:example.org:secondary-record-authority",
        "assertedAt": "2026-11-10T01:10:47Z",
    })
    mutations.append(("32_singular_predicate_has_duplicate_assertions", mutation, completed_path))

    return mutations


def contradictory_untrusted_assertion(examples: dict[str, dict]) -> tuple[dict, Path]:
    completed_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("01_"))
    data = copy.deepcopy(examples[completed_path.name])
    case = case_node(data)
    mandate_id = node(data, type_name="wce:MandateRecord")["@id"]
    data["@graph"].append({
        "@id": UNTRUSTED_CONFLICT_ASSERTION_ID,
        "@type": ["rw:Record", "wce:RoleAssertionRecord"],
        "subject": case["@id"],
        "predicate": str(WCE.hasClosure),
        "object": mandate_id,
        "assertedBy": "did:rwp:attacker.example:issuer-1",
        "assertedAt": "2026-11-10T01:10:45Z"
    })
    return data, completed_path


def stale_authorized_duplicate(examples: dict[str, dict]) -> tuple[dict, Path]:
    completed_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("01_"))
    data = copy.deepcopy(examples[completed_path.name])
    original = next(
        item for item in nodes(data, "wce:RoleAssertionRecord")
        if item["predicate"].endswith("hasClosure")
    )
    stale = copy.deepcopy(original)
    stale["@id"] = STALE_DUPLICATE_ASSERTION_ID
    stale["assertedAt"] = "2026-11-10T01:10:38Z"
    data["@graph"].append(stale)
    return data, completed_path


def newer_mandate_version(examples: dict[str, dict]) -> tuple[dict, Path, str]:
    completed_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("01_"))
    data = copy.deepcopy(examples[completed_path.name])
    old_mandate = node(data, type_name="wce:MandateRecord")
    old_mandate_id = old_mandate["@id"]
    new_mandate = copy.deepcopy(old_mandate)
    new_mandate["@id"] = NEW_MANDATE_RECORD_ID
    data["@graph"].append(new_mandate)
    case = case_node(data)
    case["trigger"] = [
        NEW_MANDATE_RECORD_ID if value == old_mandate_id else value
        for value in case["trigger"]
    ]
    for activity in data["@graph"]:
        association = activity.get("prov:qualifiedAssociation")
        if isinstance(association, dict):
            plan = association.get("prov:hadPlan")
            if isinstance(plan, dict) and plan.get("@id") == old_mandate_id:
                plan["@id"] = NEW_MANDATE_RECORD_ID
    old_assertion = next(
        item for item in nodes(data, "wce:RoleAssertionRecord")
        if item["predicate"].endswith("hasMandate")
    )
    new_assertion = copy.deepcopy(old_assertion)
    new_assertion["@id"] = NEW_MANDATE_ASSERTION_ID
    new_assertion["object"] = NEW_MANDATE_RECORD_ID
    new_assertion["assertedAt"] = "2026-11-10T01:10:50Z"
    data["@graph"].append(new_assertion)
    return data, completed_path, old_assertion["@id"]


def untrusted_successor_version(examples: dict[str, dict]) -> tuple[dict, Path, str]:
    """Add an attacker-signed pseudo-successor under an existing Record DID."""
    completed_path = next(path for path in EXAMPLE_PATHS if path.name.startswith("01_"))
    data = copy.deepcopy(examples[completed_path.name])
    old_assertion = next(
        item for item in nodes(data, "wce:RoleAssertionRecord")
        if item["predicate"].endswith("hasMandate")
    )
    attack_assertion = copy.deepcopy(old_assertion)
    attack_assertion["@id"] = UNTRUSTED_SUCCESSOR_ASSERTION_ID
    attack_assertion["assertedBy"] = "did:rwp:attacker.example:issuer-1"
    attack_assertion["assertedAt"] = "2026-11-10T01:10:51Z"
    data["@graph"].append(attack_assertion)
    return data, completed_path, old_assertion["@id"]


def main() -> int:
    failures: list[str] = []
    subschema_content = load(SUBSCHEMA_PATH)
    role_subschema_content = load(ROLE_SUBSCHEMA_PATH)
    trust_policy = load(TRUST_POLICY_PATH)
    verification_fixture = load(VERIFICATION_FIXTURE_PATH)
    root_case_schema = root_json_schema(ROOT_CASE_PATH)
    root_assertion_schema = root_json_schema(ROOT_ASSERTION_PATH)
    app_schema = subschema_content["jsonSchema"]
    role_app_schema = role_subschema_content["jsonSchema"]
    format_checker = FormatChecker()
    root_case_validator = Draft202012Validator(root_case_schema, format_checker=format_checker)
    root_assertion_validator = Draft202012Validator(root_assertion_schema, format_checker=format_checker)
    app_validator = Draft202012Validator(app_schema, format_checker=format_checker)
    role_app_validator = Draft202012Validator(role_app_schema, format_checker=format_checker)

    if subschema_content["rwpSchemaVersion"] != "0.0.16":
        failures.append("SchemaRecord content does not identify RWP 0.0.16")
    if subschema_content["subClassOf"] != ROOT_CASE_HARD_LINK:
        failures.append("subClassOf does not hard-link the RWP 0.0.16 Root CaseRecord Schema")
    if subschema_content["signaturePolicy"] != "owner":
        failures.append("subschema weakens the Root CaseRecord owner signature policy")
    if set(subschema_content["allowedStates"]) != {"draft", "finalized"}:
        failures.append("subschema does not retain the Root CaseRecord states")
    if role_subschema_content["signaturePolicy"] != "owner":
        failures.append("role assertion subschema weakens the Root AssertionRecord owner signature policy")
    if role_subschema_content["subClassOf"] != ROOT_ASSERTION_HARD_LINK:
        failures.append("role assertion subClassOf does not hard-link the RWP 0.0.16 Root AssertionRecord Schema")
    print(f"BASELINE rootCase={ROOT_CASE_VERSION} rootAssertion={ROOT_ASSERTION_VERSION}")

    examples: dict[str, dict] = {path.name: load(path) for path in EXAMPLE_PATHS}
    for path in EXAMPLE_PATHS:
        data = examples[path.name]
        payload = case_payload(data)
        root_errors = schema_errors(root_case_validator, payload)
        app_errors = schema_errors(app_validator, payload)
        selected_data, policy_errors, ignored = select_trusted_assertions(
            data, trust_policy, verification_fixture
        )
        shacl_ok, report, graph = validate_shacl(selected_data, path)
        assertion_errors: list[str] = []
        role_assertion_errors: list[str] = []
        for assertion_node in nodes(data, "wce:RoleAssertionRecord"):
            payload = assertion_payload(assertion_node)
            assertion_errors.extend(schema_errors(root_assertion_validator, payload))
            role_assertion_errors.extend(schema_errors(role_app_validator, payload))
        semantic_errors = context_semantic_failures(graph, path.name)
        passed = (
            not root_errors and not app_errors and not assertion_errors
            and not role_assertion_errors and not policy_errors
            and not semantic_errors and shacl_ok
        )
        print(
            f"POSITIVE {path.name}: pass={passed} root={not root_errors} "
            f"subschema={not app_errors} rootAssertions={not assertion_errors} "
            f"roleSubschema={not role_assertion_errors} policy={not policy_errors} "
            f"ignored={ignored} shacl={shacl_ok} triples={len(graph)}"
        )
        if not passed:
            failures.append(
                f"positive failed {path.name}: root={root_errors} app={app_errors} "
                f"assertions={assertion_errors} roleAssertions={role_assertion_errors} "
                f"policy={policy_errors} semantics={semantic_errors}\n{report}"
            )

    NEGATIVE_DIR.mkdir(parents=True, exist_ok=True)
    for old in NEGATIVE_DIR.glob("*.jsonld"):
        old.unlink()
    mutations = build_mutations(examples)
    for name, data, base_path in mutations:
        output_path = NEGATIVE_DIR / f"{name}.jsonld"
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        payload = case_payload(data)
        root_ok = not schema_errors(root_case_validator, payload)
        app_ok = not schema_errors(app_validator, payload)
        root_assertions_ok = True
        role_assertions_ok = True
        for assertion_node in nodes(data, "wce:RoleAssertionRecord"):
            assertion_data = assertion_payload(assertion_node)
            root_assertions_ok = root_assertions_ok and not schema_errors(root_assertion_validator, assertion_data)
            role_assertions_ok = role_assertions_ok and not schema_errors(role_app_validator, assertion_data)
        mutation_verification = copy.deepcopy(verification_fixture)
        if name == "27_assertion_proof_before_case_proof":
            assertion_id = nodes(data, "wce:RoleAssertionRecord")[0]["@id"]
            mutation_verification["versions"][assertion_id]["proofCreatedAt"] = (
                "2026-11-10T01:10:34Z"
            )
        if name == "30_case_proof_signer_is_not_case_owner":
            case_id = case_node(data)["@id"]
            mutation_verification["versions"][case_id][
                "verificationMethodController"
            ] = "did:rwp:attacker.example:issuer-1"
        selected_data, policy_errors, ignored = select_trusted_assertions(
            data, trust_policy, mutation_verification
        )
        if name == "25_asserted_at_is_not_datetime":
            # JSON Schema format checking is the intended rejection layer. Avoid
            # asking the RDF parser to coerce a knowingly invalid xsd:dateTime.
            shacl_ok = True
            shacl_label = "skipped-after-format-rejection"
        else:
            shacl_ok, _, _ = validate_shacl(selected_data, base_path)
            shacl_label = str(shacl_ok)
        policy_ok = not policy_errors
        rejected = not (
            root_ok and app_ok and root_assertions_ok and role_assertions_ok
            and policy_ok and shacl_ok
        )
        print(
            f"NEGATIVE {name}: rejected={rejected} root={root_ok} subschema={app_ok} "
            f"rootAssertions={root_assertions_ok} roleSubschema={role_assertions_ok} "
            f"policy={policy_ok} ignored={ignored} shacl={shacl_label}"
        )
        if not rejected:
            failures.append(f"negative mutation accepted: {name}")

    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    for old in SECURITY_DIR.glob("*.jsonld"):
        old.unlink()
    attack_data, attack_base = contradictory_untrusted_assertion(examples)
    attack_path = SECURITY_DIR / "01_untrusted_contradictory_assertion_is_ignored.jsonld"
    attack_path.write_text(
        json.dumps(attack_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    attack_schema_ok = True
    for assertion_node in nodes(attack_data, "wce:RoleAssertionRecord"):
        payload = assertion_payload(assertion_node)
        attack_schema_ok = attack_schema_ok and not schema_errors(root_assertion_validator, payload)
        attack_schema_ok = attack_schema_ok and not schema_errors(role_app_validator, payload)
    selected_attack, attack_policy_errors, attack_ignored = select_trusted_assertions(
        attack_data, trust_policy, verification_fixture
    )
    attack_shacl_ok, _, _ = validate_shacl(selected_attack, attack_base)
    attack_passed = (
        attack_schema_ok and not attack_policy_errors
        and attack_ignored == 1 and attack_shacl_ok
    )
    print(
        "RESILIENCE 01_untrusted_contradictory_assertion_is_ignored: "
        f"pass={attack_passed} rawAssertionsSchema={attack_schema_ok} "
        f"ignored={attack_ignored} selectedShacl={attack_shacl_ok}"
    )
    if not attack_passed:
        failures.append("untrusted contradictory assertion was not safely ignored")

    stale_data, stale_base = stale_authorized_duplicate(examples)
    stale_path = SECURITY_DIR / "02_stale_authorized_duplicate_is_ignored.jsonld"
    stale_path.write_text(
        json.dumps(stale_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    stale_schema_ok = True
    for assertion_node in nodes(stale_data, "wce:RoleAssertionRecord"):
        payload = assertion_payload(assertion_node)
        stale_schema_ok = stale_schema_ok and not schema_errors(root_assertion_validator, payload)
        stale_schema_ok = stale_schema_ok and not schema_errors(role_app_validator, payload)
    selected_stale, stale_policy_errors, stale_ignored = select_trusted_assertions(
        stale_data, trust_policy, verification_fixture
    )
    stale_shacl_ok, _, _ = validate_shacl(selected_stale, stale_base)
    stale_passed = (
        stale_schema_ok and not stale_policy_errors
        and stale_ignored == 1 and stale_shacl_ok
    )
    print(
        "RESILIENCE 02_stale_authorized_duplicate_is_ignored: "
        f"pass={stale_passed} rawAssertionsSchema={stale_schema_ok} "
        f"ignored={stale_ignored} selectedShacl={stale_shacl_ok}"
    )
    if not stale_passed:
        failures.append("stale authorized duplicate was not deterministically superseded")

    revision_data, revision_base, old_assertion_id = newer_mandate_version(examples)
    revision_path = SECURITY_DIR / "03_newer_version_changes_object_and_supersedes_old.jsonld"
    revision_path.write_text(
        json.dumps(revision_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    revision_verification = copy.deepcopy(verification_fixture)
    old_version_hash = revision_verification["versions"][old_assertion_id]["versionHash"]
    revision_verification["versions"][NEW_MANDATE_ASSERTION_ID] = {
        "proofVerified": True,
        "recordDid": NEW_MANDATE_ASSERTION_ID.rsplit(":sha256:", 1)[0],
        "versionHash": "sha256:" + "b" * 64,
        "state": "finalized",
        "parents": [old_version_hash],
        "recordOwner": "did:rwp:example.org:agent-record-authority",
        "verificationMethodController": "did:rwp:example.org:agent-record-authority",
        "proofCreatedAt": "2026-11-10T01:10:50Z",
    }
    revision_schema_ok = True
    for assertion_node in nodes(revision_data, "wce:RoleAssertionRecord"):
        payload = assertion_payload(assertion_node)
        revision_schema_ok = revision_schema_ok and not schema_errors(root_assertion_validator, payload)
        revision_schema_ok = revision_schema_ok and not schema_errors(role_app_validator, payload)
    selected_revision, revision_policy_errors, revision_ignored = select_trusted_assertions(
        revision_data, trust_policy, revision_verification
    )
    revision_shacl_ok, _, _ = validate_shacl(selected_revision, revision_base)
    revision_passed = (
        revision_schema_ok and not revision_policy_errors
        and revision_ignored == 1 and revision_shacl_ok
    )
    print(
        "RESILIENCE 03_newer_version_changes_object_and_supersedes_old: "
        f"pass={revision_passed} rawAssertionsSchema={revision_schema_ok} "
        f"ignored={revision_ignored} selectedShacl={revision_shacl_ok}"
    )
    if not revision_passed:
        failures.append("version-graph successor did not supersede the old Assertion Version")

    untrusted_successor_data, untrusted_successor_base, old_assertion_id = (
        untrusted_successor_version(examples)
    )
    untrusted_successor_path = (
        SECURITY_DIR / "04_untrusted_pseudo_successor_cannot_change_version_head.jsonld"
    )
    untrusted_successor_path.write_text(
        json.dumps(untrusted_successor_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    untrusted_successor_verification = copy.deepcopy(verification_fixture)
    old_version_hash = untrusted_successor_verification["versions"][old_assertion_id][
        "versionHash"
    ]
    untrusted_successor_verification["versions"][UNTRUSTED_SUCCESSOR_ASSERTION_ID] = {
        "proofVerified": True,
        "recordDid": UNTRUSTED_SUCCESSOR_ASSERTION_ID.rsplit(":sha256:", 1)[0],
        "versionHash": "sha256:" + "c" * 64,
        "state": "finalized",
        "parents": [old_version_hash],
        "recordOwner": "did:rwp:example.org:agent-record-authority",
        "verificationMethodController": "did:rwp:attacker.example:issuer-1",
        "proofCreatedAt": "2026-11-10T01:10:51Z",
    }
    untrusted_successor_schema_ok = True
    for assertion_node in nodes(untrusted_successor_data, "wce:RoleAssertionRecord"):
        payload = assertion_payload(assertion_node)
        untrusted_successor_schema_ok = (
            untrusted_successor_schema_ok
            and not schema_errors(root_assertion_validator, payload)
            and not schema_errors(role_app_validator, payload)
        )
    selected_untrusted_successor, untrusted_successor_policy_errors, untrusted_ignored = (
        select_trusted_assertions(
            untrusted_successor_data,
            trust_policy,
            untrusted_successor_verification,
        )
    )
    untrusted_successor_shacl_ok, _, _ = validate_shacl(
        selected_untrusted_successor, untrusted_successor_base
    )
    untrusted_successor_passed = (
        untrusted_successor_schema_ok
        and not untrusted_successor_policy_errors
        and untrusted_ignored == 1
        and untrusted_successor_shacl_ok
    )
    print(
        "RESILIENCE 04_untrusted_pseudo_successor_cannot_change_version_head: "
        f"pass={untrusted_successor_passed} "
        f"rawAssertionsSchema={untrusted_successor_schema_ok} "
        f"ignored={untrusted_ignored} selectedShacl={untrusted_successor_shacl_ok}"
    )
    if not untrusted_successor_passed:
        failures.append("untrusted pseudo-successor changed the trusted version head")

    if failures:
        print("RESULT: FAIL")
        for failure in failures:
            print(failure)
        return 1

    print(
        f"RESULT: PASS (positive={len(EXAMPLE_PATHS)}, "
        f"negative={len(mutations)}, resilience=4)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
