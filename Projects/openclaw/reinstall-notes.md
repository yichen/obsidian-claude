# OpenClaw Reinstall Notes

Date: 2026-03-11

## Root Cause (Confirmed 2026-03-11)

**All three OpenRouter API keys returned 401 "User not found"** — the OpenRouter account was deactivated or the keys were all revoked. This is why every LLM call returned 404 (OpenClaw converts the upstream 401 into a generic 404 error).

Secondary issues found and fixed:
- Primary model was stuck on `bailian/qwen-plus-latest` instead of OpenRouter (config changes weren't sticking due to repeated doctor-fix cycles)
- Bailian provider had `"api": "openai-responses"` which calls `/responses` endpoint — Bailian doesn't support this, causing additional 404s
- Bailian API key `sk-950770c6b8a6492db78d12e6cdfb47b9` is 403 (expired)
- Config JSON was malformed (6 model entries stranded outside bailian provider array) — fixed by `openclaw doctor --fix`

**The fix (no reinstall needed):**
1. Get a new valid OpenRouter API key
2. Update `models.providers.openrouter.apiKey` in `~/.openclaw/openclaw.json`
3. Update `OPENROUTER_API_KEY` in `~/Library/LaunchAgents/ai.openclaw.gateway.plist`
4. Set `agents.defaults.model.primary` to `openrouter/qwen/qwen3.5-35b-a3b`

---

## Things to Keep

### API Keys & Tokens

| Service | Key |
|---------|-----|
| OpenRouter (primary) | `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` |
| OpenRouter (secondary, in auth-profiles) | `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` |
| OpenRouter (was in shell env) | `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` |
| Telegram bot token | `8249501966:AAG1CO3Ylbzjx3A48L0COH0TBLE5cdrWjLM` |
| Bailian/DashScope | `sk-950770c6b8a6492db78d12e6cdfb47b9` ⚠️ **403 — likely expired** |

### Directories to Back Up

```bash
~/.openclaw/workspace/                              # skills, obsidian skill, etc.
~/.openclaw/agents/main/agent/                      # IDENTITY.md
~/.openclaw/credentials/telegram-pairing.json       # paired devices
~/.openclaw/credentials/telegram-allowFrom.json     # your Telegram user ID allowlist
~/.openclaw/credentials/telegram-default-allowFrom.json
~/.openclaw/telegram/update-offset-default.json     # prevents replaying old messages on restart
```

### Telegram Bridge State

- **Your Telegram user ID**: `7290259201` (in allowFrom — must be preserved or re-added)
- **Bot ID**: `8249501966` (matches the bot token)
- **Last update offset**: `961707902` — back this up or the bot will replay all old messages on first start
- **Pairing request** in `telegram-pairing.json` is from Feb 22 ("Lam 4") — likely stale, safe to skip restoring

---

## Clean Uninstall Steps

```bash
# 1. Stop the gateway service
launchctl bootout gui/$UID ~/Library/LaunchAgents/ai.openclaw.gateway.plist

# 2. Remove the LaunchAgent
rm ~/Library/LaunchAgents/ai.openclaw.gateway.plist

# 3. Back up workspace and credentials BEFORE deleting
cp -r ~/.openclaw/workspace ~/openclaw-workspace-backup
cp -r ~/.openclaw/credentials ~/openclaw-credentials-backup

# 4. Wipe the state directory
rm -rf ~/.openclaw

# 5. Uninstall the package
npm uninstall -g openclaw
```

---

## Reinstall Steps

```bash
# 1. Install fresh
npm install -g openclaw

# 2. Run setup wizard
openclaw configure
```

During setup:
- Set **OpenRouter** as the primary model provider
- Use key: `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`
- Target model: `qwen/qwen3.5-35b-a3b`
- **Skip Bailian** — key is expired
- Set up Telegram with token: `8249501966:AAG1CO3Ylbzjx3A48L0COH0TBLE5cdrWjLM`

```bash
# 3. Restore workspace and Telegram credentials
cp -r ~/openclaw-workspace-backup ~/.openclaw/workspace
cp ~/openclaw-credentials-backup/telegram-allowFrom.json ~/.openclaw/credentials/
cp ~/openclaw-credentials-backup/telegram-default-allowFrom.json ~/.openclaw/credentials/
# Restore update offset to avoid replaying old messages:
mkdir -p ~/.openclaw/telegram
cp ~/openclaw-credentials-backup/../telegram/update-offset-default.json ~/.openclaw/telegram/
# Optional: restore pairing (skip if stale):
# cp ~/openclaw-credentials-backup/telegram-pairing.json ~/.openclaw/credentials/

# 4. CRITICAL: Add OPENROUTER_API_KEY to the LaunchAgent plist
#    After running: openclaw gateway install
#    Edit ~/Library/LaunchAgents/ai.openclaw.gateway.plist
#    Add inside the <EnvironmentVariables> dict:
#      <key>OPENROUTER_API_KEY</key>
#      <string>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</string>
#    Then reload:
launchctl bootout gui/$UID ~/Library/LaunchAgents/ai.openclaw.gateway.plist
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

---

## Resolution (2026-03-11)

Clean reinstall completed successfully. Bot is responding on Telegram.

Backups preserved at:
- `~/openclaw-backup/` — pre-reinstall user files
- `~/openclaw-clean-install/` — clean install snapshot (for revert reference)

## Config Change: Added Ollama qwen3.5:27b as Fallback (2026-03-11)

Added local Ollama model as backup in `~/.openclaw/openclaw.json`:

- `agents.defaults.model.fallbacks`: added `"ollama/qwen3.5:27b"` after `"openrouter/auto"`
- `agents.defaults.models`: added `"ollama/qwen3.5:27b": { "alias": "Ollama-qwen3.5:27b" }`

No changes to `models.json`, `auth-profiles.json`, or `gateway.plist` — Ollama is local and needs no auth.

**Revert**: `cp ~/.openclaw/openclaw.json.bak-<timestamp> ~/.openclaw/openclaw.json` then reload LaunchAgent.

---

## Key Lesson

**OpenClaw reads `OPENROUTER_API_KEY` from the environment**, not from `models.providers.openrouter.apiKey` in the config (or in addition to it). The LaunchAgent must have this env var explicitly set in the plist `EnvironmentVariables` dict, or the built-in OpenRouter provider will never authenticate.

Do NOT rely on:
- `models.providers.openrouter.apiKey` in `openclaw.json`
- `agents/main/agent/auth-profiles.json`

These appear to be secondary/fallback mechanisms. The env var is what actually works.
