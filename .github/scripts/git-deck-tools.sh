#!/bin/bash
# GitHub settings
#set -x
GIT_ROOT="$(git rev-parse --show-toplevel)"
GITHUB_TOKEN="${GITHUB_TOKEN}"
GITHUB_REPO="YOUR_USERNAME/YOUR_REPOSITORY" # Format: username/repo
DECK_BASE_DIRECTORY="$GIT_ROOT/.pm/deck" # Your base directory for boards

# Default values for options
option_output='info'
pm_file="$GIT_ROOT/.pm/pm.md"
md_file="$GIT_ROOT/DECK.md"
collect_options() {
    # Parse options using getopts
    while getopts ":o:-:" opt; do
        case $opt in
            o)
                option_output="$OPTARG"
                ;;
            -)
                case "${OPTARG}" in
                    output)
                        option_output="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                        ;;
                    md-file)
                        md_file="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                        ;;
                    pm-file)
                        pm_file="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                        ;;
                    *)
                        echo "Invalid option: --${OPTARG}" >&2
                        return 1
                        ;;
                esac
                ;;
            \?)
                echo "Invalid option: -$OPTARG" >&2
                return 1
                ;;
            :)
                echo "Option -$OPTARG requires an argument." >&2
                return 1
                ;;
        esac
    done
    option_output=$(echo "$option_output" | tr '[:upper:]' '[:lower:]')
}

# Function to extract git-deck cards' headers
extract_md_headers() {
    local file="$1"
    declare -A headers

    # Extract the header into a variable, ignoring comment lines
    header=$(awk '
        BEGIN { in_header=0 }
        /^---/ {
            in_header=1-in_header; 
            if (in_header == 0) exit # Exit after the second ---
            next # Skip the --- lines
        }
        in_header && length($0) > 0 && !/^[[:space:]]*#/ { print }
    ' "$file")

    # Process each line of the header
    while IFS= read -r line; do
        if [[ ! -z "$line" ]]; then
            key=$(echo "$line" | cut -d':' -f1 | xargs)
            value=$(echo "$line" | cut -d':' -f2- | xargs)
            if [[ -n "$key" ]]; then
                headers["$key"]="$value"
            fi
        fi
    done <<< "$header"

    # Return the associative array
    declare -p headers
}
# Wrapper function that passes all parameters to the main function
extract_status_headers() {
    extract_md_headers "$@"  # Pass all parameters to the main function
}

# Function to extract git-deck cards' body
extract_md_body() {
    local file="$1"
    # Get the content after the second ---
    content=$(awk '
        BEGIN { in_header=0; second_dash_found=0 }
        /^---/ {
            if (in_header) {
                second_dash_found=1;
                in_header=0;
                next;
            }
            in_header=1;
            next;
        }
        second_dash_found { print }
    ' "$file")
    echo -e "$content"
}

# Function to generate a markdown file (DECK.md) from git-deck boards
generate_markdown() {
    return_value=0

    # Clear the output file if it exists
    if [ -f "$pm_file" ]; then
        cat "$pm_file" > "$md_file"
    else
        > "$md_file"
    fi

    # Loop through each board folder
    for board in $DECK_BASE_DIRECTORY/*; do
        # Read board ID from .id file
        board_id=$(<"$board/.id")
        board_name=$(basename "$board")

        # Write the board header only once
        echo "# $board_id - $board_name" >> "$md_file"

        # Loop through each column folder
        for column in "$board"/*; do
            column_name=$(basename "$column")

            # Loop through each card file in the column
            for card in "$column"/*; do
                if [[ $(basename "$card") =~ ^[0-9]{1,4}$ ]]; then
                    card_headers=$(extract_md_headers "$card")
                    eval "$card_headers"  # Evaluate to create the associative array

                    # Get the title from headers, default to "Untitled" if not found
                    card_title="${headers[Title]:-Untitled}"

                    # Initialize card_content and check if headers_output is not empty
                    card_content=""
                    if [[ -n "$card_headers" ]]; then
                        # Get the content after the second ---
                        card_content=$(extract_md_body "$card")
                    fi

                    # Read the status file for statustext and statusdetails
                    config_file="$column/.config"
                    if [[ -f "$config_file" ]]; then
                        config_headers=$(extract_status_headers "$config_file")
                        eval "$config_headers"  # Evaluate to create associative array
                        # Extract values for statustext and statusdetails
                        statustext="${headers[statustext]:-}"
                        statusdetails="${headers[statusdetails]:-}"
                    fi

                    # Get the card ID from the filename
                    card_id=$(basename "$card")
                    board_id_fix=$(printf "%03d" "$board_id")

                    # Write card details to the output markdown file
                    {
                        echo ""
                        echo "## $board_id_fix-$card_id"
                        echo "> **$card_title** ${statustext:-$column_name}"
                        echo "> <details ${statusdetails}>"
                        echo ">     <summary>Details</summary>"

                        # Indent each line of card_content with >
                        while IFS= read -r line; do
                            echo "> $line"
                        done <<< "$card_content"

                        echo "> </details>"
                    } >> "$md_file"
                fi
            done
        done
    done
    return $return_value
}

# Main
command="$1"
command=$(echo "$command" | tr '[:upper:]' '[:lower:]')
shift 1 # Shift past the first two parameters
collect_options "${@}"

case "$command" in
    generate-markdown)
            generate_markdown "${@}"
            exit $?
        ;;
    *)
        echo "Invalid card command. Usage: $(basename $0) {generate-markdown}"
        ;;
esac
