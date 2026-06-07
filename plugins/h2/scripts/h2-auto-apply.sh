#!/bin/sh
# h2-auto-apply.sh — apply newer h2 plugin payloads to already bootstrapped targets.

set -eu

INPUT=$(cat || true)

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
plugin_root=${CLAUDE_PLUGIN_ROOT:-}
if [ -z "$plugin_root" ]; then
    plugin_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
fi

project_dir=${CLAUDE_PROJECT_DIR:-}
if [ -z "$project_dir" ]; then
    project_dir=$(printf '%s' "$INPUT" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
fi
if [ -z "$project_dir" ]; then
    project_dir=$(pwd)
fi

target=$project_dir
if command -v git >/dev/null 2>&1; then
    git_root=$(git -C "$project_dir" rev-parse --show-toplevel 2>/dev/null || true)
    if [ -n "$git_root" ]; then
        target=$git_root
    fi
fi

manifest="$target/.harness-helm/install-manifest.json"
doctor_dir="$target/.harness-helm/doctor"
log_path="$doctor_dir/auto-apply-latest.json"
lock_dir="$doctor_dir/auto-apply.lock"

json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

write_log() {
    result=$1
    reason=$2
    error=${3:-}
    mkdir -p "$doctor_dir"
    now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    cat > "$log_path" <<EOF
{
  "schema_version": 1,
  "mode": "auto-apply",
  "target": "$(json_escape "$target")",
  "target_version": "$(json_escape "${target_version:-}")",
  "payload_version": "$(json_escape "${payload_version:-}")",
  "result": "$(json_escape "$result")",
  "reason": "$(json_escape "$reason")",
  "install_manifest": ".harness-helm/install-manifest.json",
  "started_at": "$(json_escape "${started_at:-$now}")",
  "completed_at": "$now",
  "errors": [$(if [ -n "$error" ]; then printf '"%s"' "$(json_escape "$error")"; fi)]
}
EOF
}

if [ ! -f "$manifest" ]; then
    exit 0
fi

mkdir -p "$doctor_dir"
if ! mkdir "$lock_dir" 2>/dev/null; then
    # Another hook or guard is already checking this target. Avoid duplicate apply.
    exit 0
fi
trap 'rmdir "$lock_dir" 2>/dev/null || true' EXIT

started_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

status=$(sed -n 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$manifest" | head -n 1)
target_version=$(sed -n 's/.*"package_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$manifest" | head -n 1)

if [ "$status" != "ok" ]; then
    write_log "skipped-recovery-required" "install-manifest status is not ok"
    echo "h2 auto-apply skipped: target recovery required. Run /h2:doctor." >&2
    exit 0
fi
if [ -z "$target_version" ]; then
    write_log "skipped-recovery-required" "install-manifest package_version missing"
    echo "h2 auto-apply skipped: package_version missing. Run /h2:doctor." >&2
    exit 0
fi

version_gt() {
    left=${1#v}
    right=${2#v}
    IFS=. read -r lmaj lmin lpatch <<EOF
$left
EOF
    IFS=. read -r rmaj rmin rpatch <<EOF
$right
EOF
    for pair in "$lmaj:$rmaj" "$lmin:$rmin" "$lpatch:$rpatch"; do
        l=${pair%:*}
        r=${pair#*:}
        if [ "$l" -gt "$r" ]; then
            return 0
        fi
        if [ "$l" -lt "$r" ]; then
            return 1
        fi
    done
    return 1
}

semver_ok() {
    case "$1" in
        v[0-9]*.[0-9]*.[0-9]*|[0-9]*.[0-9]*.[0-9]*) return 0 ;;
        *) return 1 ;;
    esac
}

package_root="$plugin_root/release/h2-install"
payload_version=""
for marker in "$package_root"/h2-install-v*.txt; do
    [ -f "$marker" ] || continue
    name=$(basename "$marker" .txt)
    candidate=${name#h2-install-}
    if semver_ok "$candidate"; then
        if [ -z "$payload_version" ] || version_gt "$candidate" "$payload_version"; then
            payload_version=$candidate
        fi
    fi
done

if [ -z "$payload_version" ]; then
    write_log "failed" "plugin payload marker missing" "release/h2-install/h2-install-v*.txt not found"
    echo "h2 auto-apply failed: plugin payload marker missing. Run /h2:doctor." >&2
    exit 0
fi
if ! semver_ok "$target_version"; then
    write_log "skipped-recovery-required" "target package_version is invalid"
    echo "h2 auto-apply skipped: invalid target package_version. Run /h2:doctor." >&2
    exit 0
fi

if version_gt "$target_version" "$payload_version"; then
    write_log "skipped-downgrade" "target version is newer than plugin payload"
    exit 0
fi
if ! version_gt "$payload_version" "$target_version"; then
    write_log "skipped-noop" "target version matches plugin payload"
    exit 0
fi

wrapper="$plugin_root/release/h2-install.sh"
if [ ! -x "$wrapper" ]; then
    write_log "failed" "plugin install wrapper missing or not executable" "$wrapper"
    echo "h2 auto-apply failed: install wrapper missing. Run /h2:doctor." >&2
    exit 0
fi

tmp_out="$doctor_dir/auto-apply.out"
tmp_err="$doctor_dir/auto-apply.err"
if "$wrapper" --target "$target" --backup >"$tmp_out" 2>"$tmp_err"; then
    rm -f "$tmp_out" "$tmp_err"
	write_log "applied" "target package_version < plugin payload version"
	exit 0
fi

err=$(cat "$tmp_err" 2>/dev/null || true)
rm -f "$tmp_out" "$tmp_err"
write_log "failed" "install wrapper failed" "$err"
echo "h2 auto-apply failed. Run /h2:doctor to recover." >&2
exit 0
