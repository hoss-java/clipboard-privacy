#!/bin/bash
#set -x
# Get the commit ID from the environment variable
COMMIT_ID="$1"
if [ -z "$COMMIT_ID" ]; then
    #echo "ERROR: Commit ID is required."
    exit 1
fi

# Fetch the commit message for the given commit ID
commit_msg_full="$(git log --format=%B -n 1 "$COMMIT_ID")"

# Separate lines in the commit message
#commit_msg_lines=($(echo "$commit_msg_full" | awk 'BEGIN{RS=""; FS="\r"} {for(i=2;i<=NF;i++) print $i}'))
# Separate lines in the commit message starting from the second line
commit_msg_lines=($(echo "$commit_msg_full" | awk 'NR > 1'))

# Initialize an array to hold directives
directives=()

# Loop through the lines starting from the second line
for line in "${commit_msg_lines[@]}"; do
    # Check if the line starts with `--` (indicating a directive)
    if [[ "$line" == --* ]]; then
        directives+=("$line")  # Add to the directives array
    fi
done

# Output results
if [ ${#directives[@]} -gt 0 ]; then
    #echo "Found directives:"
    for directive in "${directives[@]}"; do
        echo "$directive"
    done
else
    echo ""
    exit 0  # Return exit status 0 if no directives found to avoid action failure status
fi
