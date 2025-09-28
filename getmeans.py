import os
from tqdm import tqdm

def get_mean(dist_file):
    s_a = s_t = s_d = 0
    with open(dist_file, 'r') as f:
        lines = f.readlines()

    # Skip empty files
    if not lines:
        return None

    for l in lines:
        ls = l.split(',')
        s_a += float(ls[0])
        s_t += float(ls[1])
        s_d += float(ls[2])
    cnt = len(lines)

    return s_a / cnt, s_t / cnt, s_d / cnt

def get_means(means_file='means.txt'):
    means = {}
    try:
        with open(means_file, 'r') as f:
            lines = f.readlines()
        for i in range(0, len(lines), 2):
            means[lines[i].strip()] = tuple(float(x) for x in lines[i+1].split(','))
    except:
        pass

    return means

if __name__ == '__main__':
    means = get_means()

    dists_dir = 'dists'

    print("Scanning for .dist files...")

    # Collect files that need processing
    files_to_process = []
    for entry in os.scandir(dists_dir):
        if entry.is_file() and entry.name.endswith('.dist') and entry.name not in means:
            files_to_process.append(entry)

    if not files_to_process:
        print("All .dist files already have calculated means. Nothing to process.")
    else:
        print(f"Found {len(files_to_process)} .dist files to process")

        # Process files with progress bar
        skipped_files = []
        with tqdm(total=len(files_to_process), desc="Calculating means", unit="map") as pbar:
            for entry in files_to_process:
                mean = get_mean(entry.path)
                if mean is not None:
                    means[entry.name] = mean
                else:
                    skipped_files.append(entry.name)
                pbar.update(1)

        print(f"\nSuccessfully processed: {len(files_to_process) - len(skipped_files)} distribution files")
        if skipped_files:
            print(f"Skipped {len(skipped_files)} empty files")

    print("Writing means to means.txt...")
    with open('means.txt', 'w', encoding='utf8') as f:
        for name in means:
            f.write(name + '\n' + ','.join(str(x) for x in means[name]) + '\n')
    print(f"Means saved to: means.txt")
