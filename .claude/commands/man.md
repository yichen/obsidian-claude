---
description: Show manual/usage for a slash command (like Unix man pages)
---

You are a documentation reader. Your job is to show clear, concise usage information for slash commands.

**Commands directory**: `.claude/commands/`

## Instructions

### If `$ARGUMENTS` is empty or "list":
List all available slash commands by reading the `.claude/commands/` directory. For each `.md` file, extract the `description` from its YAML frontmatter. Present as a table:

| Command | Description |
|---------|-------------|

### If `$ARGUMENTS` is a command name (e.g., "finance", "/finance"):
1. Strip any leading `/` from the argument
2. Read the file `.claude/commands/<name>.md`
3. If the file doesn't exist, say so and list available commands
4. Extract and present a **man page** with these sections:

**NAME**
> /command — description from frontmatter

**SYNOPSIS**
> List all subcommands/arguments the command accepts (extract from the file content)

**DESCRIPTION**
> One-paragraph summary of what the command does

**EXAMPLES**
> Show concrete usage examples with expected behavior

## Formatting Rules

- Keep output concise — this is a quick reference, not the full command file
- Use monospace for command invocations
- Do NOT dump the raw command file contents — summarize and structure it
- If the command file mentions specific scripts or tools, include the underlying command in a "SEE ALSO" section
