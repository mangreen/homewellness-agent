# ERR: rehearsal could not find the alerts because Streamlit moves a leading emoji
Date: 2026-10-28
Severity: Medium

## Description
The rehearsal waited for an alert whose text starts with the siren emoji. The alert was on the page, but the test never saw it.

## Root Cause
Streamlit turns a leading emoji of `st.error` and `st.warning` into the icon. The element value starts after the emoji.
The test matched the emoji.

## Solution
Match words of the alert text ("緊急通報", "通知家人"), not the emoji.

## Prevention
- Do not match on a leading emoji in page tests. See MEM-0005-phase-4-demo-ui.md.
- When a test fails on the full stack, print what the page shows before you change the page.
