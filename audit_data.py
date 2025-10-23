#!/usr/bin/env python3
"""
Audit script to check data completeness for all beatmap IDs

Creates a JSON file showing which data exists for each beatmap ID.
Based on DATA_SOURCES.md, checks all granular fields.

Files checked:
- .osu file (in maps/)
- stats.json fields (hp, cs, od, ar, title, artist, creator, version, source,
                     title_lookup, artist_lookup, creator_lookup, version_lookup, source_lookup,
                     length, max_bpm, circles, sliders, spinners, divisor)
- metadata.json fields (tags, tags_lookup, submit_date, approved_date, last_update, approved)
- srs.json fields (sr, aim, tap)
- srs_dt.json fields (sr, aim, tap)
- srs_hr.json fields (sr, aim, tap)
- buckets/*.dist files (map structure analysis - bucket data)
- sliders/*.sldr files (slider pattern analysis)
- dists/*.dist files (object distribution data)

Usage:
    python3 audit_data.py                   # Create audit.json and print summary
"""

import json
import os


def load_beatmap_ids(filename='mapids_nodup.txt') -> set[int]:
    """Load all beatmap IDs from mapids_nodup.txt"""
    if not os.path.exists(filename):
        print(f"ERROR: {filename} not found!")
        return set()

    with open(filename, 'r') as f:
        return set(int(line.strip()) for line in f if line.strip())


def load_json_file(filename: str) -> dict:
    """Load a JSON file and return its contents (empty dict if not found)"""
    if not os.path.exists(filename):
        return {}

    with open(filename, 'r') as f:
        return json.load(f)


def check_osu_file(beatmap_id: int, maps_dir='maps') -> bool:
    """Check if .osu file exists for this beatmap"""
    osu_path = os.path.join(maps_dir, f"{beatmap_id}.osu")
    return os.path.exists(osu_path)


def check_bucket_file(beatmap_id: int, buckets_dir='buckets') -> bool:
    """Check if bucket file exists for this beatmap (stored as .dist in buckets/)"""
    bkt_path = os.path.join(buckets_dir, f"{beatmap_id}.dist")
    return os.path.exists(bkt_path)


def check_slider_file(beatmap_id: int, sliders_dir='sliders') -> bool:
    """Check if .sldr file exists for this beatmap"""
    sldr_path = os.path.join(sliders_dir, f"{beatmap_id}.sldr")
    return os.path.exists(sldr_path)


def check_dist_file(beatmap_id: int, dists_dir='dists') -> bool:
    """Check if .dist file exists for this beatmap"""
    dist_path = os.path.join(dists_dir, f"{beatmap_id}.dist")
    return os.path.exists(dist_path)


def check_stats_fields(beatmap_id: str, stats_data: dict) -> dict:
    """Check which stats.json fields exist for this beatmap"""
    if beatmap_id not in stats_data:
        return {
            'hp': False, 'cs': False, 'od': False, 'ar': False,
            'title': False, 'artist': False, 'creator': False, 'version': False, 'source': False,
            'title_lookup': False, 'artist_lookup': False, 'creator_lookup': False,
            'version_lookup': False, 'source_lookup': False,
            'length': False, 'max_bpm': False,
            'circles': False, 'sliders': False, 'spinners': False,
            'divisor': False,
        }

    data = stats_data[beatmap_id]
    return {
        'hp': 'hp' in data and data['hp'] is not None,
        'cs': 'cs' in data and data['cs'] is not None,
        'od': 'od' in data and data['od'] is not None,
        'ar': 'ar' in data and data['ar'] is not None,
        'title': 'title' in data and data['title'] is not None,
        'artist': 'artist' in data and data['artist'] is not None,
        'creator': 'creator' in data and data['creator'] is not None,
        'version': 'version' in data and data['version'] is not None,
        'source': 'source' in data,  # Can be empty string, so just check existence
        'title_lookup': 'title_lookup' in data and data['title_lookup'] is not None,
        'artist_lookup': 'artist_lookup' in data and data['artist_lookup'] is not None,
        'creator_lookup': 'creator_lookup' in data and data['creator_lookup'] is not None,
        'version_lookup': 'version_lookup' in data and data['version_lookup'] is not None,
        'source_lookup': 'source_lookup' in data,  # Can be empty string
        'length': 'length' in data and data['length'] is not None,
        'max_bpm': 'max_bpm' in data and data['max_bpm'] is not None,
        'circles': 'circles' in data and data['circles'] is not None,
        'sliders': 'sliders' in data and data['sliders'] is not None,
        'spinners': 'spinners' in data and data['spinners'] is not None,
        'divisor': 'divisor' in data and data['divisor'] is not None,
    }


