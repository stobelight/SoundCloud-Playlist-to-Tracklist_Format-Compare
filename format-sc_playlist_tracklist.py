# v04450

import os
from datetime import datetime
import configparser
import re
import csv

# ---------------------------
# Debug Colors & Utility
# ---------------------------

RESET = "\033[0m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
RED = "\033[31m"

def debug_print(enabled, tag, message, color=RESET):
    """Print a tagged, colored debug message if debug mode is enabled."""
    if enabled:
        print(f"{color}[{tag}]{RESET} {message}")

# ---------------------------
# Core Utility Functions
# ---------------------------

def add_prefix(number_str, prefix):
    """Add integer prefix to a number string."""
    return int(number_str) + prefix

def truncate_text(text, max_length):
    """Truncate text to max_length characters."""
    return text[:max_length]

def load_config(config_file):
    """Load configuration from file."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found!")
    config.read(config_file, encoding="utf-8")
    return config

def remove_prefix(data):
    """Remove numeric prefix from each line."""
    return [line.split(". ", 1)[1] if ". " in line else line for line in data]

def sort_output(data, sort_option):
    """Sort output by track name (case-insensitive) or number."""
    if sort_option == "track":
        return sorted(data, key=lambda x: x.split(". ", 1)[1].lower())
    elif sort_option == "number":
        return sorted(data, key=lambda x: int(x.split(".")[0]))
    else:
        raise ValueError(f"Invalid sort option: {sort_option}")

def read_file(file_path):
    """Read entire file contents."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def is_popularity_line(line):
    """Detect lines with popularity metrics (e.g., 57.4K, 1.05M)."""
    return bool(re.match(r"^\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?[KMBkmb]?\s*$", line))

def load_blocklist(file_path):
    """Load blocklist entries (lowercased, trimmed)."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

def split_artist_title(text, separators):
    """Split into (artist, title) at first configured separator."""
    for sep in separators:
        if not sep:
            continue
        # Preferred: separator with spaces
        pattern_with_spaces = f" {re.escape(sep)} "
        if pattern_with_spaces in text:
            artist, title = text.split(pattern_with_spaces, 1)
            return artist.strip(), title.strip()
        # Fallback: optional spaces
        m = re.search(rf"\s*{re.escape(sep)}\s*", text)
        if m:
            artist = text[:m.start()]
            title = text[m.end():]
            return artist.strip(), title.strip()
    return text.strip(), ""

def replace_first_separator(artist, title, replace_with):
    """Rebuild line with only the artist/title separator replaced."""
    return f"{artist}{replace_with}{title}".strip() if title else artist

# ---------------------------
# Main Script
# ---------------------------

try:
    # Load settings from config.ini
    config = load_config("config.ini")
    input_file = config["Settings"]["InputFile"]
    prefix = int(config["Settings"]["Prefix"])
    max_length = int(config["Settings"]["MaxLength"])
    sort_option = config["Settings"]["SortOption"]
    remove_prefix_option = config["Settings"].getboolean("RemovePrefix")
    replace_separator = config["Settings"].getboolean("ReplaceSeparator")
    replace_with = config["Settings"].get("ReplaceWith", "")
    if replace_with.startswith('"') and replace_with.endswith('"'):
        replace_with = replace_with[1:-1]
    blocklist_file = config["Settings"].get("BlocklistFile", "")
    blocklist = load_blocklist(blocklist_file) if blocklist_file else []
    separators = [s.strip() for s in config["Settings"].get("Separators", "·,•,‧,⋅,-").split(",") if s.strip()]
    escaped_separators = [re.escape(s) for s in separators if s]
    debug_mode = config["Settings"].getboolean("Debug", fallback=False)
    save_as_csv = config["Settings"].getboolean("SaveAsCSV", fallback=False)
except Exception as e:
    print(f"Error loading configuration: {e}")
    exit()

try:
    # Read input file and strip empty lines
    with open(input_file, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]
except Exception as e:
    print(f"Error reading input file: {e}")
    exit()

# Precompile number-line regex for efficiency
number_line_pattern = re.compile(r"^\s*\d+\s*(?:%s)" % "|".join(escaped_separators)) if escaped_separators else None

formatted_output = []
csv_rows = []
i = 0
while i < len(lines):
    try:
        # Skip lines that don't start with a track number + separator
        if not (number_line_pattern and number_line_pattern.match(lines[i])):
            debug_print(debug_mode, "SKIP", f"Skipping non-number line [{i}]: {lines[i]!r}", YELLOW)
            i += 1
            continue

        # Extract track number
        m = re.match(r"^\s*(\d+)", lines[i])
        if not m:
            debug_print(debug_mode, "ERROR", f"Could not parse number at line [{i}]: {lines[i]!r}", RED)
            i += 1
            continue
        modified_number = add_prefix(m.group(1), prefix)

        # Get track info line
        if i + 1 >= len(lines):
            debug_print(debug_mode, "ERROR", f"Missing track line after number at [{i}]", RED)
            break
        track_line = lines[i + 1]
        debug_print(debug_mode, "RAW", f"Track line: {track_line!r}", CYAN)

        # Split into artist/title
        artist, title = split_artist_title(track_line, separators)
        debug_print(debug_mode, "SPLIT", f"Artist: {artist!r}, Title: {title!r}", CYAN)

        # Remove blocklisted artist
        if blocklist and artist.lower() in blocklist:
            debug_print(debug_mode, "BLOCKLIST", f"Artist '{artist}' matched blocklist; removing artist.", RED)
            track_line, artist = title, ""
        elif replace_separator and title:
            track_line = replace_first_separator(artist, title, replace_with)
            debug_print(debug_mode, "REPLACE", f"After replacement: {track_line!r}", GREEN)

        # Capture popularity if present
        popularity = ""
        if i + 2 < len(lines) and is_popularity_line(lines[i + 2]):
            popularity = lines[i + 2]
            debug_print(debug_mode, "POPULARITY", f"Popularity line detected at [{i+2}]: {popularity!r}", MAGENTA)
            i += 3
        else:
            i += 2

        # Add to outputs
        formatted_output.append(f"{modified_number}. {truncate_text(track_line, max_length)}")
        csv_rows.append({
            "Track number": modified_number,
            "Artist": artist,
            "Title": title,
            "Plays": popularity
        })

    except Exception as e:
        debug_print(debug_mode, "ERROR", f"Error processing block starting at line {i}: {e}", RED)
        i += 1

# Sort output
try:
    formatted_output = sort_output(formatted_output, sort_option)
except ValueError as e:
    print(f"Error during sorting: {e}")
    exit()

# Remove numeric prefix if configured
if remove_prefix_option:
    formatted_output = remove_prefix(formatted_output)

# Add header/footer
try:
    header = read_file("header.txt")
    footer = read_file("footer.txt")
    formatted_output.insert(0, header)
    formatted_output.append(footer)
except Exception as e:
    print(f"Error reading header/footer: {e}")
    exit()

# Write TXT output
output_file_txt = f"OUTPUT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
try:
    with open(output_file_txt, "w", encoding="utf-8") as file:
        file.write("\n".join(formatted_output))
    print(f"Successfully written to '{output_file_txt}'!")
except Exception as e:
    print(f"Error writing output file: {e}")
    exit()

# Write CSV output if enabled
if save_as_csv:
    output_file_csv = f"OUTPUT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        with open(output_file_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["Track number", "Artist", "Title", "Plays"])
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"Successfully written CSV to '{output_file_csv}'!")
    except Exception as e:
        print(f"Error writing CSV file: {e}")
