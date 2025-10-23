#!/usr/bin/env python3
"""
Fetch beatmap metadata from osu! API using aiosu library

This script fetches metadata for beatmaps:
- tags (from v1 API - stored in beatmapset)
- last_update (from v1 API)
- approved_date (from v1 API)
- submit_date (from v1 API)

Usage:
    python3 getmetadata.py                  # Fetch only missing IDs (default)
    python3 getmetadata.py --test 5312654   # Test with specific beatmap ID
    python3 getmetadata.py --resume         # Resume from checkpoint
    python3 getmetadata.py --all            # Re-fetch metadata for all IDs
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from typing import Optional

from aiosu.v1 import Client as V1Client
from aiosu.exceptions import APIException
import calc
import secret
from tqdm.asyncio import tqdm

# Rate limiting configuration (same as original)
REQUESTS_PER_MINUTE_V1 = 60  # API v1 - recommended max (can go up to 1200)

# =============================================================================
# Metadata Fetching with aiosu
# =============================================================================

class BeatmapMetadataFetcher:
    """Fetches beatmap metadata using aiosu v1 client"""

    def __init__(self, api_key: str, rate_limit: int = REQUESTS_PER_MINUTE_V1):
        """
        Initialize the metadata fetcher

        Args:
            api_key: osu! API v1 key
            rate_limit: Requests per minute (default: 60)
        """
        self.api_key = api_key
        # aiosu uses (max_rate, time_period) format
        # For 60 requests per minute: (60, 60)
        self.rate_limit = (rate_limit, 60)
        self.client: Optional[V1Client] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.client = V1Client(self.api_key, limiter=self.rate_limit)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()

    async def get_beatmap_metadata(self, beatmap_id: int) -> Optional[dict]:
        """
        Fetch metadata for a single beatmap from API v1 using aiosu

        Returns dict with:
        - tags: str (from beatmapset)
        - submit_date: str (UTC timestamp)
        - approved_date: str or None
        - last_update: str (UTC timestamp)
        - approved: int (status code)

        Returns None if beatmap not found or error
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use async with context manager.")

        try:
            # Get beatmap data from API v1
            beatmapsets = await self.client.get_beatmap(beatmap_id=beatmap_id)

            if not beatmapsets or len(beatmapsets) == 0:
                return None

            # beatmapsets is a list of Beatmapset objects, each containing one difficulty
            # We only need the first one since we're querying by beatmap_id
            beatmapset = beatmapsets[0]

            # Extract metadata from the beatmapset
            tags = beatmapset.tags if beatmapset.tags else ""

            metadata = {
                'tags': tags,
                'tags_lookup': calc.normalize_for_lookup(tags) if tags else '',
                'submit_date': beatmapset.submitted_date.isoformat() if beatmapset.submitted_date else None,
                'approved_date': beatmapset.ranked_date.isoformat() if beatmapset.ranked_date else None,
                'last_update': beatmapset.last_updated.isoformat() if beatmapset.last_updated else None,
                'approved': beatmapset.status.value if beatmapset.status else 0,
            }

            return metadata

        except APIException as e:
            # API error (404, etc.)
            return None
        except Exception as e:
            # Unexpected error
            print(f"Error fetching beatmap {beatmap_id}: {e}")
            return None

    async def fetch_metadata_batch(
        self,
        beatmap_ids: list[int],
        existing_metadata: Optional[dict] = None,
        fetch_all: bool = False,
    ) -> tuple[dict, list[int]]:
        """
        Fetch metadata for multiple beatmap IDs (async batch processing)

        Args:
            beatmap_ids: List of beatmap IDs to fetch
            existing_metadata: Previously fetched metadata
            fetch_all: If True, re-fetch all IDs. If False (default), only fetch missing IDs

        Returns:
            Tuple of (metadata dict, list of failed IDs)
        """
        if existing_metadata is None:
            existing_metadata = {}

        metadata = dict(existing_metadata)  # Copy existing
        failed_ids = []

        # Filter IDs to fetch
        if fetch_all:
            ids_to_fetch = list(beatmap_ids)
            print(f"\nAll mode: Re-fetching metadata for {len(ids_to_fetch)} beatmaps")
        else:
            ids_to_fetch = [bid for bid in beatmap_ids if str(bid) not in existing_metadata]
            print(f"\nFetching metadata for {len(ids_to_fetch)} beatmaps not in metadata.json")

        if not ids_to_fetch:
            print("All metadata already up to date!")
            return metadata, failed_ids

        # Estimate time
        estimated_seconds = len(ids_to_fetch) * (60.0 / self.rate_limit[0])
        estimated_minutes = estimated_seconds / 60
        print(f"Estimated time: {estimated_minutes:.1f} minutes")
        print(f"Rate limit: {self.rate_limit[0]} requests per minute")
        print()

        # Process all IDs with progress bar
        processed = 0
        failed_count = 0

        # Use tqdm.asyncio for async progress tracking
        pbar = tqdm(ids_to_fetch, desc="Fetching metadata", unit="map")
        for beatmap_id in pbar:
            result = await self.get_beatmap_metadata(beatmap_id)

            if result:
                metadata[str(beatmap_id)] = result
            else:
                failed_ids.append(beatmap_id)
                failed_count += 1

            processed += 1

            # Update progress bar with failure count
            pbar.set_postfix({'failed': failed_count})

            # Save checkpoint every 5000 beatmaps
            if processed % 5000 == 0:
                save_metadata(metadata, 'metadata_checkpoint.json')

        return metadata, failed_ids


