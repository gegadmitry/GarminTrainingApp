# Local Garmin MCP

This project uses the community `Taxuspt/garmin_mcp` server through `uvx` and
the stdio transport. Python 3.12 and `uv` are required.

## One-time authentication

Choose a token directory outside this repository and outside synced folders.
The helper creates it with owner-only permissions and never accepts credentials
from a tracked file:

```sh
export GARMINTOKENS="$HOME/.garminconnect"
scripts/garmin_mcp_auth.sh
```

The command prompts for Garmin credentials and MFA when needed. Tokens are
stored in `GARMINTOKENS`; email and password are not stored in the MCP client
configuration. Re-authenticate when the upstream token expires.

## MCP client configuration

Use [config/garmin-mcp.json](../config/garmin-mcp.json) in a local MCP client.
It starts the server with:

```text
uvx --python 3.12 --from git+https://github.com/Taxuspt/garmin_mcp garmin-mcp
```

`GARMIN_ENABLED_TOOLS` is an explicit read-only allowlist covering recent
activities, activity details and splits, sleep, and stress. Do not remove the
allowlist or add write-capable tools such as workout upload, scheduling, edit,
or delete operations.

## Smoke tests

Run the credential-free configuration check at any time:

```sh
python3 scripts/garmin_mcp_smoke.py --check-config
```

After authentication, run the live stdio smoke test. It calls `get_activities`
and prints the returned recent activities:

```sh
python3 scripts/garmin_mcp_smoke.py
```

The live test fails clearly when the token directory is missing. It never
prints credentials or writes Garmin data.