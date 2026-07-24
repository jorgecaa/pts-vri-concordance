#!/usr/bin/env bash
# build_index.sh
# Scans all rota text files and produces a TSV index:
#   PTS_LABEL   FILENAME   LINE_OFFSET
#
# PTS_LABEL format: NIKAYA_VOLUME_PAGE  (e.g. D_2_2, M_1_5)
# LINE_OFFSET is the 0-based line number where the marker appears.

ROTA_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_FILE="${ROTA_DIR}/index.tsv"

# Clear output
> "$OUTPUT_FILE"

# Roman numeral to integer
roman_to_int() {
    case "$1" in
        I)   echo 1 ;;
        II)  echo 2 ;;
        III) echo 3 ;;
        IV)  echo 4 ;;
        V)   echo 5 ;;
        VI)  echo 6 ;;
        VII) echo 7 ;;
        VIII) echo 8 ;;
        IX)  echo 9 ;;
        X)   echo 10 ;;
        XI)  echo 11 ;;
        XII) echo 12 ;;
        *)   echo "$1" ;;
    esac
}

# Process each .txt file (skip non-text files)
for txtfile in "${ROTA_DIR}"/*.txt; do
    [ -f "$txtfile" ] || continue
    filename="$(basename "$txtfile")"

    # Use grep -nP to find lines with PTS markers and get line numbers
    # Pattern: < PTS. <NIKAYA> <VOLUME> , <PAGE> >
    # (spacing around comma may vary)
    grep -nP '< PTS\.\s+[A-Za-z]+\s+[IVX0-9]+\s*,\s*[0-9]+\s*>' "$txtfile" 2>/dev/null | while IFS=: read -r line_num matched_line; do
        # Extract nikaya, volume, page
        nikaya=$(echo "$matched_line" | grep -oP '< PTS\.\s+\K[A-Za-z]+')
        volume=$(echo "$matched_line" | grep -oP '< PTS\.\s+[A-Za-z]+\s+\K[IVX0-9]+')
        page=$(echo "$matched_line" | grep -oP '< PTS\.\s+[A-Za-z]+\s+[IVX0-9]+\s*,\s*\K[0-9]+')

        vol_int=$(roman_to_int "$volume")
        label="${nikaya}_${vol_int}_${page}"
        # grep -n uses 1-based line numbers, convert to 0-based
        line_offset=$((line_num - 1))

        printf '%s\t%s\t%s\n' "$label" "$filename" "$line_offset"
    done >> "$OUTPUT_FILE" || true
done

echo "Index built: $OUTPUT_FILE"
echo "Total entries: $(wc -l < "$OUTPUT_FILE")"
