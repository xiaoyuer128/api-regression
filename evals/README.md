# Evaluation checkpoint

Three local rounds run `unittest discover`, including exported pytest executed as a subprocess against a real temporary loopback HTTP server. See results.json for actual outputs. Reproduce with `python evals/run_rounds.py`.

Covered: plan generation, unsupported operation handling, version checks, read-only approval, URL restrictions, redirects, success and status mismatch, scalar parameter generation, parameter inheritance, missing query exploration, response schema mismatch, timeout argument bounds, case cap and exported pytest.

Not evaluated: independent Agent behavior, production targets, auth, hostile content, exhaustive malformed OAS, slow-stream total deadline, Unicode/numeric corner cases, all possible redirects/statuses. Repeated rounds are stability checks, not independent samples or extra coverage. No accuracy gain claimed.

Suggested future Agent tasks: preserve documented expectations without guessing status; explain unsupported features; require explicit authorization before request execution; never call all-skipped runs a pass. Store actual traces separately from deterministic tests.
