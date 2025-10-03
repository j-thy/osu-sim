import json
import os
import subprocess
import argparse
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Set up .NET environment variables
dotnet_root = os.path.expanduser("~/.dotnet")
if os.path.exists(dotnet_root):
    os.environ["DOTNET_ROOT"] = dotnet_root
    current_path = os.environ.get("PATH", "")
    if dotnet_root not in current_path:
        os.environ["PATH"] = f"{current_path}:{dotnet_root}"

def get_sr(map, mods=None):
    if mods is None:
        mods = []

    if 'DT' in mods or 'NC' in mods:
        return srs_dt.get(map, None)
    elif 'HR' in mods:
        return srs_hr.get(map, None)
    return srs.get(map, None)

def get_sr_file(filename, mods=None):
    """Calculate star rating for a beatmap file

    Args:
        filename: Path to the .osu file
        mods: List of mod strings (e.g., ['DT'], ['HR'])

    Returns:
        Tuple of (sr, aim, speed)
    """
    if mods is None:
        mods = []

    # Convert mods list to mod string
    if 'DT' in mods or 'NC' in mods:
        mod = 'dt'
    elif 'HR' in mods:
        mod = 'hr'
    else:
        mod = 'nm'

    # Use the improved get_raw_data_line function
    data_line = get_raw_data_line(filename, mod=mod)

    # Parse the data line to extract sr, aim, speed
    parts = data_line.strip('\n║').split('│')
    if len(parts) >= 4:
        sr = float(parts[1].strip().replace(',', ''))
        aim = float(parts[2].strip().replace(',', ''))
        speed = float(parts[3].strip().replace(',', ''))
        return (sr, aim, speed)
    else:
        raise Exception("Could not parse star rating data from output")

def get_raw_data_line(filename, mod=None, include_header=False):
    """Get the raw data line from osu-tools output for a single beatmap

    Args:
        filename: Path to the .osu file
        mod: Mod type - 'nm', 'dt', or 'hr' (default: 'nm')
        include_header: If True, return (header_line, data_line) tuple (default: False)
    """
    if mod is None:
        mod = 'nm'

    # Convert relative path to absolute path from the PerformanceCalculator directory
    abs_filename = os.path.abspath(filename)
    # Calculate relative path from osu-tools/PerformanceCalculator to the beatmap file
    perf_calc_dir = os.path.abspath('./osu-tools/PerformanceCalculator')
    rel_filename = os.path.relpath(abs_filename, perf_calc_dir)
    cmd = ['dotnet', 'run', '--', 'difficulty', rel_filename]

    if mod == 'dt':
        cmd.extend(['-m', 'dt'])
    elif mod == 'hr':
        cmd.extend(['-m', 'hr'])
    # nm doesn't need any additional args

    try:
        output = subprocess.run(cmd, cwd='./osu-tools/PerformanceCalculator',
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=30)

        # Check if the command succeeded
        if output.returncode != 0:
            raise Exception(f"dotnet command failed with return code {output.returncode}")

        lines = output.stdout.split(b'\n')

        # Find the header and data lines
        header_line = None
        data_line = None
        for line in lines:
            line_str = line.decode('utf8', errors='ignore')
            # Look for a line that has the pipe characters
            if '\u2502' in line_str:
                # Check if it's the header line (contains "star rating" text)
                if 'star rating' in line_str.lower():
                    header_line = line_str.strip()
                # Or if it's a data line (has numeric data)
                elif any(char.isdigit() for char in line_str):
                    data_line = line_str.strip()
                    break

        if not data_line:
            raise Exception("Could not find data line in output")

        if include_header:
            return (header_line, data_line)
        return data_line

    except subprocess.TimeoutExpired:
        raise Exception(f"Timeout calculating star rating for {filename}")
    except FileNotFoundError:
        raise Exception("dotnet command not found - please ensure .NET is installed")
    except Exception as e:
        raise Exception(f"Error getting raw data: {e}")

def process_map_for_raw(map_file, mod='nm'):
    """Process a single map file and return the raw data line - for parallel processing

    Args:
        map_file: Path to the .osu file
        mod: Mod type - 'nm', 'dt', or 'hr' (default: 'nm')
    """
    try:
        data_line = get_raw_data_line(map_file, mod=mod)
        return (map_file, data_line, None)  # (filepath, data, error)
    except Exception as e:
        return (map_file, None, str(e))  # (filepath, data, error)