async def test_single_map(beatmap_id: int = 5312654):
    """
    Test function to fetch metadata for a single map

    Args:
        beatmap_id: Beatmap ID to test (default: 5312654)
    """
    print("=" * 60)
    print("TEST MODE - Single Beatmap Fetch")
    print("=" * 60)
    print(f"Testing with beatmap ID: {beatmap_id}")
    print()

    # Get API key
    if not hasattr(secret, 'api_key'):
        print("ERROR: API v1 key not found in secret.py")
        print("Please add 'api_key = \"your_api_v1_key\"' to secret.py")
        print("Get your API v1 key from: https://osu.ppy.sh/p/api")
        return

    async with BeatmapMetadataFetcher(secret.api_key) as fetcher:
        print(f"Fetching metadata for beatmap {beatmap_id}...")
        metadata = await fetcher.get_beatmap_metadata(beatmap_id)

        if metadata:
            print("\nMetadata retrieved successfully!")
            print("-" * 60)
            print(f"Tags:          {metadata['tags']}")
            print(f"Submit Date:   {metadata['submit_date']}")
            print(f"Approved Date: {metadata['approved_date']}")
            print(f"Last Update:   {metadata['last_update']}")
            print(f"Approved:      {metadata['approved']}")
            print("-" * 60)
        else:
            print("\nFailed to fetch metadata for this beatmap")
            print("The beatmap may not exist or there was an API error")


# =============================================================================
# File I/O Functions
# =============================================================================

def load_existing_ids(filename='mapids_nodup.txt') -> set[int]:
    """Load existing beatmap IDs from file"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return set(int(line.strip()) for line in f if line.strip())
    return set()


def load_metadata(filename='metadata.json') -> dict:
    """Load existing metadata from file"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}


def save_metadata(metadata: dict, filename='metadata.json'):
    """Save metadata to file (sorted by beatmap ID)"""
    sorted_metadata = {k: metadata[k] for k in sorted(metadata.keys(), key=int)}

    with open(filename, 'w') as f:
        json.dump(sorted_metadata, f, indent=2)

    print(f"\nSaved metadata for {len(metadata)} beatmaps to {filename}")


# =============================================================================
# Main
# =============================================================================

async def main():
    """Main async function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Fetch beatmap metadata from osu! API using aiosu library',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 getmetadata.py                  # Fetch only missing IDs (default)
  python3 getmetadata.py --test 5312654   # Test with specific beatmap ID
  python3 getmetadata.py --resume         # Resume from checkpoint
  python3 getmetadata.py --all            # Re-fetch metadata for all IDs
        """
    )
    parser.add_argument('--test', '-t', type=int, metavar='BEATMAP_ID',
                        help='Test mode: fetch metadata for a single beatmap (specify beatmap ID)')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Re-fetch metadata for all IDs (default: only missing)')
    parser.add_argument('--resume', '-r', action='store_true',
                        help='Resume from checkpoint file')

    args = parser.parse_args()

    print("=== osu! Beatmap Metadata Fetcher (aiosu) ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test mode - single map
    if args.test:
        await test_single_map(args.test)
        return

    print(f"All mode: {'Yes' if args.all else 'No (default: only missing)'}")
    print(f"Resume mode: {'Yes' if args.resume else 'No'}")
    print()

    # Get API v1 key
    if not hasattr(secret, 'api_key'):
        print("ERROR: API v1 key not found in secret.py")
        print("Please add 'api_key = \"your_api_v1_key\"' to secret.py")
        print("Get your API v1 key from: https://osu.ppy.sh/p/api")
        return

    # Load beatmap IDs
    all_beatmap_ids = load_existing_ids()
    if not all_beatmap_ids:
        print("No beatmap IDs found in mapids_nodup.txt!")
        print("Please run the ID fetcher first or ensure the file exists")
        return

    print(f"Loaded {len(all_beatmap_ids)} beatmap IDs from mapids_nodup.txt")

    # Load existing metadata (or checkpoint if resuming)
    if args.resume and os.path.exists('metadata_checkpoint.json'):
        print("Resuming from checkpoint...")
        existing_metadata = load_metadata('metadata_checkpoint.json')
        print(f"Loaded checkpoint with metadata for {len(existing_metadata)} beatmaps")
    else:
        existing_metadata = load_metadata()
        print(f"Loaded existing metadata for {len(existing_metadata)} beatmaps")
    print()

    # Fetch metadata using aiosu
    print("=" * 60)
    print("FETCHING BEATMAP METADATA (API v1 via aiosu)")
    print("=" * 60)

    try:
        async with BeatmapMetadataFetcher(secret.api_key) as fetcher:
            metadata, failed_ids = await fetcher.fetch_metadata_batch(
                list(all_beatmap_ids),
                existing_metadata=existing_metadata,
                fetch_all=args.all
            )

            # Save metadata
            save_metadata(metadata)

            if failed_ids:
                print(f"\nFailed to fetch metadata for {len(failed_ids)} beatmaps")
                # Save failed IDs
                with open('metadata_failed.txt', 'w') as f:
                    for bid in failed_ids:
                        f.write(f"{bid}\n")
                print(f"Failed IDs saved to metadata_failed.txt")

            # Clean up checkpoint after successful completion
            if os.path.exists('metadata_checkpoint.json'):
                os.remove('metadata_checkpoint.json')
                print("Checkpoint file removed (run completed successfully)")

    except KeyboardInterrupt:
        print("\n\nMetadata fetch interrupted by user")
        print("Progress has been saved to metadata_checkpoint.json")
        print("Run with --resume to continue from checkpoint")

    # Final summary
    print()
    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    asyncio.run(main())
