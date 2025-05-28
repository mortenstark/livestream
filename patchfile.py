#!/usr/bin/env python3
import sys
import re
import argparse
from pathlib import Path

def apply_unified_diff(source_content, patch_content, debug=False):
    """Apply a unified diff to source content."""
    source_lines = source_content.splitlines()
    patch_lines = patch_content.splitlines()

    # Skip patch header lines (--- and +++ lines)
    i = 0
    while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
        i += 1

    if i >= len(patch_lines):
        print("Error: No hunk markers found in patch")
        return source_content

    result_lines = source_lines[:]

    # Process each hunk
    while i < len(patch_lines):
        line = patch_lines[i]

        if line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            hunk_match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if not hunk_match:
                print(f"Error: Invalid hunk header: {line}")
                i += 1
                continue

            old_start = int(hunk_match.group(1)) - 1  # Convert to 0-based index
            old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
            new_start = int(hunk_match.group(3)) - 1  # Convert to 0-based index
            new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

            if debug:
                print(f"Hunk: old_start={old_start}, old_count={old_count}, new_start={new_start}, new_count={new_count}")

            # Collect hunk lines
            i += 1
            hunk_lines = []
            while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
                hunk_lines.append(patch_lines[i])
                i += 1

            # Apply the hunk
            result_lines = apply_hunk(result_lines, old_start, old_count, hunk_lines, debug)
        else:
            i += 1

    # Join lines and preserve original line ending style
    result = '\n'.join(result_lines)
    if source_content.endswith('\n'):
        result += '\n'

    return result

def apply_hunk(source_lines, old_start, old_count, hunk_lines, debug=False):
    """Apply a single hunk to source lines."""
    if debug:
        print(f"Applying hunk at line {old_start + 1}")

    # Parse hunk lines into context, additions, and deletions
    context_lines = []
    additions = []
    deletions = []

    for line in hunk_lines:
        if line.startswith(' '):  # Context line
            context_lines.append(line[1:])
        elif line.startswith('+'):  # Addition
            additions.append(line[1:])
        elif line.startswith('-'):  # Deletion
            deletions.append(line[1:])

    if debug:
        print(f"Context lines: {len(context_lines)}")
        print(f"Additions: {len(additions)}")
        print(f"Deletions: {len(deletions)}")

    # Build the new content
    result = source_lines[:]

    # For simple additions at the end (like your case), we can handle it easily
    if len(deletions) == 0 and len(context_lines) > 0:
        # Find where to insert the new lines
        # Look for the last context line to determine insertion point
        last_context = context_lines[-1] if context_lines else ""

        # Find the insertion point after the existing content
        insert_point = old_start + old_count

        # Insert the new lines
        for i, add_line in enumerate(additions):
            result.insert(insert_point + i, add_line)

        if debug:
            print(f"Inserted {len(additions)} lines at position {insert_point}")

    else:
        # More complex case with deletions - replace the old range with new content
        new_lines = []

        # Process hunk lines in order
        for line in hunk_lines:
            if line.startswith(' '):  # Keep context lines
                new_lines.append(line[1:])
            elif line.startswith('+'):  # Add new lines
                new_lines.append(line[1:])
            # Skip deletion lines (they're removed)

        # Replace the old range with new content
        result[old_start:old_start + old_count] = new_lines

        if debug:
            print(f"Replaced {old_count} lines with {len(new_lines)} lines")

    return result

def main():
    parser = argparse.ArgumentParser(description="Apply unified diff patches")
    parser.add_argument('source_file', help='File to patch')
    parser.add_argument('patch_file', help='Patch file to apply')
    parser.add_argument('--output', help='Output file (default: overwrite source)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    try:
        # Read files
        with open(args.source_file, 'r', encoding='utf-8') as f:
            source_content = f.read()

        with open(args.patch_file, 'r', encoding='utf-8') as f:
            patch_content = f.read()

        # Apply patch
        patched_content = apply_unified_diff(source_content, patch_content, args.debug)

        # Check if content changed
        if source_content == patched_content:
            print("Warning: Content unchanged after patching")
        else:
            print("Content successfully changed")

        # Write result
        output_file = args.output or args.source_file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(patched_content)

        print(f"Successfully patched {args.source_file} to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()