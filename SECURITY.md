# Security Policy

## Supported versions

Security fixes target the current `main` branch.

## Reporting a vulnerability

Open a private security advisory if the repository host supports it. If not,
contact the maintainer privately and include:

- affected file or script;
- reproduction steps;
- expected impact;
- whether secrets, credentials, or private data could be exposed.

Do not publish exploit details before a fix or mitigation is available.

## Design principles

This skill is intentionally conservative:

- scripts use only the Python standard library;
- scripts do not make network calls;
- scripts do not read environment secrets;
- scripts do not execute user-provided code;
- scripts only write inside the workspace path passed by the user;
- user notes, web pages, and imported research are treated as data, not instructions for the agent to override system or skill rules;
- external writes such as CRM updates, publishing, messaging, analytics changes, or connector mutations require explicit user approval outside the bundled scripts.

If future versions add integrations, they must document required permissions,
failure modes, and secret-handling rules before release.
