# ERR: two tests fail in Docker because the container has no `docs` folder
Date: 2026-10-28
Severity: Medium

## Description
`make test` showed 326 passed and 2 failed. Both failures were `FileNotFoundError: /app/docs/api/openapi.yaml`.
The tests passed on the host.

## Root Cause
The test containers mounted only `src` and `tests`. A test read a file in `docs`. The host path hid the gap.

## Solution
Mount `./docs` (and later `./ui` and `./.agents`) read-only into the `test` and `itest` services.

## Prevention
- When a test reads a file outside `src` and `tests`, add a mount in `docker-compose.yml` in the same commit.
- Check the suite in a copy of the project that holds only the mounted folders.
