#!/bin/sh
# h2-install.sh — POSIX bootstrap for harness-helm install.
# Resolves the host Go harness binary, verifies its SHA256 sidecar, then
# delegates to `harness install`.

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PACKAGE_ROOT="$SCRIPT_DIR/h2-install"
MANIFEST="$PACKAGE_ROOT/MANIFEST.txt"

if [ ! -f "$MANIFEST" ]; then
    echo "h2-install: MANIFEST.txt not found at $MANIFEST" >&2
    exit 1
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

VERSION=""
for marker in "$PACKAGE_ROOT"/h2-install-v*.txt; do
    [ -f "$marker" ] || continue
    name=$(basename "$marker" .txt)
    candidate=${name#h2-install-}
    case "$candidate" in
        v[0-9]*.[0-9]*.[0-9]*)
            if [ -z "$VERSION" ] || version_gt "$candidate" "$VERSION"; then
                VERSION="$candidate"
            fi
            ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "h2-install: version marker not found in $PACKAGE_ROOT" >&2
    exit 1
fi

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m | tr '[:upper:]' '[:lower:]')
case "$OS" in
    darwin) GOOS=darwin ;;
    linux) GOOS=linux ;;
    *) echo "h2-install: unsupported platform: $OS/$ARCH" >&2; exit 1 ;;
esac
case "$ARCH" in
    arm64|aarch64) GOARCH=arm64 ;;
    x86_64|amd64) GOARCH=amd64 ;;
    *) echo "h2-install: unsupported platform: $OS/$ARCH" >&2; exit 1 ;;
esac

ASSET="harness-$VERSION-$GOOS-$GOARCH"
RELEASE_BASE=${H2_HARNESS_RELEASE_BASE:-"https://github.com/dandihera/harness-helm-claude-plugin/releases/download/$VERSION"}
TMP_DIR=$(mktemp -d -t h2-install-XXXXXX)
trap 'rm -rf "$TMP_DIR"' EXIT
RUNTIME_BINARY="$TMP_DIR/$ASSET"
CHECKSUM_FILE="$TMP_DIR/$ASSET.sha256"

fetch() {
    src="$1"
    dst="$2"
    case "$src" in
        file://*)
            cp "${src#file://}" "$dst"
            ;;
        /*|.*)
            cp "$src" "$dst"
            ;;
        http://*|https://*)
            if command -v curl >/dev/null 2>&1; then
                curl -fsSL "$src" -o "$dst"
            elif command -v wget >/dev/null 2>&1; then
                wget -qO "$dst" "$src"
            else
                echo "h2-install: curl or wget required to download release asset" >&2
                return 1
            fi
            ;;
        *)
            cp "$src" "$dst"
            ;;
    esac
}

BASE=${RELEASE_BASE%/}
fetch "$BASE/$ASSET" "$RUNTIME_BINARY" || {
    echo "h2-install: release asset not found: $BASE/$ASSET" >&2
    exit 1
}
fetch "$BASE/$ASSET.sha256" "$CHECKSUM_FILE" || {
    echo "h2-install: checksum sidecar not found: $BASE/$ASSET.sha256" >&2
    exit 1
}

EXPECTED=$(awk 'NF >= 1 {print $1; exit}' "$CHECKSUM_FILE")
case "$EXPECTED" in
    [0-9a-fA-F][0-9a-fA-F]*) ;;
    *) echo "h2-install: malformed checksum sidecar: $CHECKSUM_FILE" >&2; exit 1 ;;
esac

if command -v sha256sum >/dev/null 2>&1; then
    ACTUAL=$(sha256sum "$RUNTIME_BINARY" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
    ACTUAL=$(shasum -a 256 "$RUNTIME_BINARY" | awk '{print $1}')
else
    echo "h2-install: sha256sum or shasum required" >&2
    exit 1
fi

if [ "$(printf '%s' "$EXPECTED" | tr '[:upper:]' '[:lower:]')" != "$(printf '%s' "$ACTUAL" | tr '[:upper:]' '[:lower:]')" ]; then
    echo "h2-install: checksum mismatch for $ASSET" >&2
    exit 1
fi

chmod +x "$RUNTIME_BINARY"
if ! "$RUNTIME_BINARY" --help >/dev/null 2>&1; then
    echo "h2-install: downloaded binary launch check failed: $ASSET" >&2
    exit 1
fi

HAS_TARGET=0
for arg in "$@"; do
    case "$arg" in
        --target|--target=*) HAS_TARGET=1 ;;
    esac
done

if [ $HAS_TARGET -eq 0 ]; then
    set -- --target . "$@"
fi

exec "$RUNTIME_BINARY" install --manifest "$MANIFEST" --runtime-binary "$RUNTIME_BINARY" "$@"
