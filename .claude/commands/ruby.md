---
name: ruby
description: "Log observations, moments, and notes about Ruby Martin Chen"
---

# /ruby — Ruby Journal

Log a new entry about Ruby to `Children/Ruby.md`.

## Arguments

- `$ARGUMENTS` — the observation, moment, or note to log

## Workflow

1. Read `Children/Ruby.md`
2. **Determine the date**: Use today's date unless the user specifies a different date (e.g., "yesterday", "last Tuesday", "on March 5")
3. **Check if a header for that date already exists**:
   - If `### YYYY-MM-DD` header exists → append the new bullet under it
   - If not → prepend a new `### YYYY-MM-DD` section at the top of the file (reverse chronological order)
4. **Format the entry** as a bullet point:
   - If the input suggests a category (food, school, therapy, milestone, quote, activity), add a bold tag: `- **Food:** ...`
   - Otherwise, just use a plain bullet: `- ...`
   - Clean up speech-to-text artifacts (the user often uses voice input)
   - Keep the user's voice and tone — don't over-formalize
5. Write the file
6. Confirm what was logged with the date

## Category Tags (optional, use when obvious)

| Tag | When to use |
|-----|------------|
| **Food** | Food preferences, meals, snacks |
| **School** | Academic, classroom, homework |
| **Therapy** | Sessions with Nicole or other therapists |
| **Quote** | Something Ruby said (preserve her exact words) |
| **Milestone** | Developmental achievements, firsts |
| **Activity** | Sports, gymnastics, crafts, hobbies |
| **Social** | Friendships, interactions with peers |
| **Health** | Medical, dental, physical health |
| **Emotional** | Feelings, anxiety, coping, breakthroughs |

Only add a tag if it clearly fits. When in doubt, skip the tag.

## Example

User: `/ruby she told me today that she wants to learn piano because her friend Lily plays`

Result appended to `Children/Ruby.md`:
```markdown
### 2026-03-11
- **Activity:** Ruby told me she wants to learn piano because her friend Lily plays.
```
