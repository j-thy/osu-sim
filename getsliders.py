import os
from tqdm import tqdm

import calc

songs_dir = r'maps'

print("Scanning for .osu files...")

# First, collect all .osu files that need processing
osu_files_to_process = []
for subdir, dirs, files in os.walk(songs_dir):
    for filename in files:
        if filename.endswith(".osu"):
            path = os.path.join(subdir, filename)
            sldr_output = os.path.join('sliders', filename[:-4] + '.sldr')
            # Only add files that don't already have a .sldr file
            if not os.path.exists(sldr_output):
                osu_files_to_process.append((path, sldr_output))

if not osu_files_to_process:
    print("All .osu files already have slider data. Nothing to process.")
else:
    print(f"Found {len(osu_files_to_process)} beatmap files to process")

    failed_files = []
    # Process all files with progress bar
    with tqdm(total=len(osu_files_to_process), desc="Extracting sliders", unit="map") as pbar:
        for path, sldr_output in osu_files_to_process:
            try:
                # Calculate the slider lengths, velocity, and total ratio
                # Create a .sldr file for the beatmap
                calc.get_sliders(path, sldr_output)
            except Exception as e:
                failed_files.append(path)
            pbar.update(1)

    print(f"\nSuccessfully processed: {len(osu_files_to_process) - len(failed_files)} beatmaps")
    if failed_files:
        print(f"Failed to process: {len(failed_files)} beatmaps")
    print(f"Slider files saved to: sliders/")