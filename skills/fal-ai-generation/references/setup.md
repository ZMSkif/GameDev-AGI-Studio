# Connect fal.ai in another project

This skill ships inside the GameDev Studio plugin; nothing needs copying. Each
person uses their own fal account. Creating the account and the key, and any
payment, is done by that person (DEC-009, DEC-130).

## Account and MCP

Create your own API key in the [fal dashboard](https://fal.ai/dashboard/keys).
Use the inference/API scope unless your task needs account administration.
Connect a Streamable HTTP MCP server at `https://mcp.fal.ai/mcp`, with an
`Authorization` header whose value is `Bearer <your key>`.

Use your client's environment/header support so a real key is never committed.
For Claude Code, a project `.mcp.json` can reference an environment variable
such as `${FAL_MCP_AUTHORIZATION}` (holding the complete `Bearer` value); Codex's
project config uses `env_http_headers`. The terminal must load the variable
before starting its agent; a root `.env` is not automatically read by every MCP
client. Merge into an existing config instead of replacing its servers, and keep
`.env` in `.gitignore`.

Do not confuse `https://docs.fal.ai/mcp`, a documentation connection, with the
generation MCP. Client support changes; follow the current
[official connection guide](https://fal.ai/docs/documentation/setting-up/mcp).
Confirm tools such as `get_model_schema` in the intended agent session. A config
file alone does not prove a live connection. Listing tools or reading a schema
does not require creating an image.

## Optional Python helper

Use Python 3.10+ and install the small dependency file from this skill directory.
On Windows:

```text
python -m pip install -r scripts/requirements.txt
python scripts/fal_job.py --help
```

On macOS or Linux, `python` may not exist and Homebrew's Python refuses global
`pip install`; the macOS system `/usr/bin/python3` is 3.9. Use a virtual
environment created with Python 3.10+ (for example Homebrew's `python3`):

```text
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
.venv/bin/python scripts/fal_job.py --help
```

The commands below write `python`; on macOS or Linux, use `.venv/bin/python`.

Set `FAL_KEY` in the environment or in your project's ignored `.env`. The helper
also understands the legacy `FALAI_KEY`.
Choose a file explicitly with `--env /path/to/project/.env`; otherwise only the
current working directory's `.env` is considered. Credentials are never printed.

```text
python scripts/fal_job.py submit --endpoint fal-ai/nano-banana-pro --input examples/concept.json --out output/concept --dry-run
```

The dry run does not import the SDK, upload files, contact fal or create a paid
job. An actual `submit` uses account credits and needs `--owner-approval` with the
GitHub link where the owner approved the batch. The examples do not include keys.

Keep job receipts, reference uploads and generated media in the recipient's own
task directory. When sharing the skill again, share its clean source folder,
not a working directory containing `.env` or private receipts.