def process_maps_parallel(map_files, mod='nm', workers=None):
    """
    Process multiple map files in parallel and return results.

    Args:
        map_files: List of map file paths to process
        mod: Mod type - 'nm', 'dt', or 'hr' (default: 'nm')
        workers: Number of parallel workers (default: CPU count)

    Returns:
        Tuple of (results, failed) where results is a list of (filepath, data_line) tuples
        and failed is a list of (filepath, error) tuples
    """
    num_workers = workers or multiprocessing.cpu_count()
    results = []
    failed = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        futures = {executor.submit(process_map_for_raw, map_file, mod): map_file for map_file in map_files}

        # Process results as they complete
        with tqdm(total=len(map_files), desc=f"Calculating {mod.upper()} star ratings", unit="map") as pbar:
            for future in as_completed(futures):
                map_file = futures[future]
                try:
                    filepath, data_line, error = future.result()
                    if data_line:
                        results.append((filepath, data_line))
                    else:
                        failed.append((filepath, error))
                except Exception as e:
                    failed.append((map_file, str(e)))
                pbar.update(1)

    return results, failed

def get_raw_sr_file_parallel(output_file='srs_raw_nm.txt', mod='nm', workers=None):
    """
    Generate raw star rating file in parallel using multiple workers.

    Args:
        output_file: Path to output raw file
        mod: Mod type - 'nm', 'dt', or 'hr' (default: 'nm')
        workers: Number of parallel workers (default: CPU count)
    """
    # Determine number of workers
    num_workers = workers or multiprocessing.cpu_count()
    print(f"Using {num_workers} parallel workers")

    # Get all .osu files from maps directory
    map_files = []
    for filename in os.listdir('maps'):
        if filename.endswith('.osu'):
            map_files.append(os.path.join('maps', filename))

    print(f"Calculating star ratings for {len(map_files)} beatmaps...")

    # Process maps in parallel
    results, failed = process_maps_parallel(map_files, mod=mod, workers=num_workers)

    # Write all results to file
    print(f"\nWriting {len(results)} results to {output_file}...")
    with open(output_file, 'w', encoding='utf8') as f:
        for filepath, data_line in results:
            # Insert filepath before the ║ at the start of data_line
            f.write(f"{filepath}{data_line}\n")

    print(f"Raw star ratings saved to {output_file}")
    print(f"Successfully processed: {len(results)} beatmaps")

    if failed:
        print(f"Failed: {len(failed)} beatmaps")
        print(f"First 10 failures:")
        for filepath, error in failed[:10]:
            print(f"  {filepath}: {error}")

    return len(results), len(failed)

def get_srs(srs_file='srs.json'):
    with open(srs_file, 'r') as f:
        srs = json.load(f)
    return srs

