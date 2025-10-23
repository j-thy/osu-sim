#!/usr/bin/env python3
"""
Fetch beatmap IDs from osu! API using aiosu library

This script fetches beatmap IDs from the osu! API v2 and saves them to mapids_nodup.txt.
Only standard mode (osu!) beatmaps are fetched.

For metadata fetching (tags, dates, etc.), use getmapapi_aiosu.py instead.

Usage:
    python3 getmapapi.py                # Fetch all beatmap IDs
    python3 getmapapi.py --fast         # Fast mode: only fetch new data
    python3 getmapapi.py --approved     # Fetch ONLY approved maps (legacy)

Options:
    --fast, -f          Fast mode: only fetch new/updated data since last run
    --approved, -a      Fetch ONLY approved maps (legacy category, rare)
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from typing import Optional

from aiosu.v2 import Client as V2Client
from aiosu.models import OAuthToken
from aiosu.exceptions import APIException
import api
from tqdm.asyncio import tqdm

# Rate limiting configuration
REQUESTS_PER_MINUTE_V2 = 60  # API v2 - recommended max

# =============================================================================
# API v2 - Beatmap ID Fetching with aiosu
# =============================================================================

class BeatmapIDFetcher:
    """Fetches beatmap IDs using aiosu v2 client"""

    def __init__(self, client_id: int, client_secret: str, rate_limit: int = REQUESTS_PER_MINUTE_V2):
        """
        Initialize the beatmap ID fetcher

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            rate_limit: Requests per minute (default: 60)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        # aiosu uses (max_rate, time_period) format
        self.rate_limit = (rate_limit, 60)
        self.client: Optional[V2Client] = None
        self.total_requests = 0
        self.start_time = datetime.now()

    async def __aenter__(self):
        """Async context manager entry"""
        # Create OAuth token for client credentials grant
        # aiosu will handle token refresh automatically
        self.client = V2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            limiter=self.rate_limit
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()

    async def search_beatmapsets(
        self,
        status: str = 'ranked',
        cursor_string: Optional[str] = None,
        sort: str = 'ranked_desc'
    ):
        """
        Search for beatmapsets with rate limiting (API v2)

        Args:
            status: Beatmap status (ranked, loved, approved)
            cursor_string: Pagination cursor
            sort: Sort order (ranked_desc, ranked_asc, updated_desc, updated_asc)

        Returns:
            BeatmapsetSearchResponse or None on error
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use async with context manager.")

        try:
            # Use aiosu's search_beatmapsets method
            result = await self.client.search_beatmapsets(
                category=status,
                sort=sort,
                cursor_string=cursor_string
            )
            self.total_requests += 1
            return result

        except APIException as e:
            print(f"API Error: {e}")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    async def fetch_all_for_status(
        self,
        status: str,
        sort: str = 'ranked_desc',
        max_pages: Optional[int] = None,
        fast_mode: bool = False,
        existing_ids: Optional[set] = None
    ) -> set[int]:
        """
        Fetch ALL beatmap IDs for a given status

        Args:
            status: Beatmap status (ranked, loved, approved)
            sort: Sort order
            max_pages: Maximum pages to fetch (None = unlimited)
            fast_mode: Stop early when encountering known IDs
            existing_ids: Set of already-known IDs (for fast mode)

        Returns:
            Set of beatmap IDs
        """
        all_beatmap_ids = set()
        cursor_string = None
        page = 0
        consecutive_empty = 0
        pages_with_all_known = 0

        if existing_ids is None:
            existing_ids = set()

        print(f"\nFetching {'new' if fast_mode else 'ALL'} {status} beatmap IDs (sort: {sort})...")

        try:
            while True:
                if max_pages and page >= max_pages:
                    print(f"Reached max pages limit ({max_pages})")
                    break

                result = await self.search_beatmapsets(status, cursor_string, sort)

                if not result or not result.beatmapsets:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        print("No more data available")
                        break
                    continue

                beatmapsets = result.beatmapsets
                consecutive_empty = 0

                # Extract beatmap IDs (only standard mode)
                page_ids = set()
                new_ids_on_page = set()
                for beatmapset in beatmapsets:
                    if beatmapset.beatmaps:
                        for beatmap in beatmapset.beatmaps:
                            # Only standard mode (mode_int == 0)
                            if beatmap.mode_int == 0:
                                beatmap_id = beatmap.id
                                page_ids.add(beatmap_id)
                                all_beatmap_ids.add(beatmap_id)

                                if beatmap_id not in existing_ids:
                                    new_ids_on_page.add(beatmap_id)

                page += 1

                # Progress update
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = self.total_requests / (elapsed / 60) if elapsed > 0 else 0

                if fast_mode:
                    print(f"Page {page:4d} | New: {len(new_ids_on_page):3d}/{len(page_ids):3d} | "
                          f"Total: {len(all_beatmap_ids):7d} | Rate: {rate:.1f}/min", end='\r')
                else:
                    print(f"Page {page:4d} | Found {len(page_ids):3d} | "
                          f"Total: {len(all_beatmap_ids):7d} | Rate: {rate:.1f}/min", end='\r')

                # Fast mode stopping logic
                if fast_mode and 'desc' in sort:
                    if not new_ids_on_page:
                        pages_with_all_known += 1
                        if pages_with_all_known >= 2:
                            print(f"\nFast mode: Stopped after {page} pages (2 consecutive pages with all known IDs)")
                            break
                    else:
                        pages_with_all_known = 0

                # Get next page cursor
                cursor_string = result.cursor_string
                if not cursor_string:
                    print(f"\nNo more pages for {status}")
                    break

        except KeyboardInterrupt:
            print(f"\n\nStopped by user. Fetched {len(all_beatmap_ids)} beatmap IDs so far.")

        return all_beatmap_ids


# =============================================================================
# File I/O Functions
# =============================================================================

def load_existing_ids(filename='mapids_nodup.txt') -> set[int]:
    """Load existing beatmap IDs from file"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return set(int(line.strip()) for line in f if line.strip())
    return set()