def check_metadata_fields(beatmap_id: str, metadata_data: dict) -> dict:
    """Check which metadata.json fields exist for this beatmap"""
    if beatmap_id not in metadata_data:
        return {
            'tags': False, 'tags_lookup': False,
            'submit_date': False, 'approved_date': False, 'last_update': False, 'approved': False,
        }

    data = metadata_data[beatmap_id]
    return {
        'tags': 'tags' in data,  # Can be empty string
        'tags_lookup': 'tags_lookup' in data,  # Can be empty string
        'submit_date': 'submit_date' in data and data['submit_date'] is not None,
        'approved_date': 'approved_date' in data,  # Can be null, so just check existence
        'last_update': 'last_update' in data and data['last_update'] is not None,
        'approved': 'approved' in data and data['approved'] is not None,
    }


def check_srs_fields(beatmap_id: str, srs_data: dict) -> dict:
    """Check which srs.json fields exist for this beatmap"""
    if beatmap_id not in srs_data:
        return {'sr': False, 'aim': False, 'tap': False}

    data = srs_data[beatmap_id]

    # srs.json uses array format: [sr, aim, tap]
    if isinstance(data, list) and len(data) == 3:
        return {
            'sr': data[0] is not None,
            'aim': data[1] is not None,
            'tap': data[2] is not None,
        }

    # Fallback for object format (if it exists)
    return {
        'sr': 'sr' in data and data['sr'] is not None,
        'aim': 'aim' in data and data['aim'] is not None,
        'tap': 'tap' in data and data['tap'] is not None,
    }


def audit_all_beatmaps(beatmap_ids: set[int]) -> dict:
    """
    Create granular audit data for all beatmap IDs

    Returns dict: {beatmap_id: {category: {field: bool, ...}, ...}, ...}
    """
    print(f"Auditing {len(beatmap_ids)} beatmap IDs...")
    print()

    # Load data files
    print("Loading data files...")
    stats_data = load_json_file('stats.json')
    metadata_data = load_json_file('metadata.json')
    srs_data = load_json_file('srs.json')
    srs_dt_data = load_json_file('srs_dt.json')
    srs_hr_data = load_json_file('srs_hr.json')

    print(f"  - stats.json: {len(stats_data)} entries")
    print(f"  - metadata.json: {len(metadata_data)} entries")
    print(f"  - srs.json: {len(srs_data)} entries")
    print(f"  - srs_dt.json: {len(srs_dt_data)} entries")
    print(f"  - srs_hr.json: {len(srs_hr_data)} entries")
    print()

    # Build audit data
    audit = {}

    for beatmap_id in sorted(beatmap_ids):
        bid_str = str(beatmap_id)

        audit[bid_str] = {
            'osu_file': check_osu_file(beatmap_id),
            'stats': check_stats_fields(bid_str, stats_data),
            'metadata': check_metadata_fields(bid_str, metadata_data),
            'srs_nm': check_srs_fields(bid_str, srs_data),
            'srs_dt': check_srs_fields(bid_str, srs_dt_data),
            'srs_hr': check_srs_fields(bid_str, srs_hr_data),
            'bucket_file': check_bucket_file(beatmap_id),
            'slider_file': check_slider_file(beatmap_id),
            'dist_file': check_dist_file(beatmap_id),
        }

    return audit


