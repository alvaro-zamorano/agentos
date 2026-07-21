#!/bin/bash
# verificar.sh
# Finds all internal links (href="/...") in all HTML files in the prototipo directory,
# converts each path to a filesystem path, and checks whether the target file exists.
#
# Usage: Run from the prototipo parent directory (the directory that contains "prototipo/")
#   bash prototipo/scripts/verificar.sh
#
# The script resolves paths relative to the prototipo root:
#   /nosotros/          -> prototipo/nosotros/index.html
#   /assets/brand.css   -> prototipo/assets/brand.css

set -euo pipefail

# Determine prototipo root: this script lives in prototipo/scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTOTIPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== verificar.sh — Internal link checker ==="
echo "Prototipo dir: $PROTOTIPO_DIR"
echo ""

OK=0
MISSING=0
TOTAL=0

# Find all HTML files
while IFS= read -r -d '' html_file; do
  rel_html="${html_file#$PROTOTIPO_DIR/}"

  # Extract href="/..." values (internal absolute paths only, not http/https/mailto/tel/#)
  while IFS= read -r href; do
    href="$(echo "$href" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [ -z "$href" ] && continue

    TOTAL=$((TOTAL + 1))

    # Convert href path to a filesystem path
    # Strategy:
    #   /foo/bar/     -> prototipo/foo/bar/index.html  (trailing slash = directory)
    #   /foo/bar      -> prototipo/foo/bar             (no trailing slash, try as-is first)
    #   /assets/x.css -> prototipo/assets/x.css
    target_fs="$PROTOTIPO_DIR${href}"

    if [[ "$href" == */ ]]; then
      # Trailing slash: look for index.html
      candidate="${target_fs}index.html"
    else
      # No trailing slash: could be a file (e.g. .css, .js, .png) or a bare path
      if [[ "$href" == *.* ]]; then
        # Has an extension — treat as direct file
        candidate="$target_fs"
      else
        # No extension — try index.html
        candidate="${target_fs}/index.html"
      fi
    fi

    if [ -f "$candidate" ]; then
      echo "  OK      $href  (ref'd in $rel_html)"
      OK=$((OK + 1))
    else
      echo "  MISSING $href  ->  ${candidate#$PROTOTIPO_DIR/}  (ref'd in $rel_html)"
      MISSING=$((MISSING + 1))
    fi
  done < <(grep -oP 'href="\K/[^"#?][^"]*(?=")' "$html_file" 2>/dev/null \
           | grep -v '^https\?://' \
           | grep -v '^mailto:' \
           | grep -v '^tel:' \
           || true)
done < <(find "$PROTOTIPO_DIR" -name "*.html" -print0 2>/dev/null)

echo ""
echo "=== Summary ==="
echo "Total internal links checked: $TOTAL"
echo "OK:      $OK"
echo "MISSING: $MISSING"

if [ "$MISSING" -gt 0 ]; then
  echo ""
  echo "Note: MISSING links may point to pages not yet created in this prototype."
  echo "      External links (https://, mailto:, tel:) are excluded from this check."
  exit 1
else
  echo ""
  echo "All internal links resolve to existing files."
  exit 0
fi
