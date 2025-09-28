import os
from tqdm import tqdm

def get_median(dist_file):
    angles = []
    times = []
    dists = []
    with open(dist_file, 'r') as f:
        lines = f.readlines()

    # Skip empty files
    if not lines:
        return None

    for l in lines:
        ls = l.split(',')
        angles.append(float(ls[0]))
        times.append(float(ls[1]))
        dists.append(float(ls[2]))

    angles.sort()
    times.sort()
    dists.sort()

    return angles[len(angles)//2], times[len(times)//2], dists[len(dists)//2]

def get_medians(medians_file='medians.txt'):
    medians = {}
    try:
        with open(medians_file, 'r') as f:
            lines = f.readlines()
        for i in range(0, len(lines), 2):
            medians[lines[i].strip()] = tuple(float(x) for x in lines[i+1].split(','))
    except:
        pass

    return medians

if __name__ == '__main__':
    medians = get_medians()

    dists_dir = 'dists'

    print("Scanning for .dist files...")

    # Collect files that need processing
    files_to_process = []
    for entry in os.scandir(dists_dir):
        if entry.is_file() and entry.name.endswith('.dist') and entry.name not in medians:
            files_to_process.append(entry)

    if not files_to_process:
        print("All .dist files already have calculated medians. Nothing to process.")
    else:
        print(f"Found {len(files_to_process)} .dist files to process")

        # Process files with progress bar
        skipped_files = []
        with tqdm(total=len(files_to_process), desc="Calculating medians", unit="map") as pbar:
            for entry in files_to_process:
                median = get_median(entry.path)
                if median is not None:
                    medians[entry.name] = median
                else:
                    skipped_files.append(entry.name)
                pbar.update(1)

        print(f"\nSuccessfully processed: {len(files_to_process) - len(skipped_files)} distribution files")
        if skipped_files:
            print(f"Skipped {len(skipped_files)} empty files")

    print("Writing medians to medians.txt...")
    with open('medians.txt', 'w', encoding='utf8') as f:
        for name in medians:
            f.write(name + '\n' + ','.join(str(x) for x in medians[name]) + '\n')
    print(f"Medians saved to: medians.txt")
