---
name: keepa-smartscout-datadive-installer-experimental
description: Installs and registers the Keepa, SmartScout, and DataDive adapter MCPs (BWB03/keepa-adapter, BWB03/smartscout-adapter, BWB03/datadive-adapter) into Claude Desktop. Use this skill whenever a user wants to set up one or more of these MCPs — phrases like "install keepa MCP", "set up datadive", "add smartscout to claude desktop", "wire up the amazon MCPs", "give me keepa+datadive+smartscout", "set up my MCPs", "install the amazon stack", or any onboarding request to get these adapters running. The skill writes a single installer script to the user's outputs folder and gives them one command to run; the script does the cloning, building, config merging (without overwriting existing servers), and key prompting. Trigger on casual phrasings too. Do NOT trigger for arbitrary third-party MCPs that aren't keepa/datadive/smartscout.
---

# Keepa + SmartScout + DataDive Installer (experimental)

## How to use this skill — exact flow

The flow is: **ask in chat which adapters → write the script to outputs → tell user to run it using the exact path you wrote to**. Three steps, no improvisation.

### ⚠️ CRITICAL: where the script lives in Cowork

When you Write a file to the user's outputs folder in Cowork, the file is created at a **real absolute path on the user's local Mac/PC** — something like:

```
/Users/<their-username>/Library/Application Support/Claude/local-agent-mode-sessions/<UUID>/<UUID>/local_<UUID>/outputs/install-mcps.sh
```

That path is what you see when you call the Write tool — it's already on the user's machine, no download step is needed even though the chat UI shows the file as a downloadable artifact.

**You MUST use this exact path verbatim in your reply.**

Do **not** tell the user:

- ❌ `bash ~/Downloads/install-mcps.sh` — the file is NOT in Downloads, and never will be unless they manually download. This is the most common hallucination — the chat's "Download" / "Open in TextEdit" buttons trick the orchestrator into assuming Downloads.
- ❌ `bash ./install-mcps.sh` — only works if they're in the right cwd
- ❌ Any other guessed path

You **must** tell them:

- ✅ `bash "<exact absolute outputs path you wrote to>" <slugs>`

If you're unsure what path the Write tool used, look at the path it actually wrote to — that's the value the tool returned and the path it appears at in your file system. Quote it verbatim, in double quotes (the path contains spaces — "Application Support" — which `bash` requires quoted).

### Step 1 — Ask which adapters (in chat, not in bash)

Use `AskUserQuestion` with `multiSelect: true`. One question, three options:

```
Question: "Which MCP adapters do you want to install?"
Header:   "Adapters"
multiSelect: true
Options:
  • "Keepa" — Amazon product data, price history, BSR, deals
  • "DataDive" — niche research, keyword analysis, ranking juice
  • "SmartScout" — Amazon brand/seller intelligence
```

Default to all three if the user is vague. Map the user's selections to slugs (`keepa`, `datadive`, `smartscout`).

### Step 2 — Write the installer to the user's outputs folder

- macOS → write `scripts/install-mcps.sh` (verbatim from this skill) to the user's outputs folder using the Write tool.
- Windows → write `scripts/install-mcps.ps1` similarly.

The path you write to is the **absolute** path of the user's outputs directory — something like `/Users/<user>/Library/Application Support/Claude/local-agent-mode-sessions/<session>/.../outputs/install-mcps.sh`. Note that exact path. **Do not tell the user the file is in `~/Downloads/` or any other folder — use the path you actually wrote to.**

### Step 3 — Reply with one short message and the run command

Use the absolute path from Step 2 verbatim. Append the chosen slugs as args.

**Example reply (macOS, all three selected, with realistic Cowork path):**

> Run this in Terminal — copy the whole line, paths with spaces need the quotes:
>
> ````bash
> bash "/Users/marc/Library/Application Support/Claude/local-agent-mode-sessions/3a9b…/2cde2f89-…/local_b9e3…/outputs/install-mcps.sh" keepa datadive smartscout
> ````
>
> It'll install any missing tools (Node, git, Homebrew if needed), then prompt for each API key with hidden input — don't paste keys in chat. When it finishes, relaunch Claude Desktop.

