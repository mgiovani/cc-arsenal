---
name: wtf
description: Re-explain your own previous message in plain, simplified English (ASD-STE100
  style), when the user did not understand it. Use when the user replies with "wtf", "what?",
  "I don't get it", "explain that again simpler", "ELI5", or "in plain English". Rewrites
  what was already said; it does not do new work, new research, or new code.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: false
argument-hint: ''
---

# wtf

Rewrite your previous message so a tired non-expert understands it on the first read. Explain the same content, do not answer a new question and do not add new work.

Rules (ASD-STE100 Simplified Technical English):

- One idea per sentence. Maximum 20 words per sentence. Active voice, present tense.
- One word, one meaning. Reuse the same word for the same thing; never swap in a synonym.
- Replace every jargon term with plain words. If a term must stay (a filename, a flag, an API name), define it once in four words or less.
- Lead with the answer or the action. Cut hedging, background, and anything the user already knows.
- Maximum 5 lines total: short prose or a short bullet list. No headers, no tables, no code unless the original point *is* code.

If the previous message was already plain, say so in one line instead of padding it out. If the confusion is about *what to do next*, end with one line naming the next action.
