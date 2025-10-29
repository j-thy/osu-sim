import bisect
import json
import math
import numpy as np
import os
import random
from tqdm import tqdm
from scipy.spatial import cKDTree

import calc
from filters import apply_filter, extract_sr_range
import getmaps
import getbuckets
import getsrs

# Maximum euclidean distance threshold for star rating similarity
# Lower values = faster but more restrictive SR range
# Higher values = slower but broader SR range
# Based on analysis: euclidean distance 0.7 ≈ SR range of 1.0 star
MAX_SR_EUCLIDEAN_DISTANCE = 0.7

# Maximum allowed SR filter range (in stars)
# Users can filter within a maximum range of 1.0 star (e.g., sr>=6, sr<=7)
MAX_SR_FILTER_RANGE = 1.0

def manhattan(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))

def euclidean(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

def get_buckets(buckets_file):
    buckets = {}
    with open(buckets_file, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            buckets[int(lines[i])] = np.array(eval(lines[i+1]))
    return buckets

def kl_divergence(p, q):
    return np.sum(np.where(p*q != 0, np.log(p / q), 0))

def min_similarity(p, q):
    return np.sum(np.minimum(p, q))

def get_similarity(b1, b2):
    tol = 0.025 # ms tolerance (% of time)

    sim = 0
    for t1 in b1:
        for t2 in b2:
            tol_ms = (t1 + t2) / 2 * tol
            t_corr = min(max(0, 10 + tol_ms - abs(t1 - t2)), 10) / 10
            sim += t_corr * min_similarity(b1[t1], b2[t2])
    return sim

def get_slider_similarity(s1, s2):
    """
    Calculate slider similarity between two slider stats.

    Args:
        s1, s2: Slider stats tuples ((avg_len, avg_vel), (std_len, std_vel), time_ratio)

    Returns:
        Similarity score (lower is more similar)
    """
    if not s1[0][0] or not s2[0][0]:
        return float('inf')

    avg1, avg2 = s1[0], s2[0]
    # Relative difference in average length and velocity
    similarity = abs(avg1[0] - avg2[0]) / (avg1[0] + avg2[0]) + abs(avg1[1] - avg2[1]) / (avg1[1] + avg2[1])

    # Add time ratio difference (weighted 2x more heavily)
    similarity += abs(s1[2] - s2[2]) * 2

    return similarity

def get_similar(id, text, n=50, filters=None):
    dist = calc.get_distribution_raw(text)
    bkts = getbuckets.get_buckets_raw(dist)

    key = str(id)
    if key in srs:
        sr = srs[key]
    else:
        chars = '1234567890qwertyuiopasdfghjklzxcvbnm'
        temp_filename = ''.join(chars[random.randrange(len(chars))] for _ in range(10)) + '.osu'
        with open(temp_filename, 'w', encoding='utf8', newline='') as f:
            f.write(text)
        sr = getsrs.get_sr_file(temp_filename)
        os.remove(temp_filename)

    # Calculate self-similarity for normalization (100% = identical map)
    max_similarity = get_similarity(bkts, bkts)

    similarities = []

    def get_stat(id, key):
        if key == 'id':
            return int(id)
        elif key in ['sr', 'star', 'stars']:
            return getsrs.get_sr(id)[0]
        elif key in ['aim', 'aimsr']:
            return getsrs.get_sr(id)[1]
        elif key in ['tap', 'tapsr']:
            return getsrs.get_sr(id)[2]
        elif key == 'bpm':
            # bpm is an alias for max_bpm
            if id in stats and 'max_bpm' in stats[id]:
                return stats[id]['max_bpm']
        elif key in ['drain', 'dr']:
            # drain and dr are aliases for hp
            if id in stats and 'hp' in stats[id]:
                return stats[id]['hp']
        # String filters - use lookup fields
        elif key == 'tags':
            # Tags come from metadata.json (pre-computed tags_lookup)
            if id in metadata and 'tags_lookup' in metadata[id]:
                return metadata[id]['tags_lookup']
        elif key in ['artist', 'creator', 'title', 'source']:
            if id in stats and f'{key}_lookup' in stats[id]:
                return stats[id][f'{key}_lookup']
        elif key in ['difficulty', 'diff', 'version']:
            if id in stats and 'version_lookup' in stats[id]:
                return stats[id]['version_lookup']
        # Status/category filter - maps status codes to string names
        elif key in ['status', 'category']:
            if id in metadata and 'approved' in metadata[id]:
                status_code = metadata[id]['approved']
                status_map = {-2: 'graveyard', -1: 'wip', 0: 'pending',
                             1: 'ranked', 2: 'approved', 3: 'qualified', 4: 'loved'}
                return status_map.get(status_code, '')
        # Date filters - from metadata.json
        elif key in ['created', 'submitted']:
            # Return submit_date from metadata.json
            if id in metadata and 'submit_date' in metadata[id]:
                return metadata[id]['submit_date']
        elif key == 'ranked':
            # Return approved_date from metadata.json
            if id in metadata and 'approved_date' in metadata[id]:
                return metadata[id]['approved_date']
        elif key == 'updated':
            # Return last_update from metadata.json
            if id in metadata and 'last_update' in metadata[id]:
                return metadata[id]['last_update']
        elif id in stats and key in stats[id]:
            return stats[id][key]
        return None

    # Determine candidate selection method based on SR filters
    if filters:
        sr_min, sr_max = extract_sr_range(filters)

        if sr_min is not None or sr_max is not None:
            # SR filter provided: use SR range query for candidates
            # Remove SR filters from the list since they're applied via candidate selection
            filters = [f for f in filters if f[0] not in ['sr', 'star', 'stars']]

            # Calculate final SR range bounds
            if sr_min is not None and sr_max is not None:
                # Both bounds provided: validate and use them
                filter_range = sr_max - sr_min
                if filter_range > MAX_SR_FILTER_RANGE:
                    raise ValueError(
                        f"SR filter range [{sr_min:.2f}, {sr_max:.2f}] is too large "
                        f"({filter_range:.2f} stars > {MAX_SR_FILTER_RANGE:.2f} star). "
                        f"Please use a smaller SR range (max {MAX_SR_FILTER_RANGE:.2f} star)."
                    )
                if filter_range < 0:
                    raise ValueError(
                        f"Invalid SR filter range: minimum ({sr_min:.2f}) is greater than maximum ({sr_max:.2f})."
                    )
                final_sr_min = sr_min
                final_sr_max = sr_max

            elif sr_min is not None:
                # Only min provided: calculate max using MAX_SR_FILTER_RANGE
                final_sr_min = sr_min
                final_sr_max = sr_min + MAX_SR_FILTER_RANGE

            else:  # sr_max is not None
                # Only max provided: calculate min using MAX_SR_FILTER_RANGE
                final_sr_max = sr_max
                final_sr_min = sr_max - MAX_SR_FILTER_RANGE

            # Use binary search to find candidates in SR range
            # Find left boundary: first map with overall_sr >= final_sr_min
            left_idx = bisect.bisect_left(sr_sorted_list, (final_sr_min, ''))
            # Find right boundary: last map with overall_sr <= final_sr_max
            right_idx = bisect.bisect_right(sr_sorted_list, (final_sr_max, '\uffff'))  # max unicode char

            # Extract candidate keys
            candidate_files = [key + '.dist' for _, key in sr_sorted_list[left_idx:right_idx]]
        else:
            # No SR filter: use euclidean distance
            indices = sr_tree.query_ball_point(sr[:2], r=MAX_SR_EUCLIDEAN_DISTANCE)
            candidate_files = [sr_keys_list[idx] + '.dist' for idx in indices]
    else:
        # No filters: use euclidean distance
        indices = sr_tree.query_ball_point(sr[:2], r=MAX_SR_EUCLIDEAN_DISTANCE)
        candidate_files = [sr_keys_list[idx] + '.dist' for idx in indices]

    for file in candidate_files:
        if file.startswith(str(id) + '.'):
            continue

        # Check if file exists in all_buckets
        if file not in all_buckets:
            continue

        candidate_key = file[:-5]

        # Apply filters (SR filters already removed if used for candidate selection)
        if filters:
            valid = True
            for fil in filters:
                key, operator, value, is_string, is_date = fil
                stat_value = get_stat(candidate_key, key)
                if not apply_filter(stat_value, operator, value, is_string, is_date):
                    valid = False
                    break
            if not valid:
                continue

        # Calculate similarity
        raw_sim = get_similarity(bkts, all_buckets[file])
        percentage = (raw_sim / max_similarity * 100) if max_similarity > 0 else 0

        if sr:
            # Cache euclidean distance to avoid recalculating
            euclidean_dist = euclidean(srs[candidate_key][:2], sr[:2])
            similarities.append((candidate_key, percentage, euclidean_dist))
        else:
            similarities.append((file, percentage))

    similarities.sort(key=lambda s: -s[1])
    return similarities[:min(len(similarities), n)]

def get_similar_sliders(id, text, n=50, filters=None):
    """
    Find maps with similar slider characteristics.

    Args:
        id: Map ID to find similar maps for
        text: .osu file content
        n: Number of results to return
        filters: Optional list of filters (same format as get_similar)

    Returns:
        List of (map_id, similarity_score, euclidean_dist) tuples, sorted by similarity
    """
    sldr = calc.get_sliders_raw(text)

    key = str(id)
    if key in srs:
        sr = srs[key]
    else:
        chars = '1234567890qwertyuiopasdfghjklzxcvbnm'
        temp_filename = ''.join(chars[random.randrange(len(chars))] for _ in range(10)) + '.osu'
        with open(temp_filename, 'w', encoding='utf8', newline='') as f:
            f.write(text)
        sr = getsrs.get_sr_file(temp_filename)
        os.remove(temp_filename)

    # Convert raw slider data to stats format
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

    avg_sldr = avg(sldr[0])
    std_sldr = std(sldr[0])
    source_slider_stats = (avg_sldr, std_sldr, sldr[1])

    similarities = []

    def get_stat(id, key):
        if key == 'id':
            return int(id)
        elif key in ['sr', 'star', 'stars']:
            return getsrs.get_sr(id)[0]
        elif key in ['aim', 'aimsr']:
            return getsrs.get_sr(id)[1]
        elif key in ['tap', 'tapsr']:
            return getsrs.get_sr(id)[2]
        elif key == 'bpm':
            if id in stats and 'max_bpm' in stats[id]:
                return stats[id]['max_bpm']
        elif key in ['drain', 'dr']:
            if id in stats and 'hp' in stats[id]:
                return stats[id]['hp']
        elif key == 'tags':
            if id in metadata and 'tags_lookup' in metadata[id]:
                return metadata[id]['tags_lookup']
        elif key in ['artist', 'creator', 'title', 'source']:
            if id in stats and f'{key}_lookup' in stats[id]:
                return stats[id][f'{key}_lookup']
        elif key in ['difficulty', 'diff', 'version']:
            if id in stats and 'version_lookup' in stats[id]:
                return stats[id]['version_lookup']
        elif key in ['status', 'category']:
            if id in metadata and 'approved' in metadata[id]:
                status_code = metadata[id]['approved']
                status_map = {-2: 'graveyard', -1: 'wip', 0: 'pending',
                             1: 'ranked', 2: 'approved', 3: 'qualified', 4: 'loved'}
                return status_map.get(status_code, '')
        elif key in ['created', 'submitted']:
            if id in metadata and 'submit_date' in metadata[id]:
                return metadata[id]['submit_date']
        elif key == 'ranked':
            if id in metadata and 'approved_date' in metadata[id]:
                return metadata[id]['approved_date']
        elif key == 'updated':
            if id in metadata and 'last_update' in metadata[id]:
                return metadata[id]['last_update']
        elif id in stats and key in stats[id]:
            return stats[id][key]
        return None

    # Determine candidate selection method based on SR filters
    if filters:
        sr_min, sr_max = extract_sr_range(filters)

        if sr_min is not None or sr_max is not None:
            # SR filter provided: use SR range query for candidates
            filters = [f for f in filters if f[0] not in ['sr', 'star', 'stars']]

            # Calculate final SR range bounds
            if sr_min is not None and sr_max is not None:
                filter_range = sr_max - sr_min
                if filter_range > MAX_SR_FILTER_RANGE:
                    raise ValueError(
                        f"SR filter range [{sr_min:.2f}, {sr_max:.2f}] is too large "
                        f"({filter_range:.2f} stars > {MAX_SR_FILTER_RANGE:.2f} star). "
                        f"Please use a smaller SR range (max {MAX_SR_FILTER_RANGE:.2f} star)."
                    )
                if filter_range < 0:
                    raise ValueError(
                        f"Invalid SR filter range: minimum ({sr_min:.2f}) is greater than maximum ({sr_max:.2f})."
                    )
                final_sr_min = sr_min
                final_sr_max = sr_max

            elif sr_min is not None:
                final_sr_min = sr_min
                final_sr_max = sr_min + MAX_SR_FILTER_RANGE

            else:
                final_sr_max = sr_max
                final_sr_min = sr_max - MAX_SR_FILTER_RANGE

            # Use binary search to find candidates in SR range
            left_idx = bisect.bisect_left(sr_sorted_list, (final_sr_min, ''))
            right_idx = bisect.bisect_right(sr_sorted_list, (final_sr_max, '\uffff'))

            # Extract candidate keys
            candidate_keys = [key for _, key in sr_sorted_list[left_idx:right_idx]]
        else:
            # No SR filter: use euclidean distance
            indices = sr_tree.query_ball_point(sr[:2], r=MAX_SR_EUCLIDEAN_DISTANCE)
            candidate_keys = [sr_keys_list[idx] for idx in indices]
    else:
        # No filters: use euclidean distance
        indices = sr_tree.query_ball_point(sr[:2], r=MAX_SR_EUCLIDEAN_DISTANCE)
        candidate_keys = [sr_keys_list[idx] for idx in indices]

    for candidate_key in candidate_keys:
        if candidate_key == key:
            continue

        # Check if slider data exists
        slider_file = candidate_key + '.sldr'
        if slider_file not in all_sliders:
            continue

        # Apply filters (SR filters already removed if used for candidate selection)
        if filters:
            valid = True
            for fil in filters:
                filter_key, operator, value, is_string, is_date = fil
                stat_value = get_stat(candidate_key, filter_key)
                if not apply_filter(stat_value, operator, value, is_string, is_date):
                    valid = False
                    break
            if not valid:
                continue

        # Calculate slider similarity
        sim_score = get_slider_similarity(source_slider_stats, all_sliders[slider_file])

        # Convert to percentage: 0 distance = 100%, higher distance = lower %
        # Using exponential decay: percentage = 100 * e^(-score)
        # This gives: score 0 = 100%, score 1 = 37%, score 2 = 14%, score 3 = 5%
        percentage = 100 * math.exp(-sim_score)

        if sr and candidate_key in srs:
            euclidean_dist = euclidean(srs[candidate_key][:2], sr[:2])
            similarities.append((candidate_key, percentage, euclidean_dist))
        else:
            similarities.append((candidate_key, percentage))

    # Sort by similarity (higher percentage = more similar)
    similarities.sort(key=lambda s: -s[1])
    return similarities[:min(len(similarities), n)]

def get_all_buckets(limit=None):
    """
    Load bucket files from the buckets directory.

    Args:
        limit: Optional limit on number of buckets to load (for testing)

    Returns:
        Dictionary of buckets
    """
    buckets = {}

    bkts_dir = 'buckets'

    # First, collect all bucket files to know the total count
    bucket_files = [entry for entry in os.scandir(bkts_dir) if entry.is_file()]

    # Apply limit if specified (for test mode)
    if limit is not None:
        bucket_files = bucket_files[:limit]
        print(f"TEST MODE: Loading only {len(bucket_files)} bucket files...")
    else:
        print(f"Loading {len(bucket_files)} bucket files...")

    # Process all files with progress bar
    for entry in tqdm(bucket_files, desc="Loading similarity buckets", unit="file"):
        temp_bkts = get_buckets(entry.path)
        buckets[entry.name] = temp_bkts

    return buckets

# Check if test mode is enabled (via environment variable or module attribute)
_test_mode_limit = os.environ.get('OSU_SIM_TEST_LIMIT')
_test_limit = int(_test_mode_limit) if _test_mode_limit else None
all_buckets = get_all_buckets(limit=_test_limit)
srs = getsrs.get_srs()
with open('stats.json') as fin:
    stats = json.load(fin)

# Load metadata for tags
metadata = {}
if os.path.exists('metadata.json'):
    with open('metadata.json') as fin:
        metadata = json.load(fin)

# Build spatial index on SR values for fast nearest-neighbor queries
print(f"Building SR spatial index from {len(srs)} maps...")
sr_keys_list = []
sr_values_list = []
sr_sorted_list = []  # For 1D range queries on overall_sr

for key, sr_data in srs.items():
    sr_keys_list.append(key)
    sr_values_list.append(sr_data[:2])  # [overall_sr, aim_sr]
    sr_sorted_list.append((sr_data[0], key))  # (overall_sr, key) for range queries

sr_tree = cKDTree(sr_values_list)
sr_sorted_list.sort()  # Sort by overall_sr for efficient bisect operations

print(f"SR spatial index ready with {len(sr_keys_list)} maps.")

# Load slider statistics
def get_all_sliders():
    """Load pre-computed slider statistics from sliderstats.txt."""
    sliders = {}

    if not os.path.exists('sliderstats.txt'):
        print("Warning: sliderstats.txt not found. Slider similarity will not be available.")
        return sliders

    with open('sliderstats.txt', 'r', encoding='utf8') as f:
        lines = f.readlines()

    print(f"Loading {len(lines) // 2} slider statistics...")
    for i in tqdm(range(0, len(lines), 2), desc="Loading slider stats", unit="map"):
        filename = lines[i].strip()
        ls = [float(x) for x in lines[i+1].strip().split(',')]
        # Format: ((avg_len, avg_vel), (std_len, std_vel), time_ratio)
        sliders[filename] = ((ls[0], ls[1]), (ls[2], ls[3]), ls[4])

    print(f"Loaded {len(sliders)} slider statistics ({len(lines) // 2 - len(sliders)} skipped due to invalid data).")
    return sliders

all_sliders = get_all_sliders()

if __name__ == '__main__':
    import time
    start = time.time()
    print(get_similar(2659353), time.time() - start)
