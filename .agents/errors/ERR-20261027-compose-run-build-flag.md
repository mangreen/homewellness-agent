# ERR: `docker compose run --build` fails on Compose v2.10
Date: 2026-10-27
Severity: Medium

## Description
`make test` stopped with `unknown flag: --build`. No test ran.

## Root Cause
The Makefile used `docker compose run --build`. That flag came in a later Compose release. The Mac has Compose v2.10.2.
The build sandbox had no Docker, so nobody ran the command before delivery.

## Solution
Build first, then run: `docker compose --profile test build test`, then `docker compose --profile test run --rm test`.

## Prevention
- Use only flags that Compose v2.10 supports. Compose and Docker versions are in MEM-0001-poc-scope-and-stack.md.
- A command that the sandbox cannot run must be marked "not verified". The user runs it first.
