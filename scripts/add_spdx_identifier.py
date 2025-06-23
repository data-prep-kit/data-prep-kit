#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import os
import re
from pathlib import Path

def get_comment_prefix(file_extension):
    """Return the comment prefix based on file extension."""
    if file_extension == '.py':
        return '#'
    return None

def has_spdx_identifier(content):
    """Check if file already has SPDX identifier."""
    return 'SPDX-License-Identifier' in content

def add_spdx_identifier(file_path):
    """Add SPDX identifier to the file if it doesn't exist."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if has_spdx_identifier(content):
        print(f"Skipping {file_path} - already has SPDX identifier")
        return

    file_extension = os.path.splitext(file_path)[1]
    comment_prefix = get_comment_prefix(file_extension)
    
    if not comment_prefix:
        print(f"Skipping {file_path} - unsupported file type")
        return

    # Find the first non-empty line
    lines = content.split('\n')
    first_line_idx = 0
    for i, line in enumerate(lines):
        if line.strip():
            first_line_idx = i
            break

    # Add SPDX identifier
    spdx_line = f"{comment_prefix} SPDX-License-Identifier: Apache-2.0"
    
    # If file starts with shebang, add after it
    if lines[first_line_idx].startswith('#!'):
        lines.insert(first_line_idx + 1, spdx_line)
    else:
        lines.insert(first_line_idx, spdx_line)

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Added SPDX identifier to {file_path}")

def main():
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent

    # Only process Python files
    extension = '.py'

    # Walk through all directories
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(extension):
                file_path = os.path.join(root, file)
                add_spdx_identifier(file_path)

if __name__ == "__main__":
    main() 