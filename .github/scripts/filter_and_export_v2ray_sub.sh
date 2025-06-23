#!/bin/bash
set -e

SUB_URL="https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/subscribe/protocols/vless"
TMP_PING="ping_results.txt"
TMP_NODES="nodes.json"
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

# Export current nodes to JSON
v2sub list --json > "$TMP_NODES"

# Extract corresponding nodes and format as VLESS, then save
> "$TMP_FILTERED"
for idx in $FAST_INDEXES; do
    URI=$(jq -r ".[$idx] | \"vless://\(.id)@\(.add):\(.port)?encryption=none&security=\(.tls? // \"none\")#\(.ps)\"" "$TMP_NODES")
    echo "$URI" >> "$TMP_FILTERED"
done

# Encode as base64 for use as a subscription link
base64 -w 0 "$TMP_FILTERED" > "$TMP_SUB"

echo "Filtered and encoded subscription is ready in $TMP_SUB"
