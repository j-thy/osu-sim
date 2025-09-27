#!/usr/bin/env python3
"""
Fetch ALL beatmap IDs from osu! API v2
Rate limited to stay well under API limits (50 requests/minute)
This script is designed to run for hours/overnight to build a complete collection

Usage:
    python3 getmapids.py              # Fetch ranked and loved maps (default)
    python3 getmapids.py --fast       # Fast mode: only fetch new maps since last update
    python3 getmapids.py --approved   # Fetch ONLY approved maps (legacy category)
    python3 getmapids.py -a           # Short form of --approved
    python3 getmapids.py -f           # Short form of --fast
"""

import requests
import time
import api
from datetime import datetime
import json
import os
import sys

# Rate limiting configuration
REQUESTS_PER_MINUTE = 50  # Stay well under the 60 limit where we need to contact peppy
REQUEST_DELAY = 60.0 / REQUESTS_PER_MINUTE  # 1.2 seconds between requests

class BeatmapFetcher:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        self.total_requests = 0
        self.start_time = datetime.now()

    def search_beatmapsets(self, status='ranked', cursor_string=None, sort='ranked_desc'):
        """
        Search for beatmapsets with rate limiting
        """
        params = {
            's': status,
            'sort': sort,
        }

        if cursor_string:
            params['cursor_string'] = cursor_string

        url = 'https://osu.ppy.sh/api/v2/beatmapsets/search'

        # Rate limiting
        time.sleep(REQUEST_DELAY)

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            self.total_requests += 1

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Rate limited! Waiting 60 seconds...")
                time.sleep(60)
                return self.search_beatmapsets(status, cursor_string, sort)
            else:
                print(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def fetch_all_for_status(self, status, sort='ranked_desc', max_pages=None, fast_mode=False, existing_ids=None, oldest_new_tracker=None):
        """
        Fetch ALL beatmapsets for a given status

        In fast mode:
        - Only works with newest-first sorts (ranked_desc, updated_desc)
        - Stops after finding a page where all IDs are already known

        Both modes track the oldest new ID found for future runs
        """
        all_beatmap_ids = set()
        cursor_string = None
        page = 0
        consecutive_empty = 0
        pages_with_all_known = 0
        oldest_new_id = None
        newest_new_id = None

        # Load existing IDs for comparison (both modes need this for tracking)
        if existing_ids is None:
            existing_ids = set()
            # In slow mode, still load existing IDs to track what's new
            if not fast_mode:
                try:
                    with open('mapids_nodup.txt', 'r') as f:
                        existing_ids = set(int(line.strip()) for line in f if line.strip())
                except FileNotFoundError:
                    pass  # File doesn't exist yet

        print(f"\nFetching {'new' if fast_mode else 'ALL'} {status} beatmaps (sort: {sort})...")
        if fast_mode:
            print("Fast mode: Will stop after finding known beatmaps")
        else:
            print("This will take a while. Press Ctrl+C to stop gracefully.\n")

        try:
            while True:
                if max_pages and page >= max_pages:
                    print(f"Reached max pages limit ({max_pages})")
                    break

                data = self.search_beatmapsets(status, cursor_string, sort)

                if not data or 'beatmapsets' not in data:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        print("No more data available")
                        break
                    continue

                beatmapsets = data['beatmapsets']
                if not beatmapsets:
                    print("Reached end of results")
                    break

                consecutive_empty = 0

                # Extract beatmap IDs (only standard mode)
                page_ids = set()
                new_ids_on_page = set()
                for beatmapset in beatmapsets:
                    if 'beatmaps' in beatmapset:
                        for beatmap in beatmapset['beatmaps']:
                            # Only add standard mode beatmaps (mode_int == 0)
                            # 0 = osu!, 1 = taiko, 2 = catch, 3 = mania
                            if beatmap.get('mode_int', 0) == 0:
                                beatmap_id = beatmap['id']
                                page_ids.add(beatmap_id)
                                all_beatmap_ids.add(beatmap_id)

                                # Track new IDs (both fast and slow modes)
                                if beatmap_id not in existing_ids:
                                    new_ids_on_page.add(beatmap_id)
                                    if oldest_new_id is None or beatmap_id < oldest_new_id:
                                        oldest_new_id = beatmap_id
                                    if newest_new_id is None or beatmap_id > newest_new_id:
                                        newest_new_id = beatmap_id

                page += 1

                # Progress update
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = self.total_requests / (elapsed / 60) if elapsed > 0 else 0

                if fast_mode:
                    print(f"Page {page:4d} | New: {len(new_ids_on_page):3d}/{len(page_ids):3d} | "
                          f"Total new: {len(all_beatmap_ids):7d} | "
                          f"Rate: {rate:.1f}/min", end='\r')
                else:
                    print(f"Page {page:4d} | Found {len(page_ids):3d} beatmaps | "
                          f"Total: {len(all_beatmap_ids):7d} | "
                          f"Requests: {self.total_requests:5d} | "
                          f"Rate: {rate:.1f}/min", end='\r')

                # Fast mode stopping logic
                if fast_mode and 'desc' in sort:  # Only for newest-first sorts
                    if not new_ids_on_page:  # No new IDs on this page
                        pages_with_all_known += 1
                        if pages_with_all_known >= 2:  # Stop after 2 consecutive pages with all known IDs
                            print(f"\n\nFast mode: Stopped after {page} pages (found 2 consecutive pages with all known IDs)")
                            break
                    else:
                        pages_with_all_known = 0  # Reset counter if we found new IDs

                # Get next page cursor
                cursor_string = data.get('cursor_string')
                if not cursor_string:
                    print(f"\nNo more pages for {status}")
                    break

        except KeyboardInterrupt:
            print(f"\n\nStopped by user. Fetched {len(all_beatmap_ids)} beatmap IDs so far.")

        # Update the oldest new ID tracker (both modes)
        if oldest_new_tracker is not None and oldest_new_id:
            oldest_new_tracker[status] = oldest_new_id
            print(f"Oldest new {status} ID found: {oldest_new_id}")
            if newest_new_id:
                print(f"Newest new {status} ID found: {newest_new_id}")

        return all_beatmap_ids

def save_progress(beatmap_ids, filename='beatmap_ids_progress.json'):
    """Save progress to a file in case we need to resume"""
    with open(filename, 'w') as f:
        json.dump(list(beatmap_ids), f)
    print(f"Progress saved to {filename}")

def load_progress(filename='beatmap_ids_progress.json'):
    """Load previously saved progress"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return set(json.load(f))
    return set()

def save_oldest_new_ids(oldest_new_ids, filename='oldest_new_beatmap_ids.json'):
    """
    Save the oldest new beatmap ID found for each category
    This file should be committed to the repo to track update history
    """
    with open(filename, 'w') as f:
        json.dump(oldest_new_ids, f, indent=2)
    print(f"Oldest new IDs saved to {filename}")

def load_oldest_new_ids(filename='oldest_new_beatmap_ids.json'):
    """Load the oldest new beatmap IDs from previous runs"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {
        'ranked': None,
        'loved': None,
        'last_update': None
    }

