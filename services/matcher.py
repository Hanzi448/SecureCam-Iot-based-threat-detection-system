# services/matcher.py
import numpy as np

def find_best_match(embedding, db_embeddings, ids, names, threshold=0.40):
    """
    Compare an embedding with all DB embeddings.
    Returns (matched, best_id, best_name, distance)
    """
    if db_embeddings.shape[0] == 0:
        return False, None, None, None

    emb = embedding / np.linalg.norm(embedding)
    dists = 1 - np.dot(db_embeddings, emb)  # cosine distance
    best_idx = np.argmin(dists)
    best_dist = dists[best_idx]
    matched = best_dist < threshold
    return matched, ids[best_idx], names[best_idx], float(best_dist)
