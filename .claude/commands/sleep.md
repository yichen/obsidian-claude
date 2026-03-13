---
name: sleep
description: "Log sleep diary entry to Health/Yi's Mental Health, Anxiety, SAD.md"
---

# /sleep — Sleep Diary

Log a sleep/mental health entry to `Health/Yi's Mental Health, Anxiety, SAD.md`.

## Arguments

- `$ARGUMENTS` — sleep report, mood, meds, or mental health observations

## Workflow

1. Read the **first 60 lines** of `Health/Yi's Mental Health, Anxiety, SAD.md` (to see recent entries and current format)
2. **Determine the date**: Use today's date unless the user specifies a different date (e.g., "last night" = today's date since the entry is about last night's sleep logged today)
3. **Check if a header for that date already exists**:
   - If `## YYYY-MM-DD` header exists → append the new bullet(s) under it
   - If not → prepend a new `## YYYY-MM-DD` section at the top of the file, **after any existing front matter but before the first `##` header** (reverse chronological order)
4. **Format the entry** as one or more bullet points with bold tags:
   - Split the input into separate bullets when it covers multiple topics
   - Apply the appropriate bold tag to each bullet (see table below)
   - **Copyedit**: Fix grammar, spelling, punctuation, and sentence flow. Clean up speech-to-text artifacts. Tighten wordy sentences. Use em-dashes for asides (matching existing style). But preserve the user's voice, meaning, and emotional tone.
5. Write the file
6. Confirm what was logged with the date

## Tags (always apply one per bullet)

| Tag | When to use |
|-----|------------|
| **Sleep:** | Hours slept, sleep quality, wakeups, REM, evening routine, bedtime, wake time |
| **Meds:** | Hydroxyzine PAM/HCL, melatonin, ashwagandha, Zyrtec, any sleep/anxiety meds |
| **Mood:** | General emotional state, anxiety levels, happiness, sadness |
| **Stress:** | Work stress, financial anxiety, coparenting tension, job concerns |
| **Takeaway:** | Insights, patterns noticed, lessons learned, plans to try |
| **Fitness:** | Exercise and its effect on sleep/mood (jogging, lifting, etc.) |
| **SAD:** | Seasonal affective disorder observations, light therapy, winter patterns |

Always tag every bullet. When the input covers both sleep and meds, split into two tagged bullets.

## Style Notes (match existing entries)

- Em-dashes for parenthetical asides: `—especially since...—`
- Specific details: hours slept, REM time, Garmin data, med names
- Causal observations: "curious if X caused Y", "wondering if", "starting to think"
- First person, journal tone — honest and reflective
- Reference known patterns: 4 a.m. wakeups, campground resets, post-date insomnia, chase-and-tickle bedtime routine, AI/YouTube rabbit holes disrupting sleep

## Example

User: `/sleep took hydroxyzine last night, slept about 6 hours, woke up at 4am again but managed to fall back asleep after 30 minutes. REM was low again maybe 20 minutes. feeling pretty good today though`

Result appended to `Health/Yi's Mental Health, Anxiety, SAD.md`:
```markdown
## 2026-03-11
- **Meds:** Took hydroxyzine PAM at bedtime.
- **Sleep:** Slept about 6 hours—woke up at 4 a.m. again but managed to fall back asleep after 30 minutes. REM was low again, maybe 20 minutes.
- **Mood:** Feeling pretty good today despite the short night.
```
