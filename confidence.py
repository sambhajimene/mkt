# confidence.py
from collections import Counter

def confidence_score(bias_list):
    if not bias_list:
        return 0
    count = Counter(bias_list)
    bias, hits = count.most_common(1)[0]
    score = int((hits / len(bias_list)) * 100)
    return score