(The path above is just a shape — use the actual one the Write tool returned, with the user's real username and the real session UUIDs.)

**Example reply (Windows, all three selected):**

> Run this in PowerShell:
>
> ````powershell
> powershell -ExecutionPolicy Bypass -Command "& '<absolute path you wrote to>' -Servers keepa,datadive,smartscout"
> ````
>
> It'll install any missing tools (Node LTS, git via winget), then prompt for each API key with hidden input. When it finishes, relaunch Claude Desktop.

**Why `-Command "& '...' -Servers a,b"` instead of `-File ... -Servers a,b`** — when invoked via `-File`, `powershell.exe` passes `keepa,datadive` as a single string token rather than splitting on the comma, so the `[string[]] $Servers` param ends up as `@("keepa,datadive")` and the script fails validation with "Unknown preset 'keepa,datadive'". Using `-Command` makes PowerShell parse the argument as a real expression so the comma works as the array operator. The script also has a defensive split as a fallback, but always emit the `-Command` form first.

That's the entire reply. **Do not** add:
- A prereq list — the script checks and offers to install Node, git, etc.
- A "what it does" enumeration — the script prints its own summary at the end
- Verification suggestions — the script prints those too

### Why we don't inline the script in a heredoc

We tried that. Terminal's bracketed-paste buffer truncates very long pastes (~2 KB+) mid-stream, leaving bash hanging at a `heredoc>` prompt with no way to recover except Ctrl+C. Writing to outputs and running with the absolute path is reliable — the file is on the user's machine, no clipboard limit involved.

### Why the multi-pick happens in chat, not in the script

The chat picker (`AskUserQuestion`) is friendlier than a numbered Terminal menu, and it lets the orchestrator pass the slugs to the script as args — so the script doesn't need to read stdin for menu selection (which can collide with the heredoc/paste mechanics).

The bash and PowerShell scripts default to **all three** if no slugs are passed (so a user running them standalone still gets a sane outcome), but the canonical path through this skill always passes slugs explicitly.

### If the user comes back with a problem

- **"No such file or directory"** at the path you gave — the path was wrong (most often: you said `~/Downloads/install-mcps.sh` instead of the Cowork outputs path). Re-write the script with the Write tool, capture the **exact absolute path** the tool wrote to, and re-emit the bash command with that path verbatim. Tell the user: "ignore the previous path, use this one".
- **"Permission denied"** running the script — Tell them `chmod +x "<path>"` then rerun. (Or `bash <path>` which doesn't need exec perms — the form we already use.)
- **Anything else** — The script's own errors are descriptive. Quote them back to the user and follow the script's suggested fix.

## Reference: the three adapters

| Slug | Repo | Env var |
|---|---|---|
| `keepa` | https://github.com/BWB03/keepa-adapter | `KEEPA_API_KEY` |
| `datadive` | https://github.com/BWB03/datadive-adapter | `DATADIVE_API_KEY` |
| `smartscout` | https://github.com/BWB03/smartscout-adapter | `SMARTSCOUT_API_KEY` |

All three are stdio MCPs (Node/TypeScript) registered via `claude_desktop_config.json` (the Connectors UI's "+" button only accepts remote/HTTP MCPs).

## Reference: what the installer guarantees (so you can answer "is it safe?")

If the user asks what the installer does or whether it's safe to run, you can quote these:

- **It won't overwrite the user's existing `claude_desktop_config.json`.** Reads the current file, merges in new entries, writes back. Other MCP servers, the `preferences` block, and any extra env vars on existing entries are preserved. A timestamped `.bak.<TS>` is created before the write.
- **It won't crash on launch.** `BWB03/keepa-adapter` opens a SQLite DB at startup and needs `KEEPA_DB_PATH` set absolutely or it hits `SQLITE_CANTOPEN`. The installer always sets `KEEPA_DB_PATH` to an absolute path inside the install dir, plus `KEEPA_DEFAULT_DOMAIN=com`.
- **API keys never appear in chat.** Each key is entered via a hidden Terminal prompt (`read -s` on macOS, `Read-Host -AsSecureString` on Windows), then written directly to the config file.
- **Claude Desktop is force-quit before any write,** so the app can't race the installer or wipe `mcpServers` while we're working.

## Reference: how to run / flags

**macOS:**
```bash
bash install-mcps.sh keepa datadive smartscout    # all three
bash install-mcps.sh keepa                         # just one
bash install-mcps.sh --reset-keys                  # re-enter keys without re-cloning
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File install-mcps.ps1 -Servers keepa,datadive,smartscout
powershell -ExecutionPolicy Bypass -File install-mcps.ps1 -ResetKeys -Servers keepa
```

Linux is not supported (the script uses `osascript` and the macOS-specific config path).

## Important guardrails

### Never accept API keys in chat

If the user pastes an API key into the chat, **decline to write it to disk for them**. Tell them:

1. Keys must be entered via the installer's Terminal prompt so they're not persisted in the chat transcript.
2. They should rotate the leaked key at the provider before re-entering.
3. Then run the installer.

### Don't bypass the installer

Don't reach for `cp` or hand-edit the JSON. The installer encodes all the safety checks — backup, merge, validate, force-quit, db-path. If you find yourself improvising, stop and run the script instead.

## Files in this skill

```
keepa-smartscout-datadive-installer-experimental/
├── SKILL.md          (this file)
├── scripts/
│   ├── install-mcps.sh    (macOS installer)
│   └── install-mcps.ps1   (Windows installer)
└── references/
    └── presets.json       (the three repo URLs and env var names)
```

`presets.json` is the source of truth — if a fourth adapter gets added, edit `presets.json` and both scripts (which carry their own equivalent inline) pick it up.