def calculate_summary(audit: dict) -> dict:
    """Calculate summary statistics from audit data"""
    total = len(audit)

    # Initialize all field counts to 0 (ensures we show fields even if count is 0)
    stats_fields = ['hp', 'cs', 'od', 'ar', 'title', 'artist', 'creator', 'version', 'source',
                    'title_lookup', 'artist_lookup', 'creator_lookup', 'version_lookup', 'source_lookup',
                    'length', 'max_bpm', 'circles', 'sliders', 'spinners', 'divisor']
    metadata_fields = ['tags', 'tags_lookup', 'submit_date', 'approved_date', 'last_update', 'approved']
    srs_fields = ['sr', 'aim', 'tap']

    # Count how many beatmaps have each field
    osu_file_count = 0
    bucket_file_count = 0
    slider_file_count = 0
    dist_file_count = 0
    stats_field_counts = {field: 0 for field in stats_fields}
    metadata_field_counts = {field: 0 for field in metadata_fields}
    srs_nm_field_counts = {field: 0 for field in srs_fields}
    srs_dt_field_counts = {field: 0 for field in srs_fields}
    srs_hr_field_counts = {field: 0 for field in srs_fields}

    # Count complete beatmaps (have all required fields)
    complete_osu_file = 0
    complete_stats = 0
    complete_metadata = 0
    complete_srs_nm = 0
    complete_srs_dt = 0
    complete_srs_hr = 0

    for beatmap_id, data in audit.items():
        # Count .osu file
        if data['osu_file']:
            osu_file_count += 1
            complete_osu_file += 1

        # Count generated files
        if data.get('bucket_file', False):
            bucket_file_count += 1
        if data.get('slider_file', False):
            slider_file_count += 1
        if data.get('dist_file', False):
            dist_file_count += 1

        # Count stats fields
        for field, exists in data['stats'].items():
            if exists:
                stats_field_counts[field] += 1
        if all(data['stats'].values()):
            complete_stats += 1

        # Count metadata fields
        for field, exists in data['metadata'].items():
            if exists:
                metadata_field_counts[field] += 1
        if all(data['metadata'].values()):
            complete_metadata += 1

        # Count srs_nm fields
        for field, exists in data['srs_nm'].items():
            if exists:
                srs_nm_field_counts[field] += 1
        if all(data['srs_nm'].values()):
            complete_srs_nm += 1

        # Count srs_dt fields
        for field, exists in data['srs_dt'].items():
            if exists:
                srs_dt_field_counts[field] += 1
        if all(data['srs_dt'].values()):
            complete_srs_dt += 1

        # Count srs_hr fields
        for field, exists in data['srs_hr'].items():
            if exists:
                srs_hr_field_counts[field] += 1
        if all(data['srs_hr'].values()):
            complete_srs_hr += 1

    return {
        'total_beatmaps': total,
        'osu_file': {
            'count': osu_file_count,
            'percentage': (osu_file_count / total * 100) if total > 0 else 0,
        },
        'bucket_file': {
            'count': bucket_file_count,
            'percentage': (bucket_file_count / total * 100) if total > 0 else 0,
        },
        'slider_file': {
            'count': slider_file_count,
            'percentage': (slider_file_count / total * 100) if total > 0 else 0,
        },
        'dist_file': {
            'count': dist_file_count,
            'percentage': (dist_file_count / total * 100) if total > 0 else 0,
        },
        'stats': {
            'complete_count': complete_stats,
            'complete_percentage': (complete_stats / total * 100) if total > 0 else 0,
            'field_counts': dict(stats_field_counts),
            'field_percentages': {k: (v / total * 100) if total > 0 else 0 for k, v in stats_field_counts.items()},
        },
        'metadata': {
            'complete_count': complete_metadata,
            'complete_percentage': (complete_metadata / total * 100) if total > 0 else 0,
            'field_counts': dict(metadata_field_counts),
            'field_percentages': {k: (v / total * 100) if total > 0 else 0 for k, v in metadata_field_counts.items()},
        },
        'srs_nm': {
            'complete_count': complete_srs_nm,
            'complete_percentage': (complete_srs_nm / total * 100) if total > 0 else 0,
            'field_counts': dict(srs_nm_field_counts),
            'field_percentages': {k: (v / total * 100) if total > 0 else 0 for k, v in srs_nm_field_counts.items()},
        },
        'srs_dt': {
            'complete_count': complete_srs_dt,
            'complete_percentage': (complete_srs_dt / total * 100) if total > 0 else 0,
            'field_counts': dict(srs_dt_field_counts),
            'field_percentages': {k: (v / total * 100) if total > 0 else 0 for k, v in srs_dt_field_counts.items()},
        },
        'srs_hr': {
            'complete_count': complete_srs_hr,
            'complete_percentage': (complete_srs_hr / total * 100) if total > 0 else 0,
            'field_counts': dict(srs_hr_field_counts),
            'field_percentages': {k: (v / total * 100) if total > 0 else 0 for k, v in srs_hr_field_counts.items()},
        },
    }


