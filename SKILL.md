---
name: api-regression
description: Generate reviewable HTTP regression cases from an OpenAPI 3.0 document and execute approved cases against a specified test environment. Use for API contract regression, boundary inputs and reproducible failures.
---

# API Regression

## Contract and scope

Obtain an OpenAPI document, explicit test base URL and authentication input method. Start with OpenAPI 3.0 JSON; reject unsupported features rather than guessing their semantics. Separate documented expectations from exploratory cases. Never infer an exact error status where the contract does not specify it.

## Workflow

1. Inspect paths, operations, required parameters, request schemas and documented responses.
2. Produce a reviewable case manifest with operation, method, URL path, inputs, expected status/schema, expectation source and side-effect classification. Redact authentication values from artifacts.
3. Generate runnable tests only for supported contracts. Default execution to approved read-only operations in the explicit test environment. Require explicit task authorization before state-changing operations; do not assume GET endpoints are harmless when their documented behavior says otherwise.
4. Apply request timeouts, bound case counts and disable redirects by default. Do not fetch remote OpenAPI references automatically.
5. Report passed, failed, skipped and unsupported cases separately. Preserve redacted request details and response evidence sufficient for reproduction. Do not claim unexecuted cases passed.

## Supported implementation

Run `python scripts/api_regression.py --spec examples/openapi.json` to generate a plan. Add `--export-pytest test_generated.py` to export without requests. After explicit read-only authorization add `--base-url http://127.0.0.1:PORT --approve-read-only` to execute. Only GET, scalar query/path parameters with explicit valid samples, numeric status codes and a restricted JSON body schema subset are implemented. See README.md for exact limits. Missing-required-query cases are exploratory observations, not invented status assertions.

Read summary and skipped cases before concluding. Exit 0 can mean no tests executed. Generated pytest requires explicit approval and environment settings documented in README.md. See evals/README.md for tested behavior and remaining gaps; script tests do not establish Agent compliance.
