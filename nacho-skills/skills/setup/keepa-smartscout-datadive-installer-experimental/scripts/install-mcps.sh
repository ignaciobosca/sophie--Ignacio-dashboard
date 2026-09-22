#!/usr/bin/env bash
# Keepa + SmartScout + DataDive adapter installer — macOS (experimental)
#
# Usage:
#   bash install-mcps.sh                       # installs all three (default)
#   bash install-mcps.sh keepa                 # install just keepa
#   bash install-mcps.sh keepa datadive        # ...or any subset
#   bash install-mcps.sh --reset-keys [slugs]  # rewrite API keys, no rebuild
#
# What I do:
#   1. Quit Claude Desktop so it can't race the config write
#   2. Install Node + git via Homebrew if they're missing (with your OK)
#   3. Clone + build each selected repo into ~/Tools/
#   4. Merge entries into ~/Library/Application Support/Claude/claude_desktop_config.json
#      (preserves any other servers + the `preferences` block; backup first)
#   5. Prompt for each API key in Terminal — hidden input, never through chat
#   6. Validate JSON and tell you to relaunch Claude Desktop

set -euo pipefail

# Compatible with macOS default bash 3.2 (no associative arrays).

# ── Preset definitions (slug|repo|env_var|display|dirname) ────────────────────
PRESETS_RAW="\
keepa|https://github.com/BWB03/keepa-adapter.git|KEEPA_API_KEY|Keepa|keepa-adapter
datadive|https://github.com/BWB03/datadive-adapter.git|DATADIVE_API_KEY|DataDive|datadive-adapter
smartscout|https://github.com/BWB03/smartscout-adapter.git|SMARTSCOUT_API_KEY|SmartScout|smartscout-adapter"

color() { printf "\033[1;%sm%s\033[0m\n" "$1" "$2"; }
info()  { color 36 "==> $1"; }
ok()    { color 32 "✓  $1"; }
warn()  { color 33 "!  $1"; }
fail()  { color 31 "✗  $1"; exit 1; }

# Look up a column for a slug; column 1=slug, 2=repo, 3=env_var, 4=display, 5=dirname
preset_field() {
  echo "$PRESETS_RAW" | awk -F'|' -v s="$1" -v c="$2" '$1==s {print $c; exit}'
}
list_slugs() { echo "$PRESETS_RAW" | awk -F'|' '{print $1}'; }
valid_slug() { [ -n "$(preset_field "$1" 1)" ]; }

TOOLS_DIR="${MCP_TOOLS_DIR:-$HOME/Tools}"
CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG="$CONFIG_DIR/claude_desktop_config.json"

# ── Args ──────────────────────────────────────────────────────────────────────
MODE="install"   # install | reset-keys
SLUGS=()
for a in "$@"; do
  case "$a" in
    --reset-keys) MODE="reset-keys" ;;
    -h|--help)
      sed -n '2,18p' "$0"; exit 0 ;;
    -*)
      fail "Unknown flag: $a" ;;
    *)
      valid_slug "$a" || fail "Unknown preset '$a'. Valid: $(list_slugs | tr '\n' ' ')"
      SLUGS+=("$a") ;;
  esac
done

# ── Quit Claude Desktop early ─────────────────────────────────────────────────
info "Quitting Claude Desktop"
osascript -e 'tell application "Claude" to quit' 2>/dev/null || true
sleep 1
pkill -x "Claude" 2>/dev/null || true
sleep 1
ok "Claude Desktop is quit"

