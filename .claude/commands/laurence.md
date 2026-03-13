---
name: laurence
description: "Log observations, moments, and notes about Laurence Martin Chen"
---

# /laurence — Laurence Journal

Log a new entry about Laurence to `Children/Laurence.md`.

## Arguments

- `$ARGUMENTS` — the observation, moment, or note to log

## Workflow

1. Read `Children/Laurence.md`
2. **Determine the date**: Use today's date unless the user specifies a different date (e.g., "yesterday", "last Tuesday", "on March 5")
3. **Check if a header for that date already exists**:
   - If `## YYYY-MM-DD` header exists → append the new bullet under it
   - If not → prepend a new `## YYYY-MM-DD` section at the top of the file (reverse chronological order)
4. **Format the entry** as a bullet point:
   - If the input suggests a category (see table below), add a bold tag: `- **Behavior:** ...`
   - Otherwise, just use a plain bullet: `- ...`
   - **Copyedit the input**: Fix grammar, spelling, punctuation, and sentence structure. Clean up speech-to-text artifacts. Tighten wordy sentences. Ensure clarity and readability. But preserve the user's voice, meaning, and details — don't change the substance or tone, just polish the writing.
5. Write the file
6. Confirm what was logged with the date

## Category Tags (optional, use when obvious)

| Tag | When to use |
|-----|------------|
| **Behavior** | Emotional outbursts, aggression, impulse control, meltdowns |
| **Regulation Tool** | Coping strategies, therapy homework, stoplight method |
| **ADHD** | Medication, focus, impulsivity, diagnosis-related |
| **School** | Academic, classroom, homework, teacher feedback |
| **Therapy** | Sessions with Ciara or other therapists |
| **Health** | Medical, dental, medication, physical health |
| **Quote** | Something Laurence said (preserve his exact words) |
| **Milestone** | Developmental achievements, firsts, breakthroughs |
| **Activity** | Sports, robotics, chess, camps, hobbies |
| **Social** | Friendships, peer interactions, bullying concerns |
| **Food** | Food preferences, meals, snacks |
| **Connection Moment** | Positive bonding moments between Laurence and dad |

Only add a tag if it clearly fits. When in doubt, skip the tag.

## Copyediting Guidelines

The user often logs via voice input. Apply these edits:
- Fix run-on sentences — split into shorter, clearer sentences
- Correct subject-verb agreement and tense consistency
- Fix homophones and speech-to-text errors (e.g., "there" → "their", "pick him up" → "picking him up")
- Remove filler words and false starts
- Standardize names: "Ciara" (therapist), "Dr. Soong" (psychiatrist), "Sheri" (mom), "Ruby" (sister)
- Do NOT change the meaning, emotional tone, or level of detail

## Example

User: `/laurence today at pickup the teacher said he got frustrated during math and ripped up his worksheet but then calmed down on his own after a few minutes which is actually progress`

Result appended to `Children/Laurence.md`:
```markdown
## 2026-03-11
- **Regulation Tool:** At pickup, the teacher said Laurence got frustrated during math and ripped up his worksheet, but then calmed down on his own after a few minutes — which is actually progress.
```
