import re


def parse_output(message):
    pattern = r"output_folder\s+(?:{)?(.*?)(?:}|\.|$)"
    match = re.search(pattern, message)
    if match:
        return match.group(1)
    return None