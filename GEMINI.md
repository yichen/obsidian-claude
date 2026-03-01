# Gemini Code Assist - Workspace Context

**⚠️ MANDATORY CONTEXT LOADING**

At the start of EVERY conversation and for EVERY task, you MUST:

1. **Load `CLAUDE.md`** - This is the SINGLE SOURCE OF TRUTH for this workspace
2. **Follow all instructions** in CLAUDE.md regarding:
   - **Scan for and load ALL `CLAUDE.md` files** in subdirectories (e.g., Children/CLAUDE.md, Trips/CLAUDE.md, Relationship/CLAUDE.md) to ensure full context availability.
   - Do not wait for triggers; pre-load all folder-specific rules immediately.
   - Search strategy (semantic search vs grep)
   - Indexing behavior
   - User preferences and key information

**Why this matters:**
- CLAUDE.md contains all context, preferences, and instructions for working with this Obsidian vault
- It references folder-specific CLAUDE.md files for specialized contexts
- It defines critical rules about indexing, search, and workflow

**Do not proceed with any task without first loading CLAUDE.md.**
