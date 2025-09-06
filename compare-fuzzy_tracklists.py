# v0752

import configparser
from fuzzywuzzy import fuzz, process
from colorama import Fore, Style, init
from datetime import datetime
import os
import re
import csv  # <-- added
from concurrent.futures import ThreadPoolExecutor

# Initialize Colorama for colored console output
init(autoreset=True)

def normalize(line, strip_numbers=True):
    line = line.strip()
    if strip_numbers:
        line = re.sub(r'^\d+[\.\)\:\-]\s*', '', line)
    return line.lower()

def highlight_changes(raw, norm):
    raw_words = raw.strip().split()
    norm_words = norm.strip().split()
    highlighted = [
        Fore.GREEN + w + Style.RESET_ALL if w.lower() in norm_words
        else Fore.RED + w + Style.RESET_ALL
        for w in raw_words
    ]
    return " ".join(highlighted) + Fore.CYAN + f"  -->  {norm}" + Style.RESET_ALL

def color_score(score, threshold):
    if score >= threshold:
        return Fore.GREEN + str(score) + Style.RESET_ALL
    elif score >= threshold - 10:
        return Fore.YELLOW + str(score) + Style.RESET_ALL
    return Fore.RED + str(score) + Style.RESET_ALL

def sort_results(results, sort_by):
    key = (lambda x: (x[2], x[0].lower())) if sort_by == "score" else (lambda x: x[0].lower())
    return sorted(results, key=key)

def debug_preview(main_raw, main_norm, new_raw, new_norm):
    print(Fore.MAGENTA + "\n--- DEBUG: Normalization Preview ---" + Style.RESET_ALL)
    print(Fore.CYAN + "\nMain file (master list):" + Style.RESET_ALL)
    for raw, norm in zip(main_raw, main_norm):
        print(highlight_changes(raw, norm))
    print(Fore.CYAN + "\nNew file (current list):" + Style.RESET_ALL)
    for raw, norm in zip(new_raw, new_norm):
        print(highlight_changes(raw, norm))
    print(Fore.MAGENTA + "--- END DEBUG ---\n" + Style.RESET_ALL)

def fuzzy_match_task(args):
    raw, norm, other_norm, threshold = args
    match, score = process.extractOne(norm, other_norm, scorer=fuzz.token_sort_ratio)
    return (raw, match, score) if score < threshold else None

def resolve_thread_count(thread_cap):
    cpu_count = os.cpu_count() or 1
    if thread_cap == 0:
        return max(cpu_count - 1, 1)
    if thread_cap <= 1:
        return 1
    return min(thread_cap, 8)

