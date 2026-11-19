# UX Copy and States

## Contents

- [Design every state](#design-every-state)
- [Honest data](#honest-data)
- [Errors](#errors)
- [Confirmations and destructive actions](#confirmations-and-destructive-actions)
- [Writing the strings](#writing-the-strings)
- [Forms and feedback](#forms-and-feedback)

## Design every state

A component is unfinished until loading, empty, error, disabled and overflow are drawn. Name the missing state in a review.

- Loading. Use a skeleton shaped like the final content so the layout does not jump. Name the real operation in any loading text. Show progress only when it is real.
- Empty. The copy depends on the cause. First use shows the value and a next step. A cleared list gets a light touch. No results suggests a different query or clearing filters. No permission explains why and how to get access. A failure explains and offers a retry.
- Error. It sits inside the failing region, not in a full-page banner that hides a working screen. It says what failed, when data was last good and offers a retry.
- Stale. Data that has gone stale announces itself, for example a disconnected strip, and resumes from the last valid point on reconnect.
- Disabled. State why, and keep the control legible.

Draw every reachable state, and name any you skip on purpose.

## Honest data

- A measured zero renders as `0`. A value never looked at renders as a dash or as "not looked at yet" (the general no-fake-zero rule is in `code-guidelines`).
- A status indicator appears only when its subject needs attention. The healthy default stays silent. A permanent "Connected" footer and positive assertions such as "on budget" or "no conflicts" dress the absence of a problem as information.
- State appears once per view. Two elements restating one fact is noise, and a fact shown twice is one value in the data.
- A rendered preview shows interface, not commentary or implementation rationale.
- Internal identifiers (ticket or requirement ids) never lead a row. Put them last in tertiary text.
- A row reports what happened, not what the row is.
- Never invent proof: customers, quotes, logos, ratings, counts or benchmarks. Label demonstration data as synthetic, and use realistic domain names instead of "John Doe" or lorem ipsum.

## Errors

- Name the problem, the cause if known, and the next step. Never lead with an internal code, and never promise a cause the system cannot know.
- Map statuses to distinct UI: 400 inline validation, 401 sign-in, 403 a permission explanation, 404 a not-found state, 429 a wait message, 500 a generic message with a support path.
- Keep what the user typed when a submit fails. Never wipe the form.
- Show a network failure with an explanation and a retry. Do not show a request line or status code to the user, and fall back to a plain sentence such as "Could not reach the server. Check that it is running."
- Validation names the rule for that field and does not blame the person. Prevent the error where you can: remove invalid options instead of graying them out.
- Keep a joke away from loss, money, privacy or blocked work.

## Confirmations and destructive actions

- Frequent and reversible: act, then offer an undo toast. Rare and irreversible: a modal with a confirmation that is visibly distinct (the danger role).
- Name the object and the verb on both the message and the button ("Delete project", not "Yes", "OK" or "Continue").
- When an action is irreversible, surface the risk in the eyebrow beside a warning icon and keep the title a plain statement of the action. A risk buried inside the title gets skimmed.
- A screen with a human gate keeps its decision controls in view at all times, in a bar pinned to the surface edge.
- Toasts confirm a non-blocking outcome. They auto-dismiss after about 3 to 5 seconds, never take focus and pause their timer while the tab is hidden.

## Writing the strings

- Use one noun and one verb per concept across the product. Match the backend's own words, and keep a short glossary when screens disagree.
- Buttons name the action in one to three words, verb first. Navigation labels are single nouns that link to screens.
- Write short plain sentences at about a sixth-grade level. Cut genre verbs (unlock, supercharge, seamless) and stock openers. Use no em dash in product strings.
- Send every user-facing string through the project's translation function when one exists, with English keys and complete sentences. Do not add i18n to a project without it. Never glue fragments together, and write plurals as plain conditions or the library's plural rules.
- Format dates, numbers and currency with `Intl`, never by hand. Budget 30 to 40 percent extra width for translated text.
- Lead with the one fact the user needs now, then the next available action. Put uncommon detail behind progressive disclosure.
- Every placeholder shows an example. The label stays visible once the field has input.
- Use the trade's own vocabulary in labels and empty states, not template nouns such as "Items" or "Records".

## Forms and feedback

- Disable a submit while work is in flight to stop a double submit, using `aria-disabled` so focus survives. Verify by clicking it ten times quickly.
- Confirm each completed action with a brief visible signal. Silent success leaves people unsure.
- Autosave long forms and confirm before closing a sheet with unsaved changes.
- Keep helper text under the label and state the expected format before any error appears.
- Do not fake a form or payment when no backend exists. Point the action at its real destination and list the placeholder as a launch blocker.
