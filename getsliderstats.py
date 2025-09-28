import math
import os
from tqdm import tqdm

def avg(lst):
    if not lst:
        return 0, 0
    return sum(p[0] for p in lst) / len(lst), sum(p[1] for p in lst) / len(lst)

def var(lst):
    if not lst:
        return 0, 0
    lst_avg = avg(lst)
    return sum((p[0] - lst_avg[0]) ** 2 for p in lst) / len(lst), sum((p[1] - lst_avg[1]) ** 2 for p in lst) / len(lst)

def std(lst):
    lst_var = var(lst)
    return math.sqrt(lst_var[0]), math.sqrt(lst_var[1])

def get_sliders(sliders_file):
    sliders = []
    ratio = 0
    with open(sliders_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            ls = line.split(',')
            if len(ls) == 2:
                sliders.append((float(ls[0]), float(ls[1])))
            elif ls:
                ratio = float(ls[0])
    return sliders, ratio

def get_all_sliders():
    sliders = {}

    sldr_dir = 'sliders'

    print("Scanning for .sldr files...")

    # First, collect all .sldr files to know the total count
    sldr_files = [entry for entry in os.scandir(sldr_dir) if entry.is_file() and entry.name.endswith('.sldr')]

    if not sldr_files:
        print("No .sldr files found in sliders/ directory.")
        return sliders

    print(f"Found {len(sldr_files)} slider files to process")

    # Process all files with progress bar
    with tqdm(total=len(sldr_files), desc="Loading slider data", unit="file") as pbar:
        for entry in sldr_files:
            tmp_sldr, ratio = get_sliders(entry.path)
            sliders[entry.name] = (tmp_sldr, ratio)
            pbar.update(1)

    return sliders

all_sliders = get_all_sliders()

if all_sliders:
    print(f"\nCalculating statistics for {len(all_sliders)} slider files...")

    with open('sliderstats.txt', 'w', encoding='utf8') as f:
        with tqdm(total=len(all_sliders), desc="Computing statistics", unit="file") as pbar:
            for file in all_sliders:
                avg_slider = avg(all_sliders[file][0])
                std_slider = std(all_sliders[file][0])
                ratio = all_sliders[file][1]
                f.write(f'{file}\n{avg_slider[0]},{avg_slider[1]},{std_slider[0]},{std_slider[1]},{ratio}\n')
                pbar.update(1)

    print(f"\nSuccessfully processed: {len(all_sliders)} slider files")
    print(f"Statistics saved to: sliderstats.txt")
else:
    print("No slider data to process.")
