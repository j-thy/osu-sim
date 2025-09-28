import os
from tqdm import tqdm

import calc

songs_dir = r'maps'

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
processed_count = 0
failed_count = 0

with tqdm(total=len(osu_files), desc="Extracting distributions", unit="map") as pbar:
    for path, filename in osu_files:
        try:
            # Create a .dist file for the beatmap
            dist_output = os.path.join('dists', filename[:-4] + '.dist')
            # If the .dist file doesn't already exist...
            if not os.path.exists(dist_output):
                # Calculate the distribution of angles, time, and distance between notes
                calc.get_distribution(path, dist_output)
                processed_count += 1
        except Exception:
            failed_count += 1

        # Update progress bar with current beatmap ID
        beatmap_id = filename[:-4]
        pbar.set_postfix({'ID': beatmap_id, 'Processed': processed_count, 'Failed': failed_count})
        pbar.update(1)

# Summary
print(f"\n{'='*50}")
print(f"Distribution extraction complete!")
print(f"Successfully processed: {processed_count} beatmaps")
print(f"Failed to process: {failed_count} beatmaps")
print(f"Total files scanned: {len(osu_files)} beatmaps")