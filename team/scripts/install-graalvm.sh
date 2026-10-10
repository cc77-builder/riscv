#!/usr/bin/env bash
set -euo pipefail
# Fixed official archive; no sudo and no changing the user's shell configuration.
DEST=${JAVA_HOME:-"$HOME/.local/share/graalvm-jdk-21.0.12"}
CACHE=${XDG_CACHE_HOME:-"$HOME/.cache"}/riscv-team
ARCHIVE=graalvm-jdk-21.0.12_linux-x64_bin.tar.gz
SHA256=b007ff64c425f85bbe0e686107044fba6ca5054a7e89271a473767f546aaddc1
test "$(uname -m)" = x86_64
if test -x "$DEST/bin/java"; then
  info=$("$DEST/bin/java" -version 2>&1)
  [[ "$info" == *'"21.0.12"'* && "$info" == *GraalVM* ]]
  echo "GRAALVM_ALREADY_MATCHES: $DEST"
  exit 0
fi
if test -d "$DEST" && test -n "$(ls -A "$DEST")"; then
  echo "Destination is nonempty; choose a new JAVA_HOME: $DEST" >&2
  exit 1
fi
mkdir -p "$CACHE"
curl -fL --retry 3 -o "$CACHE/$ARCHIVE" "https://download.oracle.com/graalvm/21/archive/$ARCHIVE"
printf '%s  %s\n' "$SHA256" "$CACHE/$ARCHIVE" | sha256sum -c -
mkdir -p "$DEST"
tar -xzf "$CACHE/$ARCHIVE" -C "$DEST" --strip-components=1
info=$("$DEST/bin/java" -version 2>&1)
[[ "$info" == *'"21.0.12"'* && "$info" == *GraalVM* ]]
printf '%s\n' "$info"
echo "GRAALVM_INSTALL_PASS: set JAVA_HOME=$DEST before sourcing activate.sh"