def update_mapids_file(all_beatmap_ids, filename='mapids_nodup.txt'):
    """
    Update mapids_nodup.txt by adding only new unique beatmap IDs and maintaining sorted order
    """
    # Read existing IDs
    try:
        with open(filename, 'r') as f:
            existing_ids = set(int(line.strip()) for line in f if line.strip())
        print(f"\nExisting beatmap IDs in {filename}: {len(existing_ids)}")
    except FileNotFoundError:
        existing_ids = set()
        print(f"\n{filename} not found, will create new file")

    # Find new unique IDs
    new_ids = all_beatmap_ids - existing_ids

    if new_ids:
        print(f"New beatmap IDs found: {len(new_ids)}")

        # Combine existing and new IDs, then sort
        combined_ids = existing_ids | new_ids
        sorted_ids = sorted(combined_ids)

        # Rewrite file in sorted order
        with open(filename, 'w') as f:
            for beatmap_id in sorted_ids:
                f.write(f"{beatmap_id}\n")

        print(f"Added {len(new_ids)} new IDs to {filename}")
        print(f"Total beatmap IDs now: {len(sorted_ids)} (sorted)")

        # Show sample of new IDs
        sample = list(sorted(new_ids))[:5]
        if sample:
            print(f"Sample new IDs: {sample}")
    else:
        print("No new beatmap IDs to add")

        # Even if no new IDs, ensure file is sorted
        if existing_ids:
            sorted_ids = sorted(existing_ids)
            with open(filename, 'w') as f:
                for beatmap_id in sorted_ids:
                    f.write(f"{beatmap_id}\n")
            print(f"File verified/sorted with {len(sorted_ids)} IDs")

    return new_ids

