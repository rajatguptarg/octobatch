# TASK-008 CLI Parity

## Objective
Provide CLI commands that mirror UI flows for apply, preview, publish, and status using API authentication.

## Commands
- `octobatch apply -f spec.yaml` → POST spec and trigger apply/selection run.
- `octobatch preview --campaign <id> --spec-version <n>` → trigger preview run and stream status.
- `octobatch publish --campaign <id> --run <preview_run_id>` → trigger publish for ready repos.
- `octobatch status --campaign <id>` → show runs, counts, and open changesets.

## Configuration
- Config file `~/.config/octobatch/config.yaml` with `apiBaseUrl`, `githubAppId`, `clientId`, `clientSecret`, and optional `accessToken`.
- CLI obtains token via OAuth device flow or cached installation token; supports GHES by honoring `apiBaseUrl`.

## Output
- Human-readable tables and JSON output (`--json`) including campaign/run IDs for scripting.
- Progress bars for preview/publish and links to logs/patch artifacts.

## Tests
- Integration tests against staging API to verify command outputs and authentication fallback.
- Golden snapshot tests for JSON output to ensure stability.

## Rollback
- Disable `publish` subcommand via feature flag when API publish is paused.
