#!/bin/bash
set -e

SUB_URL="https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/protocols/vless"
TMP_PING="ping_results.txt"
TMP_LIST="all_nodes.txt"
TMP_FILTERED="filtered.txt"
TMP_SUB="filtered_sub.txt"

# Add subscription (skip if already added)
v2sub add "$SUB_URL" 2>/dev/null || echo "Subscribe already added"

# Update nodes
v2sub update

# Test delay, store results
v2sub ping > "$TMP_PING"

# Find indexes of nodes with delay < 200ms
FAST_INDEXES=$(awk '/ms$/ && $NF+0 < 200 {print NR-1}' "$TMP_PING")

# List all nodes to a file (plain text)
v2sub list > "$TMP_LIST"

# Extract the corresponding lines for fast nodes
> "$TMP_FILTERED"
for idx in $FAST_INDEXES; do
    # v2sub list output is typically 1-based; adjust if needed
    NODE_LINE=$(sed -n "$((idx+1))p" "$TMP_LIST")
    echo "$NODE_LINE" >> "$TMP_FILTERED"
done

# Optionally encode as base64 for use as a subscription link
base64 -w 0 "$TMP_FILTERED" > "$TMP_SUB"

echo "Filtered and encoded subscription is ready in $TMP_SUB"
