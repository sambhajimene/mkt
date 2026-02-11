# confidence.py
from collections import Counter

def confidence_score(bias_list):
    # At least 3 strikes must agree
    if len(bias_list) < 3:
        return 0

    count = Counter(bias_list)
    bias, hits = count.most_common(1)[0]

    return int((hits / len(bias_list)) * 100)