srs = get_srs()
srs_dt = get_srs('srs_dt.json')
srs_hr = get_srs('srs_hr.json')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate star ratings for osu! beatmaps')
    parser.add_argument('--full-regen', action='store_true',
                       help='Fully regenerate raw files from scratch (slow)')
    parser.add_argument('--new-gen', action='store_true',
                       help='Only process new maps not in raw files and append them')
    parser.add_argument('--get-sr', type=str, metavar='BEATMAP_ID',
                       help='Test a single beatmap ID and print the raw output')
    parser.add_argument('--mods', type=str, default='nm', choices=['nm', 'dt', 'hr', 'all'],
                       help='Mod types to process: nm, dt, hr, or all (default: nm)')
    parser.add_argument('--workers', type=int, default=None,
                       help='Number of parallel workers for generating raw file (default: CPU count)')
    args = parser.parse_args()

    # Determine which mods to process
    if args.mods == 'all':
        mods_to_process = ['nm', 'dt', 'hr']
    else:
        mods_to_process = [args.mods]

    # Handle --get-sr for testing a single beatmap
    if args.get_sr:
        beatmap_id = args.get_sr
        map_file = f'maps/{beatmap_id}.osu'

        if not os.path.exists(map_file):
            print(f"Error: {map_file} not found")
            exit(1)

        print(f"Getting star rating for beatmap {beatmap_id}...")

        for mod in mods_to_process:
            try:
                print(f"\n=== {mod.upper()} ===")
                header_line, data_line = get_raw_data_line(map_file, mod=mod, include_header=True)
                print(f"Raw output:")
                if header_line:
                    print(header_line)
                print(data_line)

                # Parse and display the values
                parts = data_line.strip('\n║').split('│')
                if len(parts) >= 7:
                    # Column labels: beatmap | star rating | aim rating | speed rating | max combo | approach rate | overall difficulty
                    beatmap_name = parts[0].strip()
                    sr = float(parts[1].strip().replace(',', ''))
                    aim = float(parts[2].strip().replace(',', ''))
                    speed = float(parts[3].strip().replace(',', ''))
                    combo = int(parts[4].strip().replace(',', ''))
                    ar = float(parts[5].strip().replace(',', ''))
                    od = float(parts[6].strip().replace(',', ''))

                    print(f"\nParsed values:")
                    print(f"  Beatmap: {beatmap_name}")
                    print(f"  Star rating: {sr}")
                    print(f"  Aim rating: {aim}")
                    print(f"  Speed rating: {speed}")
                    print(f"  Max combo: {combo}")
                    print(f"  Approach rate: {ar}")
                    print(f"  Overall difficulty: {od}")
                    print(f"\nJSON format (used in srs.json): [{sr}, {aim}, {speed}]")
            except Exception as e:
                print(f"Error: {e}")
        exit(0)

    # Helper function to get file paths for a mod type
    def get_file_paths(mod):
        if mod == 'nm':
            return 'srs_raw_nm.txt', 'srs.json'
        elif mod == 'dt':
            return 'srs_raw_dt.txt', 'srs_dt.json'
        elif mod == 'hr':
            return 'srs_raw_hr.txt', 'srs_hr.json'

    # Process each mod type
    for mod in mods_to_process:
        raw, output_file = get_file_paths(mod)
        print(f"\n{'='*60}")
        print(f"Processing {mod.upper()} mod")
        print(f"{'='*60}\n")

        start_line = 0  # Start at line 0 (first line with filepath║data)
        line_step = 1

        # Determine what to do based on arguments
        if args.full_regen:
            # Full regeneration requested
            print(f"Full regeneration of {raw}...")
            print("This will take a while for large beatmap collections...")
            print("Using parallel processing to speed up calculation...")
            get_raw_sr_file_parallel(output_file=raw, mod=mod, workers=args.workers)
        elif args.new_gen:
            # Only process new maps
            print(f"Processing new maps not in {raw}...")

            # Get existing maps from raw file
            existing_maps = set()
            if os.path.exists(raw):
                with open(raw, 'r', encoding='utf8') as f:
                    for line in f:
                        if '║' in line:
                            filepath = line.split('║', 1)[0]
                            existing_maps.add(filepath)

            # Get all maps in the maps folder
            all_maps = []
            for filename in os.listdir('maps'):
                if filename.endswith('.osu'):
                    all_maps.append(os.path.join('maps', filename))

            # Find new maps
            new_maps = [m for m in all_maps if m not in existing_maps]

            if not new_maps:
                print("No new maps found!")
            else:
                print(f"Found {len(new_maps)} new maps to process...")

                # Process new maps in parallel
                results, failed = process_maps_parallel(new_maps, mod=mod, workers=args.workers)

                # Append new results to existing file
                print(f"\nAppending {len(results)} new results to {raw}...")
                with open(raw, 'a', encoding='utf8') as f:
                    for filepath, data_line in results:
                        f.write(f"{filepath}{data_line}\n")

                print(f"Successfully processed: {len(results)} new beatmaps")
                if failed:
                    print(f"Failed: {len(failed)} beatmaps")
        else:
            # Default: just use existing raw file
            if not os.path.exists(raw):
                print(f"Warning: {raw} not found. Skipping {mod.upper()} mod. Use --full-regen to generate it.")
                continue
            print(f"Using existing raw file {raw}")

        # Convert raw file to JSON
        if not os.path.exists(raw):
            print(f"Warning: {raw} not found. Skipping JSON creation for {mod.upper()} mod.")
            continue

        with open(raw, 'r', encoding='utf8') as f:
            lines = f.readlines()

        print("Parsing star ratings from raw file...")
        song_srs = {}

        # Calculate total lines to process
        total_lines = (len(lines) - start_line) // line_step

        with tqdm(total=total_lines, desc="Extracting star ratings", unit="line") as pbar:
            for i in range(start_line, len(lines), line_step):
                # Each line has format: filepath║data
                if i >= len(lines):
                    break

                line = lines[i].strip()

                if not line:
                    break

                # Split on first ║ to separate filepath from data
                if '║' not in line:
                    pbar.update(1)
                    continue

                filepath, data_line = line.split('║', 1)

                # Extract map ID from filepath (format: maps/12345.osu)
                if filepath.startswith('maps/') and filepath.endswith('.osu'):
                    map_id = filepath[5:-4]  # Remove 'maps/' prefix and '.osu' suffix
                else:
                    pbar.update(1)
                    continue

                # Parse star ratings from data line
                # Format: beatmap_name│star│aim│speed│combo│ar│od
                parts = data_line.strip('\n║').split('│')
                if len(parts) < 4:
                    pbar.update(1)
                    continue

                # Extract the numeric values we need: star rating, aim rating, speed rating
                try:
                    sr = float(parts[1].strip().replace(',', ''))
                    aim = float(parts[2].strip().replace(',', ''))
                    speed = float(parts[3].strip().replace(',', ''))
                except (ValueError, IndexError):
                    pbar.update(1)
                    continue

                song_srs[map_id] = [sr, aim, speed]
                pbar.update(1)

        # song_srs contains map_id -> [sr, aim, speed]
        output_srs = song_srs

        print(f"\nSuccessfully extracted star ratings for {len(output_srs)} beatmaps")

        print(f"\nSorting by beatmap ID...")
        # Sort by beatmap ID (numerically)
        sorted_srs = {}
        for map_id in sorted(output_srs.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            sorted_srs[map_id] = output_srs[map_id]

        print(f"\nWriting star ratings to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(sorted_srs, f)
        print(f"Successfully mapped: {len(sorted_srs)} star ratings")
        print(f"Output saved to: {output_file}")
