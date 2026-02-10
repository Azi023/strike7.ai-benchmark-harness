# Repository Guidelines

## Project Structure & Module Organization
- `benchmarks/`: Core benchmark environments (`S7BEN-<CATEGORY>-<ID>`), each with `docker-compose.yml`, `Makefile`, `benchmark.yaml`, and app code under `app/` (or multiple service folders for complex scenarios).
- `dashboard/`: Flask-based control plane and API (`app.py`, `api/`, `config/`, `templates/`, `static/`).
- `dashboard/tests/`: Pytest + Playwright end-to-end tests for dashboard UI/API workflows.
- `scripts/`: Operational helpers for container lifecycle, benchmark validation, and migration utilities.
- `docs/`: Implementation notes, deployment guides, and phase reports.

## Build, Test, and Development Commands
- Start one benchmark:
  ```bash
  cd benchmarks/S7BEN-EASY-001 && make up && make test && make down
  ```
- Manage containers centrally:
  ```bash
  ./scripts/manage-containers.sh up S7BEN-EASY-001
  ./scripts/manage-containers.sh stop-all
  ```
- Run dashboard locally:
  ```bash
  cd dashboard && pip install -r requirements.txt && python app.py
  ```
- Run dashboard E2E tests:
  ```bash
  cd dashboard/tests && python -m pytest test_e2e_playwright.py -v
  ```

## Coding Style & Naming Conventions
- Python: follow PEP 8, 4-space indentation, `snake_case` for functions/modules, `PascalCase` for classes.
- Shell: keep scripts POSIX/Bash-friendly, executable, and rooted via repo path detection (`SCRIPT_DIR`/`REPO_ROOT`).
- Benchmark IDs and directories use `S7BEN-<CATEGORY>-<3-digit>` (for example `S7BEN-HARD-018`).
- Keep changes scoped: benchmark-specific edits should stay inside that benchmark directory unless intentionally shared.

## Testing Guidelines
- Prefer local validation at the smallest scope first: benchmark-level `make test`, then broader script/test runs.
- Dashboard tests use `pytest` discovery (`test_*.py`, `Test*`, `test_*`) configured in `dashboard/tests/pytest.ini`.
- Use markers (`smoke`, `container`, `ui`, `api`, `slow`) to target runs when iterating.

## Commit & Pull Request Guidelines
- Follow Conventional Commit prefixes seen in history: `fix:`, `feat:`, `docs:`, `ci:`, `chore:`.
- Keep commit messages imperative and specific (for example `fix: correct container health polling timeout`).
- PRs should include:
  - Summary of affected benchmarks/components
  - Reproduction and verification steps (commands run)
  - Related issue/task reference
  - Screenshots/GIFs for dashboard UI changes

## Security & Configuration Tips
- Do not commit real secrets, tokens, or private endpoints.
- Prefer environment-based configuration and keep local overrides out of version control.
- Treat benchmark vulnerabilities as intentional test fixtures; avoid “hardening” challenge logic unless the benchmark spec requires it.

## Recheck & Continuation Workflow
- Start every debugging session by reading `STRIKE7_PROJECT_SUMMARY.md` before scanning code.
- Use targeted scans only (no full-repo sweep): `dashboard/app.py`, `dashboard/api/*.py`, `dashboard/safety_daemon.py`, `dashboard/static/js/dashboard.js`, `dashboard/templates/index.html`, `dashboard/data/benchmarks.json`, and benchmark `docker-compose.yml` files.
- Note current local reality: there is no `mcp-server/index.js`, `dashboard/config/settings.py`, or `dashboard/static/js/main.js`; use `dashboard/strike7_mcp_server.py`, `dashboard/config/settings.yaml`, and `dashboard/static/js/dashboard.js`.
- Verify container state with:
  ```bash
  curl -s http://localhost:5500/api/containers/status | jq
  docker ps --format '{{.Names}}\t{{.Status}}'
  ```
- For VPS checks (read-only): `ssh root@139.59.80.137`, then inspect `docker ps`, `systemctl status strike7-dashboard`, and `journalctl -u strike7-dashboard -n 100`.
- Keep fixes minimal and ordered: diagnose one issue, patch one issue, run smoke checks, then move to the next issue.