def save_beatmap_ids(beatmap_ids: set[int], filename='mapids_nodup.txt') -> set[int]:
    """Save beatmap IDs to file (sorted, deduplicated)"""
    existing_ids = load_existing_ids(filename)
    all_ids = existing_ids | beatmap_ids
    new_ids = beatmap_ids - existing_ids

    sorted_ids = sorted(all_ids)

    with open(filename, 'w') as f:
        for beatmap_id in sorted_ids:
            f.write(f"{beatmap_id}\n")

    print(f"\nSaved {len(all_ids)} total IDs to {filename}")
    if new_ids:
        print(f"Added {len(new_ids)} new IDs")

    return new_ids


# =============================================================================
# Main
# =============================================================================

async def main():
    """Main async function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Fetch beatmap IDs from osu! API using aiosu library',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 getmapids.py                # Fetch all beatmap IDs
  python3 getmapids.py --fast         # Fast mode: only fetch new data
  python3 getmapids.py --approved     # Fetch ONLY approved maps (legacy)
        """
    )
    parser.add_argument('--fast', '-f', action='store_true',
                        help='Fast mode: only fetch new/updated data since last run')
    parser.add_argument('--approved', '-a', action='store_true',
                        help='Fetch ONLY approved maps (legacy category, rare)')

    args = parser.parse_args()

    print("=== osu! Beatmap ID Fetcher (aiosu) ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Fast mode: {'Yes' if args.fast else 'No'}")
    print(f"Approved only: {'Yes' if args.approved else 'No'}")
    print()

    # Get OAuth credentials
    print("Getting API v2 access token...")
    try:
        # Use the existing api.py to get OAuth token
        import secret
        token_data = api.get_access_token()

        # Extract client credentials from secret.py
        if not hasattr(secret, 'client_id') or not hasattr(secret, 'client_secret'):
            print("ERROR: client_id or client_secret not found in secret.py")
            print("Please add these OAuth credentials to secret.py")
            return

        print("Successfully obtained token\n")
    except Exception as e:
        print(f"Failed to get token: {e}")
        return

    print("=" * 60)
    print("FETCHING BEATMAP IDs (API v2 via aiosu)")
    print("=" * 60)

    # Load existing IDs
    existing_ids = load_existing_ids()
    print(f"Loaded {len(existing_ids)} existing beatmap IDs\n")

    # Determine fetch strategies
    if args.approved:
        strategies = [
            ('approved', 'ranked_desc'),
            ('approved', 'ranked_asc'),
        ]
    elif args.fast:
        strategies = [
            ('ranked', 'ranked_desc'),
            ('loved', 'updated_desc'),
        ]
    else:
        strategies = [
            ('ranked', 'ranked_desc'),
            ('ranked', 'ranked_asc'),
            ('loved', 'updated_desc'),
            ('loved', 'updated_asc'),
        ]

    # Fetch IDs using aiosu
    all_beatmap_ids = set()

    try:
        async with BeatmapIDFetcher(secret.client_id, secret.client_secret) as fetcher:
            for status, sort in strategies:
                ids = await fetcher.fetch_all_for_status(
                    status, sort, max_pages=None,
                    fast_mode=args.fast,
                    existing_ids=existing_ids if args.fast else None
                )
                all_beatmap_ids.update(ids)

                print(f"\nTotal unique beatmap IDs so far: {len(all_beatmap_ids)}")
                print("-" * 60)

    except KeyboardInterrupt:
        print("\n\nFetch interrupted by user")

    # Save IDs
    if all_beatmap_ids:
        new_ids = save_beatmap_ids(all_beatmap_ids)
        print(f"Total beatmap IDs: {len(existing_ids | all_beatmap_ids)}")
    else:
        print("No beatmap IDs were fetched")

    # Final summary
    print()
    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Note: For metadata fetching (tags, dates, etc.), use getmapapi_aiosu.py")


if __name__ == '__main__':
    asyncio.run(main())
