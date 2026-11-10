# Optional backend assessment

Decision: retain the small deterministic runner for reviewed examples. Consider Schemathesis for broad schema support, property-based generation and stateful testing. It is not currently integrated or required.

Before integration: pin a tested version; inspect the installed version's CLI help and official documentation; restrict execution to explicit approved environments; define mutation/auth permissions; map unsupported, skipped and failure results without hiding gaps; redact artifacts and reproduce a known bug. Do not assume the current local GET-only approval authorizes fuzzing or write operations.

Official source: https://github.com/schemathesis/schemathesis . No Schemathesis runtime experiment has been performed here. This is an architecture assessment, not a working adapter.
