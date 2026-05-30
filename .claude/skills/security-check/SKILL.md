---
name: security-check
description: Use when the user asks for a security review, hardening pass, or risk scan for this Python MCP server. Focus on secrets exposure, unsafe URL construction, upstream auth/token handling, input trust boundaries, logging of sensitive data, and tool input validation.
---

# Security Check

Use this skill for a focused security pass on the MCP server.

## Scope

- secret leakage in code, config, or logs (tokens, API keys, credentials)
- unsafe URL construction against the upstream API (path traversal, host smuggling)
- upstream auth header / token handling and lifecycle
- LLM-controlled tool input as an untrusted boundary — anything an LLM passes is user-controlled
- error messages or tool return values exposing internal details (stack traces, raw upstream errors with hostnames, internal IDs)
- environment variable handling and `.env` discipline

## Workflow

1. Identify every input that originates outside the process: tool parameters from the MCP client, env vars, upstream responses.
2. Trace how those values flow through `tools.py` → `client.py` → upstream → back to the LLM client.
3. Confirm tool parameters are validated by Pydantic / type hints before being interpolated into URLs, headers, or query strings.
4. Verify `httpx` requests build paths via `client.get(f"/employees/{id}")` only after validating `id`; never concatenate raw user input into a base URL.
5. Check that auth tokens are read once from config and never logged or echoed back in tool responses.
6. Report concrete risks with exploit shape or failure mode.

## Rules

- Treat **every tool argument** as untrusted input — an LLM may pass arbitrary values, including prompt-injected content.
- No secrets in logs at any level; redact tokens before logging request/response bodies.
- Never include raw `httpx.Response` text in tool return values when it might contain upstream error details, internal hostnames, or stack traces.
- No `eval`, `exec`, `subprocess.run(shell=True)`, or dynamic import driven by tool input.
- Validate config at startup; refuse to boot with placeholder/empty secrets.
- Recommend the smallest safe fix that reduces exposure.
