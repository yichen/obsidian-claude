# Specification: Finance AI (Privacy-First Desktop Application)

## 1. Vision & Core Principles
- **Privacy-First**: Zero raw financial data leaves the local machine. Remote LLMs only receive anonymized Markdown summaries.
- **High-Density Aesthetic**: Modeled after ChatGPT Desktop and Linear. Avoid "floating" elements; use structured grid systems.
- **Verifiable Design**: UI agents must validate every component against the `theme-tokens.json` file.

## 2. Technical Stack
- **Framework**: Electron + React/TypeScript.
- **Styling**: Tailwind CSS + Shadcn UI. (Direct CSS overrides are prohibited).
- **Intelligence**: Local SQLite + Node-based MCP Server.
- **Agent Orchestration**: Claude Code v2.1.32+ (Opus 4.6 Agent Team Mode).

## 3. The "Anti-White Space" Layout Contract
To ensure a professional SaaS look, all agents must adhere to these constraints:

| Element | Specification | Verification |
| :--- | :--- | :--- |
| **Max Content Width** | 1280px (Centered) | Playwright Viewport Check |
| **Grid System** | 8px Base Grid (All spacing must be multiples of 8) | Tailwind Linter |
| **Density Rule** | If a card has > 30% empty space, add a Sparkline or Metric. | Vision Review (Opus 4.6) |
| **Typography** | Font: Inter. Body: 14px. Headers: Semibold. | Global CSS Audit |

## 4. Agent Team Workflow (Opus 4.6)
Initialize the build team with: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

### Roles:
1. **Architect (Opus 4.6)**: Owns the `TASK_LIST.md` and logic.
2. **UI Challenger (Opus 4.6)**: The "Critic." Uses Vision to review UI screenshots and rejects "messy" layouts.
3. **Implementer (Sonnet 4.6)**: High-speed frontend development using Shadcn UI.
4. **Tester (Sonnet 4.6)**: Runs Playwright visual regression tests.

## 5. Page Requirements
- **Home**: 3-Column Bento Grid. Sidebar: 260px fixed width.
- **Transactions**: Fixed-layout table (SaaS Density). No shifting on search.
- **AI Chat**: Minimalist ChatGPT-style. Charts must be responsive and pinnable.

## 6. Verification
- All UI must pass a Lighthouse accessibility score of 90+.
- Zero horizontal scrolling at 1440px resolution.