# ERR: text box disappears after a quick reply (short-circuit in the page)
Date: 2026-10-30
Severity: Medium

## Description
In the demo page the text box under the quick replies vanished after the user clicked quick replies a few times.
It came back only after a scenario click, a reset or a page reload.

## Root Cause
The code was `message = chosen or st.chat_input(...)`. When a quick reply was clicked, `chosen` was true,
so Python did not run `st.chat_input(...)`. Streamlit draws only what a run executes, so the box was not drawn.
The page runs again only on a user action, and the next quick reply skipped the box again.
No test clicked a quick reply and then looked for the box.

## Solution
Draw the box first: `typed = st.chat_input(...)`, then `message = chosen or typed`.
Tests now check that the box exists after every kind of click, and after seven clicks in a row.
The rehearsal checks the box in every step.

## Prevention
- Never put a Streamlit widget on the right side of `or`, `and` or a conditional expression. Draw every widget in every run.
- When a page test clicks a control, also check that the other controls are still there.