# Helper for yes/no confirmations during the brew/winget install flow
prompt_yn() {
  local msg="$1" default="${2:-Y}" reply
  read -r -p "$msg " reply || reply=""
  reply="${reply:-$default}"
  case "$reply" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

# Default to all three adapters when no slugs are passed. Claude (in chat) is
# expected to ask the user which adapters they want and pass the slugs as args
# — there's no interactive bash picker on purpose.
if [ "${#SLUGS[@]}" -eq 0 ]; then
  while IFS= read -r s; do SLUGS+=("$s"); done < <(list_slugs)
fi

info "Mode: $MODE"
info "Targets: ${SLUGS[*]}"

# ── Dependency checks (with auto-install via Homebrew) ────────────────────────
ensure_brew() {
  if command -v brew >/dev/null 2>&1; then return 0; fi
  warn "Homebrew is not installed."
  if ! prompt_yn "Install Homebrew now? (will ask for your sudo password) [Y/n]:"; then
    fail "Cancelled. Install Homebrew yourself: https://brew.sh — then rerun this script."
  fi
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Add brew to PATH for this script (Apple Silicon: /opt/homebrew, Intel: /usr/local)
  if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
  if [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"; fi
  command -v brew >/dev/null 2>&1 || fail "Homebrew install completed but 'brew' still not on PATH."
}

ensure_node() {
  if command -v node >/dev/null 2>&1; then
    NODE_MAJOR=$(node -p "process.versions.node.split('.')[0]")
    if [ "$NODE_MAJOR" -ge 18 ]; then ok "Node $(node -v) detected"; return 0; fi
    warn "Node $(node -v) is too old (need 18+)"
  else
    warn "Node.js is not installed."
  fi
  if prompt_yn "Install Node 18+ via Homebrew now? [Y/n]:"; then
    ensure_brew
    info "Running: brew install node"
    brew install node
  else
    fail "Cancelled. Install Node LTS from https://nodejs.org and rerun this script."
  fi
  command -v node >/dev/null 2>&1 || fail "Node still missing after install."
  ok "Node $(node -v) installed"
}

ensure_git() {
  if command -v git >/dev/null 2>&1; then return 0; fi
  warn "git is not installed."
  echo "Triggering the Xcode Command Line Tools installer (a popup will appear)."
  xcode-select --install 2>&1 || true
  fail "Click 'Install' in the popup, wait for it to finish, then rerun this script."
}

ensure_python3() {
  command -v python3 >/dev/null 2>&1 || fail "python3 not found (used for JSON merge — should be on macOS by default)"
}

if [ "$MODE" = "install" ]; then
  ensure_node
  ensure_git
  ensure_python3
fi
ensure_python3   # always needed (used for the JSON merge step)

# ── Clone + build each selected adapter ───────────────────────────────────────
if [ "$MODE" = "install" ]; then
  mkdir -p "$TOOLS_DIR"
  for slug in "${SLUGS[@]}"; do
    repo=$(preset_field "$slug" 2)
    dirname=$(preset_field "$slug" 5)
    target="$TOOLS_DIR/$dirname"

    if [ -d "$target/.git" ]; then
      info "[$slug] updating existing checkout at $target"
      git -C "$target" pull --ff-only
    else
      [ -e "$target" ] && fail "[$slug] $target exists but isn't a git repo. Move it aside and rerun."
      info "[$slug] cloning $repo -> $target"
      git clone --depth=1 "$repo" "$target"
    fi

    cd "$target"
    info "[$slug] npm install"
    # --loglevel=error keeps output tidy without hiding native-build errors
    # (--silent would mask node-gyp failures and leave the user with a
    # confusing 'tsup missing' message at the next step).
    if ! npm install --loglevel=error; then
      if [ "$slug" = "keepa" ]; then
        fail "[$slug] npm install failed. If you see a node-gyp / better-sqlite3 / 'Xcode' error, switch to Node 22 LTS ('brew install node@22 && brew link --force node@22') and rerun. The current keepa-adapter's better-sqlite3 pin doesn't have prebuilds for very-recent Node versions."
      else
        fail "[$slug] npm install failed — see errors above"
      fi
    fi
    info "[$slug] npm run build"
    npm run build
    [ -f "$target/dist/index.js" ] || fail "[$slug] build did not produce dist/index.js"
    ok "[$slug] built $target/dist/index.js"
  done
fi

# ── Backup current config ─────────────────────────────────────────────────────
mkdir -p "$CONFIG_DIR"
TS=$(date +%Y%m%d-%H%M%S)
if [ -f "$CONFIG" ]; then
  cp "$CONFIG" "${CONFIG}.bak.${TS}"
  ok "Backup -> ${CONFIG}.bak.${TS}"
else
  echo '{}' > "$CONFIG"
  warn "No existing config — created an empty one"
fi

# ── Prompt for API keys (hidden input, no chat) ───────────────────────────────
echo
echo "── API keys ─────────────────────────────────────────────────────────────"
echo "Paste each key when prompted. Input is hidden — nothing will be echoed."
echo "Press Enter on a blank line to keep the existing key (if any)."
echo
KEYS_BLOB=""
for slug in "${SLUGS[@]}"; do
  display=$(preset_field "$slug" 4)
  env_var=$(preset_field "$slug" 3)
  read -r -s -p "$display API key ($env_var): " v || v=""
  echo
  # KEYS_BLOB collects "<slug>\t<key>" lines for the python merge step
  KEYS_BLOB+="$slug	$v
"
done

# ── Merge into config (python; passes data via env vars on macOS — `ps`
#    requires entitlements + no /proc, so this is acceptable here) ─────────────
info "Merging mcpServers into config (preserves existing servers + preferences)"
PRESETS_BLOB="$PRESETS_RAW" \
TOOLS_DIR_E="$TOOLS_DIR" \
CONFIG_PATH="$CONFIG" \
SLUGS_E="${SLUGS[*]}" \
KEYS_BLOB="$KEYS_BLOB" \
python3 <<'PY'
import json, os, sys

cfg_path  = os.environ["CONFIG_PATH"]
tools_dir = os.environ["TOOLS_DIR_E"]
slugs     = os.environ["SLUGS_E"].split()

presets = {}
for line in os.environ["PRESETS_BLOB"].strip().splitlines():
    s, repo, env_var, display, dirname = line.split("|")
    presets[s] = {"env_var": env_var, "dirname": dirname}

keys = {}
for line in os.environ["KEYS_BLOB"].splitlines():
    if "\t" in line:
        s, k = line.split("\t", 1)
        keys[s] = k

# Read existing config; fail LOUD if malformed (don't silently clobber).
if os.path.exists(cfg_path):
    with open(cfg_path) as f:
        raw = f.read().strip()
    if not raw:
        cfg = {}
    else:
        try:
            cfg = json.loads(raw)
        except Exception as e:
            print(f"ERROR: Existing config has invalid JSON: {e}", file=sys.stderr)
            print(f"       Inspect {cfg_path} and fix it before rerunning.", file=sys.stderr)
            print(f"       Your original was just backed up to a sibling .bak.* file.", file=sys.stderr)
            sys.exit(2)
else:
    cfg = {}
if not isinstance(cfg, dict):
    print("ERROR: Existing config is not a JSON object — aborting.", file=sys.stderr)
    sys.exit(2)

mcp = cfg.setdefault("mcpServers", {})

for s in slugs:
    p = presets[s]
    entry_path = os.path.join(tools_dir, p["dirname"], "dist", "index.js")
    existing = mcp.get(s, {}) if isinstance(mcp.get(s), dict) else {}
    existing_env = existing.get("env", {}) if isinstance(existing, dict) else {}
    new_key = keys.get(s, "")
    final_key = new_key if new_key else existing_env.get(p["env_var"], f"PASTE_YOUR_{p['env_var']}_HERE")
    env = {p["env_var"]: final_key}

    # keepa-adapter: pin the SQLite path so it doesn't crash with SQLITE_CANTOPEN
    if s == "keepa":
        env.setdefault("KEEPA_DB_PATH", os.path.join(tools_dir, p["dirname"], "keepa.db"))
        env.setdefault("KEEPA_DEFAULT_DOMAIN", "com")

    # Preserve any extra env vars the user already had on this server
    for ek, ev in (existing_env.items() if isinstance(existing_env, dict) else []):
        if ek != p["env_var"] and ek not in env:
            env[ek] = ev

    mcp[s] = {"command": "node", "args": [entry_path], "env": env}

with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")

print("Top-level keys:", list(cfg.keys()))
print("mcpServers now:", sorted(mcp.keys()))
PY

# ── Validate ──────────────────────────────────────────────────────────────────
python3 -m json.tool "$CONFIG" >/dev/null && ok "JSON valid"

cat <<EOF

────────────────────────────────────────────────────────────
✓ Config:  $CONFIG
✓ Backup:  ${CONFIG}.bak.${TS}

NEXT — relaunch Claude Desktop:

  open -a "Claude"

Don't change any settings yet. Test in chat:
  • "Check my Keepa token status"
  • "List my DataDive niches"
  • "Search SmartScout for ASIN B0XXXXXXXX"

If a 401 / auth error comes back, your key was wrong. Fix:
  bash $0 --reset-keys ${SLUGS[*]}
────────────────────────────────────────────────────────────
EOF
