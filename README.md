# Work Closure application profile for RecordWeb RWP 0.0.16

This repository contains a non-normative, application-specific experiment for representing finite work closure with RecordWeb CaseRecords and AssertionRecords. It is not an RWP extension and does not claim RWP conformance.

Baseline:

- RWP 0.0.16, commit `1823691d1c4bd097e2d911354db55f9011746815`
- Root CaseRecord Schema versionHash `sha256:3622a965594d5b9970f2e5c92c66f878ccfb5a972f61ac3b46ef41dbfa1116e9`
- Root AssertionRecord Schema versionHash `sha256:fe06970166343fd7ca1c7c948617c7f1869d2273727a66333aa459cd7a123ef4`

## Contents

- field mapping and Case Profile
- two application subschemas
- provisional predicate declarations and JSON-LD context
- SHACL Core and SHACL-SPARQL constraints
- authenticated assertion-selection policy and simulated proof-verifier fixture
- four positive projections, 32 negative cases and four resilience cases
- validator, generator, hash-pinned dependency lock and author-run evidence

Author-run result, including SHACL:

```text
RESULT: PASS (positive=4, negative=32, resilience=4)
```

## Reproduction prerequisite

Third-party RecordWeb source snapshots are deliberately not redistributed. Before running the validator, create `rwp_0_0_16_primary_sources/` and retrieve these two records from the RecordWeb resolver:

- `root-caserecord_3622a965.json` from `https://recordweb.org/resolver/records/d2d14675-50c9-463d-b564-1ea50644c836/schema-root-caserecord`
  - expected file SHA-256: `97737ba379ef3b99ac6dfbde763107b0d0a1e26e47cd9b700026f88647fae203`
- `root-assertionrecord_fe069701.json` from `https://recordweb.org/resolver/records/d2d14675-50c9-463d-b564-1ea50644c836/schema-root-assertionrecord`
  - expected file SHA-256: `5db2c6669eede4fa8660e6269079bf36452182ff2899fb865ae5ecd0e88b8fdc`

Stop if either hash differs. The resolver URLs are not asserted to be immutable.

Then run:

```bash
python3 -m venv .venv-rwp016
.venv-rwp016/bin/pip install --require-hashes \
  -r requirements-rwp-0.0.16-validation-draft-0.9-hashed.txt
.venv-rwp016/bin/python -I validate_rwp_0_0_16_adapter_v0_9.py
```

The supplied wheel hashes are for macOS arm64 and Python 3.11. Other platforms must create and review their own complete hash set.

## Important limits

- Example DIDs and hashes are illustrative and are not resolvable.
- Proof-verification data is simulated; no real cryptographic proof is supplied.
- The SHACL log is an author-run record, not an independent reviewer reproduction.
- The `wce:` vocabulary is provisional and is not published as a resolvable vocabulary.
- Conflicting authorized AssertionRecords can block validation until corrected or withdrawn.
- Passing the tests is not a claim of authority, evidence truth, legal effect or RWP conformance.

Author: Shunjiro Ono, Independent Researcher, Japan  
Version: draft-0.9, 2026-11-10

## License

See [LICENSES.md](LICENSES.md). Software, schemas, JSON-LD, SHACL and machine-readable fixtures are Apache-2.0. Original explanatory documentation is CC BY 4.0.
