# confidence.py
def confidence_score(bias_list):
    dominant = max(set(bias_list), key=bias_list.count)
    score = int((bias_list.count(dominant) / len(bias_list)) * 100)
    return dominant, score