def compare_files(main_file, new_file, similarity_threshold=85, sort_by="default",
                  debug_mode=False, thread_cap=1, strip_leading_numbers=True, save_csv=False):
    with open(main_file, "r", encoding="utf-8") as f1, open(new_file, "r", encoding="utf-8") as f2:
        main_raw = [l.strip() for l in f1 if l.strip()]
        new_raw = [l.strip() for l in f2 if l.strip()]

    main_norm = [normalize(l, strip_leading_numbers) for l in main_raw]
    new_norm = [normalize(l, strip_leading_numbers) for l in new_raw]

    if debug_mode:
        debug_preview(main_raw, main_norm, new_raw, new_norm)

    new_set = set(new_norm)
    main_set = set(main_norm)

    tasks_main = [(raw, norm, new_norm, similarity_threshold)
                  for raw, norm in zip(main_raw, main_norm) if norm not in new_set]
    tasks_new = [(raw, norm, main_norm, similarity_threshold)
                 for raw, norm in zip(new_raw, new_norm) if norm not in main_set]

    only_in_main, only_in_new = [], []
    actual_threads = resolve_thread_count(thread_cap)
    print(Fore.YELLOW + f"[DEBUG] Using {actual_threads} thread(s) for fuzzy matching" + Style.RESET_ALL)

    if actual_threads == 1:
        for t in tasks_main:
            if (res := fuzzy_match_task(t)):
                only_in_main.append(res)
        for t in tasks_new:
            if (res := fuzzy_match_task(t)):
                only_in_new.append(res)
    else:
        with ThreadPoolExecutor(max_workers=actual_threads) as executor:
            only_in_main.extend(filter(None, executor.map(fuzzy_match_task, tasks_main)))
            only_in_new.extend(filter(None, executor.map(fuzzy_match_task, tasks_new)))

    only_in_main = sort_results(only_in_main, sort_by)
    only_in_new = sort_results(only_in_new, sort_by)

    print(Fore.CYAN + f"\n=== Lines only in main_file: {main_file} (missing from new_file: {new_file}) ===" + Style.RESET_ALL)
    print(f"Threshold: {similarity_threshold} | Sort: {sort_by} | Threads: {actual_threads}\n")
    for raw, match, score in only_in_main:
        print(f"{raw}  --> Closest: '{match}'  (Score: {color_score(score, similarity_threshold)})")

    print(Fore.CYAN + f"\n=== Lines only in new_file: {new_file} (not in main_file: {main_file}) ===" + Style.RESET_ALL)
    print(f"Threshold: {similarity_threshold} | Sort: {sort_by} | Threads: {actual_threads}\n")
    for raw, match, score in only_in_new:
        print(f"{raw}  --> Closest: '{match}'  (Score: {color_score(score, similarity_threshold)})")

    main_name = os.path.splitext(os.path.basename(main_file))[0]
    new_name = os.path.splitext(os.path.basename(new_file))[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_diff = f"DIFF_{main_name}_vs_{new_name}_{timestamp}.txt"

    with open(output_diff, "w", encoding="utf-8") as diff_file:
        diff_file.write(f"=== Lines only in main_file: {main_file} (missing from new_file: {new_file}) ===\n")
        diff_file.write(f"Threshold: {similarity_threshold} | Sort: {sort_by} | Threads: {actual_threads}\n\n")
        for raw, match, score in only_in_main:
            diff_file.write(f"{raw}  --> Closest: '{match}'  (Score: {score})\n\n")
        diff_file.write(f"\n=== Lines only in new_file: {new_file} (not in main_file: {main_file}) ===\n")
        diff_file.write(f"Threshold: {similarity_threshold} | Sort: {sort_by} | Threads: {actual_threads}\n\n")
        for raw, match, score in only_in_new:
            diff_file.write(f"{raw}  --> Closest: '{match}'  (Score: {score})\n\n")

    print(Fore.MAGENTA + f"\nDifferences report saved to '{output_diff}'" + Style.RESET_ALL)

    if save_csv:
        output_csv = f"DIFF_{main_name}_vs_{new_name}_{timestamp}.csv"
        with open(output_csv, "w", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Section", "Line", "Closest Match", "Score"])
            for raw, match, score in only_in_main:
                writer.writerow([f"Only in {main_file}", raw, match, score])
            for raw, match, score in only_in_new:
                writer.writerow([f"Only in {new_file}", raw, match, score])
        print(Fore.MAGENTA + f"CSV report saved to '{output_csv}'" + Style.RESET_ALL)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")

    if "difference_settings" not in config:
        raise ValueError("Missing [difference_settings] section in config.ini")

    main_file = config["difference_settings"]["main_file"]
    new_file = config["difference_settings"]["new_file"]
    similarity_threshold = int(config["difference_settings"]["similarity_threshold"])
    sort_by = config["difference_settings"].get("sort_by", "default").lower()
    debug_mode = config["difference_settings"].get("debug_mode", "false").lower() == "true"
    strip_leading_numbers = config["difference_settings"].get("strip_leading_numbers", "true").lower() == "true"
    save_csv = config["difference_settings"].get("save_csv", "false").lower() == "true"

    try:
        thread_cap = int(config["difference_settings"].get("thread_cap", "1"))
    except ValueError:
        thread_cap = 1

    compare_files(main_file, new_file, similarity_threshold, sort_by,
                  debug_mode, thread_cap, strip_leading_numbers, save_csv)
