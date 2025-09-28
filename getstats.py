#!/usr/bin/env python3
"""
Extract basic statistics from all osu! beatmap files

Reads all .osu files from the maps/ directory and extracts metadata such as:
- HP (Health Points drain rate)
- CS (Circle Size)
- OD (Overall Difficulty)
- AR (Approach Rate)
- Title, Artist, Creator, Version
- Length and max BPM

Output: stats.json - A dictionary mapping beatmap IDs to their statistics
"""

import os
import json
from tqdm import tqdm

import calc

# Directory containing downloaded .osu beatmap files
songs_dir = r'maps'

# Dictionary to store all beatmap statistics
# Key: beatmap ID (filename without .osu extension)
# Value: dictionary of stats from calc.get_stats()
stats = {}

print("Scanning for .osu files...")

# First, collect all .osu files to know the total count
osu_files = []
for subdir, dirs, files in os.walk(songs_dir):
    for filename in files:
        if filename.endswith(".osu"):
            path = os.path.join(subdir, filename)
            osu_files.append((path, filename))

print(f"Found {len(osu_files)} beatmap files to process")

# Process all files with progress bar
failed_count = 0
failed_maps = []  # Store failed map info for logging

with tqdm(total=len(osu_files), desc="Extracting stats", unit="map") as pbar:
    for path, filename in osu_files:
        try:
            # Extract beatmap ID from filename (remove .osu extension)
            beatmap_id = filename[:-4]

            # Call calc.get_stats() to extract all statistics from the beatmap
            # This parses the .osu file and returns a dict with HP, CS, OD, AR, etc.
            stats[beatmap_id] = calc.get_stats(path)

        except Exception as e:
            # Skip files that can't be parsed (corrupted or invalid format)
            failed_count += 1
            # Log the failed map with error details
            failed_maps.append({
                'beatmap_id': filename[:-4],
                'filename': filename,
                'path': path,
                'error': str(e)
            })

        # Update progress bar with current beatmap ID
        pbar.set_postfix({'ID': beatmap_id, 'Failed': failed_count})
        pbar.update(1)

# Write all collected statistics to a JSON file
# This creates a comprehensive database of beatmap metadata
print(f"\nWriting stats to stats.json...")
with open('stats.json', 'w') as fout:
    # Sort by numeric beatmap ID for natural ordering
    sorted_stats = {k: stats[k] for k in sorted(stats.keys(), key=int)}
    json.dump(sorted_stats, fout, indent=2)

# Write failed maps to log file if any failed
if failed_maps:
    print(f"Writing failed maps to getstats_failed.log...")
    with open('getstats_failed.log', 'w') as f:
        f.write(f"Failed to parse {len(failed_maps)} beatmap files\n")
        f.write("="*60 + "\n\n")

        for failed in failed_maps:
            f.write(f"Beatmap ID: {failed['beatmap_id']}\n")
            f.write(f"Filename: {failed['filename']}\n")
            f.write(f"Path: {failed['path']}\n")
            f.write(f"Error: {failed['error']}\n")
            f.write("-"*40 + "\n")

    print(f"Failed maps logged to: getstats_failed.log")

# Summary
print(f"\n{'='*50}")
print(f"Stats extraction complete!")
print(f"Successfully processed: {len(stats)} beatmaps")
print(f"Failed to process: {failed_count} beatmaps")
print(f"Output saved to: stats.json")