def main():
    # Check command line arguments
    approved_only = '--approved' in sys.argv or '-a' in sys.argv
    fast_mode = '--fast' in sys.argv or '-f' in sys.argv

    print("=== osu! Complete Beatmap ID Fetcher ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Rate limit: {REQUESTS_PER_MINUTE} requests/minute")

    if approved_only:
        print("Fetching ONLY APPROVED maps (legacy category)")
    elif fast_mode:
        print("FAST MODE: Only fetching new maps since last update")
    else:
        print("Fetching ALL ranked and loved maps (excluding approved)")

    if not fast_mode:
        print("\nThis script will run for HOURS. It's designed to run overnight.")
    print("Progress is saved periodically in case of interruption.\n")

    # Get API token
    print("Getting API access token...")
    try:
        token_data = api.get_access_token()
        token = token_data['access_token']
        print("Successfully obtained token\n")
    except Exception as e:
        print(f"Failed to get token: {e}")
        return

    fetcher = BeatmapFetcher(token)

    # Load existing IDs if in fast mode (for stopping condition)
    existing_ids = set()
    if fast_mode:
        try:
            with open('mapids_nodup.txt', 'r') as f:
                existing_ids = set(int(line.strip()) for line in f if line.strip())
            print(f"Loaded {len(existing_ids)} existing beatmap IDs for fast mode\n")
        except FileNotFoundError:
            print("Warning: mapids_nodup.txt not found, fast mode will fetch all maps\n")

    # Load oldest new IDs tracker (both modes use this)
    oldest_new_tracker = load_oldest_new_ids()
    if oldest_new_tracker['last_update']:
        print(f"Last update: {oldest_new_tracker['last_update']}")
        if oldest_new_tracker.get('ranked'):
            print(f"Last oldest new ranked ID: {oldest_new_tracker['ranked']}")
        if oldest_new_tracker.get('loved'):
            print(f"Last oldest new loved ID: {oldest_new_tracker['loved']}\n")

    # Load any previous progress
    all_beatmap_ids = load_progress()
    if all_beatmap_ids and not fast_mode:  # Don't resume in fast mode
        print(f"Loaded {len(all_beatmap_ids)} beatmap IDs from previous run\n")
        resume = input("Resume from previous progress? (y/n): ")
        if resume.lower() != 'y':
            all_beatmap_ids = set()

    # Fetch beatmaps by status and sort order
    # We'll try different combinations to maximize coverage
    if approved_only:
        # ONLY fetch approved maps
        strategies = [
            ('approved', 'ranked_desc'),  # Approved maps newest
            ('approved', 'ranked_asc'),   # Approved maps oldest
        ]
    elif fast_mode:
        # Fast mode: only fetch newest first (desc sorts)
        strategies = [
            ('ranked', 'ranked_desc'),    # Newest ranked first
            ('loved', 'updated_desc'),    # Newest loved
        ]
    else:
        # Default: fetch ranked and loved (no approved) in both directions
        strategies = [
            ('ranked', 'ranked_desc'),    # Newest ranked first
            ('ranked', 'ranked_asc'),     # Oldest ranked first
            ('loved', 'updated_desc'),    # Newest loved
            ('loved', 'updated_asc'),     # Oldest loved
        ]

    try:
        for status, sort in strategies:
            # No page limits for these statuses
            max_pages = None

            ids = fetcher.fetch_all_for_status(
                status, sort, max_pages,
                fast_mode=fast_mode,
                existing_ids=existing_ids if fast_mode else None,
                oldest_new_tracker=oldest_new_tracker  # Both modes use this now
            )
            all_beatmap_ids.update(ids)

            # Save progress after each status
            save_progress(all_beatmap_ids)

            print(f"\nTotal unique beatmap IDs so far: {len(all_beatmap_ids)}")
            print(f"Total API requests made: {fetcher.total_requests}")

            elapsed = (datetime.now() - fetcher.start_time).total_seconds()
            print(f"Time elapsed: {elapsed/3600:.1f} hours")
            print("-" * 60)

    except KeyboardInterrupt:
        print("\n\nFetch interrupted by user")

    # Final update of mapids file
    print("\nUpdating mapids_nodup.txt...")
    new_ids = update_mapids_file(all_beatmap_ids)

    # Save oldest new IDs if we found any new ones
    if new_ids and (fast_mode or not approved_only):
        oldest_new_tracker['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_oldest_new_ids(oldest_new_tracker)

    # Clean up progress file
    if os.path.exists('beatmap_ids_progress.json'):
        os.remove('beatmap_ids_progress.json')
        print("Cleaned up progress file")

    # Final statistics
    elapsed = (datetime.now() - fetcher.start_time).total_seconds()
    print(f"\n=== Fetch Complete ===")
    if elapsed < 120:
        print(f"Total time: {elapsed:.1f} seconds")
    else:
        print(f"Total time: {elapsed/3600:.2f} hours")
    print(f"Total API requests: {fetcher.total_requests}")
    print(f"Average rate: {fetcher.total_requests/(elapsed/60):.1f} requests/minute")
    print(f"Total unique beatmap IDs fetched: {len(all_beatmap_ids)}")
    print(f"New IDs added: {len(new_ids)}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()