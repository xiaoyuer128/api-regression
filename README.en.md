# API Regression

[简体中文](README.md) | [English](README.en.md)

Generate reviewable GET contract plans from OpenAPI, run explicitly approved local checks, and export pytest tests. Python 3.10+.

```console
python -m pip install -r requirements.txt
python scripts/api_regression.py --spec examples/openapi.json
python scripts/api_regression.py --spec examples/openapi.json --export-pytest test_generated.py
python -m unittest discover -s tests -v
python evals/run_rounds.py
```

To execute against a separately started read-only service, add `--base-url http://127.0.0.1:8000 --approve-read-only`. Only HTTP IPv4 loopback is supported. No redirects/proxies; timeout defaults to 3 seconds (maximum 30), at most 100 cases and 1 MiB response reads.

Supports OpenAPI 3.0.0–3.0.3 JSON, explicit numeric response statuses, scalar query/path examples/enums/defaults, parameter overrides, missing-required-query exploration and a restricted JSON response schema subset. Unsupported features are skipped. No authentication, mutation methods, remote references, YAML, complex parameter serialization, nullable/composition/format schemas or full OpenAPI validation.

Exploratory requests are observed, never asserted to return an invented 400 status. A documented status match does not establish business correctness. Generated pytest requires API_REGRESSION_SCRIPT, API_REGRESSION_BASE_URL and API_REGRESSION_APPROVED=1; exploration is skipped. Run `python -m pytest --rootdir . test_generated.py -q`.

Exit 0 means no executed failures, including generation-only or all-skipped runs; 1 failed/error; 2 input/configuration error. Inspect actual counts. Reports omit response bodies/query values but paths may contain identifiers.

See [recorded test rounds](evals/results.json), [evaluation limitations](evals/README.md) and [development workflow](docs/DEVELOPMENT.md). Tests use temporary local HTTP services and execute generated pytest. No independent Agent benchmark, exhaustive hostile-input/resource analysis or production endpoint validation is claimed. Python's default JSON parser remains in use; extreme numbers and duplicate keys need future hardening. Intended for trusted local services. Repository: https://github.com/xiaoyuer128/api-regression .
