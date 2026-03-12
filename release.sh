#!/usr/bin/env bash
# Tag and push a new release from WSL. The GitHub Action builds the Windows exe
# and creates the release when it sees the new tag.
#
# Usage:
#   ./release.sh           # prompt for version
#   ./release.sh 1.0.3      # release as v1.0.3

set -e
cd "$(dirname "$0")"

# --- Version ---
VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  read -rp "Enter version number (e.g. 1.0.3): " VERSION
  if [[ -z "$VERSION" ]]; then
    echo "No version entered. Exiting."
    exit 1
  fi
fi
TAG="v${VERSION}"

# --- Tag and push ---
echo ""
echo "[1/2] Creating tag $TAG..."
git tag -a "$TAG" -m "Release $TAG"
echo ""
echo "[2/2] Pushing to GitHub..."
git push origin main
git push origin "$TAG"

echo ""
echo "Done. GitHub Action will build the Windows exe and create the release."
echo "Release: https://github.com/talkingtoaj/break-timer/releases/tag/$TAG"
