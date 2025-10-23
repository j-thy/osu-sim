import json
import math
import numpy as np
import os
import random
from tqdm import tqdm

import calc
from filters import apply_filter
import getmaps
import getbuckets
import getsrs

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

def get_similar(id, n=50, filters=None):
    text = getmaps.get_map(id)
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

    for file in all_buckets:
        if file.startswith(str(id)):
            continue

        if filters:
            valid = True
            for fil in filters:
                key, operator, value, is_string, is_date = fil
                stat_value = get_stat(file[:-5], key)
                if not apply_filter(stat_value, operator, value, is_string, is_date):
                    valid = False
                    break
            if not valid:
                continue

        if not sr:
            raw_sim = get_similarity(bkts, all_buckets[file])
            # Normalize to percentage (0-100%)
            percentage = (raw_sim / max_similarity * 100) if max_similarity > 0 else 0
            similarities.append((file, percentage))
        else:
            key = file[:-5]
            if key not in srs:
                continue

            if euclidean(srs[key][:2], sr[:2]) <= 0.5:
                raw_sim = get_similarity(bkts, all_buckets[file])
                # Normalize to percentage (0-100%)
                percentage = (raw_sim / max_similarity * 100) if max_similarity > 0 else 0
                similarities.append((key, percentage, euclidean(srs[key][:2], sr[:2])))

    similarities.sort(key=lambda s: -s[1])
    return similarities[:min(len(similarities), n)]

def get_all_buckets():
    buckets = {}

    bkts_dir = 'buckets'

    # First, collect all bucket files to know the total count
    bucket_files = [entry for entry in os.scandir(bkts_dir) if entry.is_file()]

    print(f"Loading {len(bucket_files)} bucket files...")

    # Process all files with progress bar
    for entry in tqdm(bucket_files, desc="Loading similarity buckets", unit="file"):
        temp_bkts = get_buckets(entry.path)
        buckets[entry.name] = temp_bkts

    return buckets

all_buckets = get_all_buckets()
srs = getsrs.get_srs()
with open('stats.json') as fin:
    stats = json.load(fin)

# Load metadata for tags
metadata = {}
if os.path.exists('metadata.json'):
    with open('metadata.json') as fin:
        metadata = json.load(fin)

if __name__ == '__main__':
    import time
    start = time.time()
    print(get_similar(2659353), time.time() - start)
