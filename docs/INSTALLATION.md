# v0.1.0 installation and demo / 安装与演示

License: MIT, see LICENSE. This is an early release with the limitations in README.

## Install

Copy the complete `api-regression` folder into the host's supported skills directory, preserving SKILL.md, scripts, examples and references. Install requirements.txt when present; test-failure-triage runtime uses the standard library (requirements-dev.txt is for tests).

For skills.sh the documented source command is `npx skills add xiaoyuer128/api-regression`. Platform listing/host discovery is separate from script execution. Do not assume all marketplaces deliver executable supporting files.

## Complete demo

From any working directory run `python /absolute/path/to/api-regression/scripts/demo.py`. It resolves bundled assets relative to its installation path and prints actual results. API demo starts and closes its own local read-only service, including a deliberate response regression. Output-validation demo uses supplied candidates, not model-generated repairs. Triage demo retains unconfirmed root cause.

## Verification and version

Run `python scripts/demo.py` from the installed folder. See installation-check.json for isolated layout execution. It verifies packaged files and script behavior, not actual marketplace indexing or automatic Agent activation. VERSION fixes the release label; publish the exact commit SHA as immutable installation reference. ZIP SHA-256 values are recorded in the parent release index. Do not install unreviewed updates merely because the label matches.
