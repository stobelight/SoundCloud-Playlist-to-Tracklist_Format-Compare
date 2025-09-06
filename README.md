# SoundCloud-Playlist-to-Tracklist Format-Compare

# Tracklist-Format for SoundCloud Playlist
A Python script that processes raw, copy-pasted playlist [text](INPUT.txt) into formatted tracklist [output](OUTPUT_date_time.txt).  
- updated for 2025 site

## Features
- **Configurable**: All settings are in `config.ini`
- **Debug Mode**: Color-coded visual feedback.
- **Multiple Separators**: Handles `·`, `•`, `‧`, `⋅`, `-` and more with optional replace.
- **Blocklist**: Filter for unwanted names before output. [View Sample BLOCKLIST.txt](BLOCKLIST.txt)
- **More**: Truncate for descriptions, header/footer, simple .CSV spreadsheet export.

wip:
- All in one full featured interface
>/js/index.html    ; demo

## Usage
> Recommend: Download repo and Open folder in Visual Studio Code, run .py in Terminal.
1. Create a config.ini file, or modify default config file.
2. Prepare your input text file. [View Sample INPUT.txt](INPUT.txt)
3. Run: python format-sc_playlist_tracklist.py

Output will be saved as:
>OUTPUT_YYYYMMDD_HHMMSS.txt   /    OUTPUT_YYYYMMDD_HHMMSS.csv (if SaveAsCSV = true)

[View Sample tracklist.txt](OUTPUT_date_time.txt)
[View Sample .csv](OUTPUT_date_time_csv.csv)



# Tracklist-Comparator with Fuzzywuzzy 
A Python script for comparing two text files (music tracklists) using fuzzy matching. It highlights differences, handles formatting quirks, and supports multithreading for fun and speed.

## Features
- **Configurable**: All settings are in `config.ini` — Similarity threshold, multithreading cap.
- **Debug Mode**: Color-coded visual feedback.
- **More**: Normalize inputs and strip track numbers, simple .CSV spreadsheet export.

## Usage
> Recommend: Download repo and Open folder in Visual Studio Code, run .py in Terminal.
1. Create a config.ini file, or modify default config file.
2. Prepare your input text files. [View Sample MAIN_list.txt](MAIN_list.txt), [View Sample NEW_list.txt](NEW_list.txt) (here, the original MAIN tracklist is compared to the NEW playlist copied live from SoundCloud. so, some tracks are missing to time)
3. Run: python compare-fuzzy_tracklists.py
4. Print results to the console with color-coded scores

Output will be saved as:
>DIFF_{main_list}_vs_{new_list}_{timestamp}.txt     /     DIFF_{main_list}_vs_{new_list}_{timestamp}.csv (if save_csv = true)

[View Sample .csv](DIFF_MAIN_list_vs_NEW_list_date_time_csv.csv)
```
Comparing the sample MAIN/NEW_list.txt shows changes over time to the main playlist and live track data:

=== Lines only in main_file: MAIN_list.txt (missing from new_file: NEW_list.txt) ===
-tracks here with similarity threshold (Score: ~< 50) are likely to be missing from the live playlist,
but archived in the main tracklist.
```

## Example config.ini
```
[Settings]
# Debug
Debug = true

# Path to your input file (same directory)
InputFile = INPUT.txt

# also save to spreadsheet CSV
SaveAsCSV = true

# Sort option: "track" or "number"
SortOption = number

# Integer prefix to add to track numbers
Prefix = 0

# Maximum length for track titles
MaxLength = 200

# Remove numeric prefix from final output (true/false)
RemovePrefix = false

# Configurable separators (comma-separated list) (·, •, ‧, ⋅, -)
Separators = ·, •, ‧, ⋅

# Boolean flag: replace known separators 
ReplaceSeparator = true

# What to replace it with (leave empty to remove) (" - ")
ReplaceWith = " - "

# Remove false names (match name before separator)
BlocklistFile = BLOCKLIST.txt



#### compare fuzzywuzzy script settings ####
[difference_settings]
# true = show raw→normalized preview, false = skip
debug_mode = true

# multithreading count: 1 = none, 0 = max cpu cores - 1, 2 - 8, 9+ = 8
thread_cap = 8

# main list of tracks to check against
main_file = MAIN_list.txt

# current new list of tracks
new_file = NEW_list.txt

# also save to spreadsheet CSV
save_csv = true

# sort by: "score" or "default"
sort_by = score

# default: 85; 65, 55 lowest
similarity_threshold = 75

# clean input = false, with track #'s = true
strip_leading_numbers = true
```

- >Thank you Copilot and GPT-5 for the free vibecode
