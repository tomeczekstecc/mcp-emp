---
name: security-check
description: Use when the user asks for a security review, hardening pass, or risk scan for frontend code in this repository. Focus on secrets exposure, unsafe rendering, auth/session handling, input trust boundaries, browser storage, and integration assumptions.
---

# Security Check

Use this skill for a focused frontend security pass.

## Scope

- secret leakage in code or config
- unsafe HTML rendering and injection paths
- auth, session, token, and cookie handling
- client-side trust of server or user input
- local storage, query params, and error message exposure

## Workflow

1. Identify any user-controlled or backend-controlled inputs.
2. Trace how those values are rendered, stored, and sent.
3. Look for unsafe browser APIs, over-trusting client logic, and sensitive data exposure.
4. Report concrete risks with exploit shape or failure mode.

## Rules

- Prefer real risk over generic OWASP checklists.
- Treat `dangerouslySetInnerHTML`, URL construction, and token handling as high-attention areas.
- Call out when a frontend decision assumes Laravel will enforce safety server-side.
- Recommend the smallest safe fix that reduces exposure.
