#!/bin/bash
# Release the de-marketplace-listing plugin: bump version, validate, deploy
# to all three live locations, byte-verify, and build the .plugin archive.
#
# Usage: scripts/release.sh <version>        e.g. scripts/release.sh 2.5.9
#
# Does NOT commit/push (commit messages are bespoke) and does NOT restart
# the Claude app (user does that manually). Safe to re-run after a failure.
set -euo pipefail

VERSION="${1:?usage: release.sh <version>}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "ERROR: version must be X.Y.Z, got '$VERSION'"; exit 1; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/plugin-source"
ARCHIVE="$ROOT/de-marketplace-listing-$VERSION.plugin"
CACHE="$HOME/.claude/plugins/cache/local-desktop-app-uploads/de-marketplace-listing/$VERSION"

# --- locate the session-dependent deploy targets ------------------------------
find_target() { # newest match wins; the session dir changes over time
  local pattern="$1" label="$2"
  local matches=()
  while IFS= read -r -d '' d; do matches+=("$d"); done \
    < <(find "$HOME/Library/Application Support/Claude/local-agent-mode-sessions" \
        -maxdepth 6 -type d -path "$pattern" -print0 2>/dev/null)
  [[ ${#matches[@]} -gt 0 ]] || { echo "ERROR: no $label dir found" >&2; exit 1; }
  if [[ ${#matches[@]} -gt 1 ]]; then
    echo "WARNING: ${#matches[@]} $label dirs found, using newest" >&2
    ls -td "${matches[@]}" | head -1
  else
    echo "${matches[0]}"
  fi
}
RPM="$(find_target "*/rpm/plugin_01WmsnTfPwfzreKj4Ezh2Kmx" "rpm")"
COWORK="$(find_target "*/cowork_plugins/marketplaces/local-desktop-app-uploads/de-marketplace-listing" "cowork source")"

echo "==> Releasing $VERSION"
echo "    rpm:    $RPM"
echo "    cowork: $COWORK"
echo "    cache:  $CACHE"

# --- 1. version bump (idempotent) ---------------------------------------------
# The PLUGIN_VERSION_LINE in every SKILL.md is the ONLY version a running skill
# can see — a skill loaded via the Skill tool cannot read plugin.json. If this
# stamp is ever missed, runs fall back to guessing (v2.6.4 shipped with the
# version only as an "e.g." example and four runs invented "2.2.1").
sed -i '' "s/\"version\": \"[0-9.]*\"/\"version\": \"$VERSION\"/" "$SRC/.claude-plugin/plugin.json"
sed -i '' "s/^PLUGIN_VERSION: .*/PLUGIN_VERSION: $VERSION/" "$ROOT/evals/fixtures/sample-action-file.md"
BUMPED=("$SRC/.claude-plugin/plugin.json" "$ROOT/evals/fixtures/sample-action-file.md")
for s in "$SRC"/skills/*/SKILL.md; do
  grep -q "PLUGIN_VERSION_LINE" "$s" || { echo "ERROR: no PLUGIN_VERSION_LINE marker in $s"; exit 1; }
  sed -i '' "s/\*\*Plugin version: [0-9.]*\.\*\*/**Plugin version: $VERSION.**/" "$s"
  BUMPED+=("$s")
done
for f in "${BUMPED[@]}"; do
  grep -q "$VERSION" "$f" || { echo "ERROR: version bump failed in $f"; exit 1; }
done
echo "==> Version bumped in ${#BUMPED[@]} files"

# --- 2. validation gate --------------------------------------------------------
python3 -c "import json; json.load(open('$ROOT/evals/evals.json'))" \
  || { echo "ERROR: evals.json is not valid JSON"; exit 1; }
python3 "$SRC/scripts/validate_action_file.py" "$ROOT/evals/fixtures/sample-action-file.md" \
  "$ROOT/evals/fixtures/test-config.md" \
  || { echo "ERROR: golden fixture failed validation"; exit 1; }
echo "==> Validator gate passed"

# --- 3. deploy (rpm keeps its leftover .git/.gitignore untouched) --------------
mkdir -p "$CACHE"
for target in "$RPM" "$COWORK" "$CACHE"; do
  rsync -a --delete --exclude=.git --exclude=.gitignore --exclude=.orphaned_at \
    "$SRC/" "$target/"
  diff -r --exclude=.git --exclude=.gitignore --exclude=.orphaned_at "$SRC" "$target" \
    || { echo "ERROR: $target not byte-identical after deploy"; exit 1; }
done
echo "==> Deployed + byte-verified: rpm, cowork source, cache"

# --- 3b. point the Claude Code install record at the new cache dir -------------
# (lesson 8: part of the convention; was missed 2.5.6…2.6.5 — CLI sessions sat on 2.5.5)
python3 - "$VERSION" "$CACHE" <<'PY'
import json, sys, datetime
ver, path = sys.argv[1], sys.argv[2]
p = "/Users/janniswerner/.claude/plugins/installed_plugins.json"
d = json.load(open(p))
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
for e in d["plugins"].get("de-marketplace-listing@local-desktop-app-uploads", []):
    e["installPath"] = path; e["version"] = ver; e["lastUpdated"] = now
json.dump(d, open(p, "w"), indent=2)
PY
echo "==> installed_plugins.json → $VERSION"

# --- 4. archive (store; the eval suite lives at repo level and is not shipped) -
rm -f "$ARCHIVE"
(cd "$SRC" && zip -0 -r -X -q "$ARCHIVE" . \
  -x ".git/*" -x ".gitignore")

# verify: archive regular files == source files minus exclusions
expected="$(cd "$SRC" && find . -type f ! -path "./.git/*" ! -name .gitignore \
  | sed 's|^\./||' | sort)"
actual="$(zipinfo -1 "$ARCHIVE" | grep -v '/$' | sort)"
diff <(echo "$expected") <(echo "$actual") \
  || { echo "ERROR: archive file list does not match source"; exit 1; }
echo "==> Archive: $ARCHIVE ($(echo "$actual" | wc -l | tr -d ' ') files, $(du -h "$ARCHIVE" | cut -f1 | tr -d ' '))"

echo "==> DONE, LOCALLY. Remaining: git commit + push, then the deploy is NOT finished until you"
echo "    UPLOAD $ARCHIVE to the account's plugin \"My Uploads\"."
echo "    WHY THIS MATTERS: for a plugin present in My Uploads, the Claude app loads the ACCOUNT"
echo "    copy, not what this script writes to rpm/cowork/cache (main.log: \"exists in both remote"
echo "    and local. Using remote.\"). So without the upload, NOTHING you changed here actually runs."
echo "    No CLI exists for it: Settings -> Plugins -> Add -> Upload plugin -> pick the .plugin ->"
echo "    Upload -> Replace. Claude can do this via the claude.ai Plugins page on request."