def print_summary(summary: dict):
    """Print summary statistics"""
    total = summary['total_beatmaps']

    print("=" * 80)
    print("DATA COMPLETENESS SUMMARY")
    print("=" * 80)
    print()
    print(f"Total beatmaps: {total:,}")
    print()

    # .osu files
    print("=== .osu Files (MANDATORY) ===")
    print(f"Complete: {summary['osu_file']['count']:,} ({summary['osu_file']['percentage']:.2f}%)")
    print(f"Missing:  {total - summary['osu_file']['count']:,}")
    print()

    # Generated files
    print("=== Generated Files (MANDATORY for similarity search) ===")
    print(f"Buckets (buckets/*.dist):  {summary['bucket_file']['count']:,} ({summary['bucket_file']['percentage']:.2f}%)")
    print(f"  Missing:                 {total - summary['bucket_file']['count']:,}")
    print(f"Sliders (sliders/*.sldr):  {summary['slider_file']['count']:,} ({summary['slider_file']['percentage']:.2f}%) [optional]")
    print(f"  Missing:                 {total - summary['slider_file']['count']:,}")
    print(f"Dists (dists/*.dist):      {summary['dist_file']['count']:,} ({summary['dist_file']['percentage']:.2f}%) [optional]")
    print(f"  Missing:                 {total - summary['dist_file']['count']:,}")
    print()

    # stats.json
    print("=== stats.json (MANDATORY for filtering) ===")
    print(f"Complete (all fields): {summary['stats']['complete_count']:,} ({summary['stats']['complete_percentage']:.2f}%)")
    print()

    # Define mandatory vs optional stats fields
    mandatory_stats = {'hp', 'cs', 'od', 'ar', 'title', 'artist', 'creator', 'version',
                       'title_lookup', 'artist_lookup', 'creator_lookup', 'version_lookup',
                       'length', 'max_bpm', 'circles', 'sliders', 'spinners'}
    optional_stats = {'source', 'source_lookup', 'divisor'}

    print("Field Coverage (MANDATORY):")
    for field in sorted(f for f in summary['stats']['field_counts'].keys() if f in mandatory_stats):
        count = summary['stats']['field_counts'][field]
        pct = summary['stats']['field_percentages'][field]
        missing = total - count
        print(f"  {field:20s}: {count:7,} ({pct:6.2f}%)  Missing: {missing:7,}")

    print("\nField Coverage (OPTIONAL):")
    for field in sorted(f for f in summary['stats']['field_counts'].keys() if f in optional_stats):
        count = summary['stats']['field_counts'][field]
        pct = summary['stats']['field_percentages'][field]
        missing = total - count
        print(f"  {field:20s}: {count:7,} ({pct:6.2f}%)  Missing: {missing:7,}")
    print()

    # metadata.json
    print("=== metadata.json (OPTIONAL - for filters) ===")
    print(f"Complete (all fields): {summary['metadata']['complete_count']:,} ({summary['metadata']['complete_percentage']:.2f}%)")
    print()
    print("Field Coverage:")
    for field in sorted(summary['metadata']['field_counts'].keys()):
        count = summary['metadata']['field_counts'][field]
        pct = summary['metadata']['field_percentages'][field]
        missing = total - count
        print(f"  {field:20s}: {count:7,} ({pct:6.2f}%)  Missing: {missing:7,}")
    print()

    # srs.json (NM)
    print("=== srs.json (NoMod) - OPTIONAL for SR filtering ===")
    print(f"Complete (all fields): {summary['srs_nm']['complete_count']:,} ({summary['srs_nm']['complete_percentage']:.2f}%)")
    print()
    print("Field Coverage:")
    for field in sorted(summary['srs_nm']['field_counts'].keys()):
        count = summary['srs_nm']['field_counts'][field]
        pct = summary['srs_nm']['field_percentages'][field]
        missing = total - count
        print(f"  {field:20s}: {count:7,} ({pct:6.2f}%)  Missing: {missing:7,}")
    print()

    # srs_dt.json
    print("=== srs_dt.json (DoubleTime) - OPTIONAL for DT SR filtering ===")
    print(f"Complete (all fields): {summary['srs_dt']['complete_count']:,} ({summary['srs_dt']['complete_percentage']:.2f}%)")
    print()
    print("Field Coverage:")
    for field in sorted(summary['srs_dt']['field_counts'].keys()):
        count = summary['srs_dt']['field_counts'][field]
        pct = summary['srs_dt']['field_percentages'][field]
        missing = total - count
        print(f"  {field:20s}: {count:7,} ({pct:6.2f}%)  Missing: {missing:7,}")
    print()

    # srs_hr.json
    print("=== srs_hr.json (HardRock) - OPTIONAL for HR SR filtering ===")
    print(f"Complete (all fields): {summary['srs_hr']['complete_count']:,} ({summary['srs_hr']['complete_percentage']:.2f}%)")
    print()
    print("Field Coverage:")
    for field in sorted(summary['srs_hr']['field_counts'].keys()):
        count = summary['srs_hr']['field_counts'][field]
        pct = summary['srs_hr']['field_percentages'][field]
        missing = total - count
        print(f"  {field:20s}: {count:7,} ({pct:6.2f}%)  Missing: {missing:7,}")

    print("=" * 80)
    print("\nLEGEND:")
    print("  MANDATORY - Required for map to appear in similarity results")
    print("  OPTIONAL  - Enables additional filtering but not required for basic functionality")


def main():
    """Main function"""
    print("=== Beatmap Data Audit ===")
    print()

    # Load beatmap IDs
    beatmap_ids = load_beatmap_ids()
    if not beatmap_ids:
        print("No beatmap IDs found!")
        return

    # Audit all beatmaps
    audit = audit_all_beatmaps(beatmap_ids)

    # Save audit data
    with open('audit.json', 'w') as f:
        json.dump(audit, f, indent=2)

    print(f"Saved audit data for {len(audit):,} beatmaps to audit.json")
    print()

    # Calculate and print summary
    summary = calculate_summary(audit)
    print_summary(summary)


if __name__ == '__main__':
    main()
