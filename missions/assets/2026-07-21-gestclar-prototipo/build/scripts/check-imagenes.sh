#!/bin/bash
# check-imagenes.sh
# Checks all HTML files in the prototipo directory for local image src references
# and verifies whether the corresponding image files exist.
#
# Usage: Run from the prototipo parent directory (e.g., the mission root)
#   bash prototipo/scripts/check-imagenes.sh
# Or from inside the prototipo directory:
#   bash scripts/check-imagenes.sh

set -euo pipefail

# Determine prototipo root: this script lives in prototipo/scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTOTIPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== check-imagenes.sh ==="
echo "Prototipo dir: $PROTOTIPO_DIR"
echo ""

OK=0
MISSING=0
TOTAL=0

# Find all HTML files
while IFS= read -r -d '' html_file; do
  # Extract all src="/assets/img/..." references
  while IFS= read -r img_src; do
    # Strip leading/trailing whitespace and quotes
    img_src="$(echo "$img_src" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [ -z "$img_src" ] && continue

    TOTAL=$((TOTAL + 1))

    # Convert URL path to filesystem path
    # /assets/img/foo.png -> prototipo/assets/img/foo.png
    img_path="$PROTOTIPO_DIR${img_src}"

    rel_html="${html_file#$PROTOTIPO_DIR/}"

    if [ -f "$img_path" ]; then
      echo "  OK      $img_src  (ref'd in $rel_html)"
      OK=$((OK + 1))
    else
      echo "  MISSING $img_src  (ref'd in $rel_html)"
      MISSING=$((MISSING + 1))
    fi
  done < <(grep -oP 'src="\K/assets/img/[^"]+' "$html_file" 2>/dev/null || true)
done < <(find "$PROTOTIPO_DIR" -name "*.html" -print0 2>/dev/null)

echo ""
echo "=== Summary ==="
echo "Total image references checked: $TOTAL"
echo "OK:      $OK"
echo "MISSING: $MISSING"

if [ "$MISSING" -gt 0 ]; then
  echo ""
  echo "Action needed: add the missing images to $PROTOTIPO_DIR/assets/img/"
  exit 1
else
  echo ""
  echo "All images accounted for."
  exit 0
fi
