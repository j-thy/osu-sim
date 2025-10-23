#!/usr/bin/env python3
"""
Download osu! beatmap files from the osu! website

Usage:
    python3 getmaps.py              # Download all maps from mapids_nodup.txt
    python3 getmaps.py --retry-failed  # Retry previously failed downloads
    python3 getmaps.py -r            # Short form of --retry-failed
"""

import argparse
import os
import requests
from tqdm import tqdm

def get_map(id):
    r = requests.get(f'https://osu.ppy.sh/osu/{id}', timeout=5)
    return r.text

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Download osu! beatmap files from the osu! website',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 getmaps.py              # Download all maps from mapids_nodup.txt
  python3 getmaps.py --retry-failed  # Retry previously failed downloads
        """
    )
    parser.add_argument('--retry-failed', '-r', action='store_true',
                        help='Retry previously failed downloads')

    args = parser.parse_args()

    mapids_file = 'mapids_nodup.txt'
    maps_folder = 'maps'

    if args.retry_failed:
        # Try to download previously failed maps
        if not os.path.exists('failed_map_downloads.txt'):
            print("No failed_map_downloads.txt file found. Nothing to retry.")
            exit(0)

        print("Loading failed map IDs...")
        with open('failed_map_downloads.txt', 'r') as f:
            mapids = [l.strip() for l in f.readlines() if l.strip()]

        if not mapids:
            print("No failed map IDs to retry.")
            exit(0)

        print(f"Retrying {len(mapids)} previously failed maps...")
    else:
        # Normal mode - load all map IDs
        print("Loading map IDs...")
        with open(mapids_file, 'r') as f:
            mapids = [l.strip() for l in f.readlines() if l.strip()]

        print(f"Total map IDs in {mapids_file}: {len(mapids)}")

    # Get existing maps
    print("Checking existing maps...")
    existing = set(os.listdir(maps_folder))
    existing_ids = {f[:-4] for f in existing if f.endswith('.osu')}  # Remove .osu extension

    # Find maps to download
    maps_to_download = [mid for mid in mapids if mid not in existing_ids]

    print(f"Maps already downloaded: {len(existing_ids)}")
    print(f"Maps to download: {len(maps_to_download)}")

    if not maps_to_download:
        print("All maps are already downloaded!")
        exit(0)

    # Download missing maps with progress bar
    print("\nStarting downloads...")

    failed_ids = []
    consecutive_failures = 0

    with tqdm(total=len(maps_to_download), desc="Downloading maps", unit="map") as pbar:
        for map_id in maps_to_download:
            filename = f'{map_id}.osu'
            filepath = os.path.join(maps_folder, filename)

            # Update progress bar description with current ID
            pbar.set_postfix({'ID': map_id, 'Failed': len(failed_ids)})

            try:
                # Download the map
                text = get_map(map_id)

                # Save to file
                with open(filepath, 'w', encoding='utf8', newline='') as f:
                    f.write(text)

                consecutive_failures = 0  # Reset on success

            except requests.exceptions.RequestException as e:
                failed_ids.append(map_id)
                consecutive_failures += 1

                # If too many consecutive failures, might be network issue
                if consecutive_failures >= 10:
                    print(f"\n\nToo many consecutive failures ({consecutive_failures}). Stopping.")
                    print("You can run the script again to resume.")
                    break

            except Exception as e:
                failed_ids.append(map_id)
                print(f"\nError with map {map_id}: {e}")

            pbar.update(1)

    # Summary
    print(f"\n{'='*50}")
    print(f"Download complete!")
    print(f"Successfully downloaded: {len(maps_to_download) - len(failed_ids)} maps")

    if failed_ids:
        print(f"Failed to download: {len(failed_ids)} maps")
        print(f"Failed IDs (first 10): {failed_ids[:10]}")

        # Load existing failed IDs if file exists
        existing_failed = set()
        if os.path.exists('failed_map_downloads.txt'):
            with open('failed_map_downloads.txt', 'r') as f:
                existing_failed = {l.strip() for l in f.readlines() if l.strip()}

        # Combine with new failed IDs
        all_failed = existing_failed | set(failed_ids)

        # Save all failed IDs to file
        with open('failed_map_downloads.txt', 'w') as f:
            for map_id in sorted(all_failed):
                f.write(f"{map_id}\n")

        new_failures = len(all_failed) - len(existing_failed)
        if existing_failed:
            print(f"Added {new_failures} new failures to existing {len(existing_failed)} failed IDs")
        print(f"Total failed IDs in failed_map_downloads.txt: {len(all_failed)}")
        print("Run with --retry-failed or -r to retry these downloads")
    elif retry_failed and os.path.exists('failed_map_downloads.txt'):
        # If retry was successful and no new failures, clean up the file
        os.remove('failed_map_downloads.txt')
        print("All previously failed maps downloaded successfully!")
        print("Removed failed_map_downloads.txt")

    print(f"Total maps now in {maps_folder}: {len(existing_ids) + len(maps_to_download) - len(failed_ids)}")

    # Cleanup failed_map_downloads.txt - remove any IDs that have been successfully downloaded
    if os.path.exists('failed_map_downloads.txt'):
        with open('failed_map_downloads.txt', 'r') as f:
            failed_list = [l.strip() for l in f.readlines() if l.strip()]

        if failed_list:
            print("\nCleaning up failed_map_downloads.txt...")

            # Check which failed IDs now exist in maps folder
            current_maps = set(os.listdir(maps_folder))
            still_failed = []
            cleaned_count = 0

            for map_id in failed_list:
                filename = f'{map_id}.osu'
                if filename not in current_maps:
                    # Still missing, keep in failed list
                    still_failed.append(map_id)
                else:
                    # Now exists, remove from failed list
                    cleaned_count += 1

            if cleaned_count > 0:
                if still_failed:
                    # Write back the cleaned list
                    with open('failed_map_downloads.txt', 'w') as f:
                        for map_id in still_failed:
                            f.write(f"{map_id}\n")
                    print(f"Removed {cleaned_count} successfully downloaded maps from failed list")
                    print(f"Remaining failed maps: {len(still_failed)}")
                else:
                    # All failed maps have been downloaded, remove the file
                    os.remove('failed_map_downloads.txt')
                    print(f"All {cleaned_count} previously failed maps have been downloaded")
                    print("Removed failed_map_downloads.txt")
            else:
                print(f"No cleanup needed - all {len(failed_list)} maps still missing")