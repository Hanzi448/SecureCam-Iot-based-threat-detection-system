# services/face_utils.py
import numpy as np
from extensions import db
from models.watchlist import Watchlist

def save_watchlist_entry(name, image_url, embedding: np.ndarray):
    """Save new watchlist entry."""
    emb_bytes = embedding.astype(np.float32).tobytes()
    norm = float(np.linalg.norm(embedding))
    entry = Watchlist(
        name=name,
        image_url=image_url,
        embedding=emb_bytes,
        embedding_norm=norm
    )
    db.session.add(entry)
    db.session.commit()
    print(f"[DB] Added to watchlist: {name} (id={entry.id})")
    return entry.id


def load_all_watchlist_embeddings():
    """Return all embeddings as (ids, names, embeddings ndarray)."""
    rows = Watchlist.query.all()
    ids, names, embs = [], [], []
    for row in rows:
        if not row.embedding:
            continue
        vec = np.frombuffer(row.embedding, dtype=np.float32)
        vec = vec / np.linalg.norm(vec)
        ids.append(row.id)
        names.append(row.name)
        embs.append(vec)
    if not embs:
        return [], [], np.empty((0, 512))
    return ids, names, np.vstack(embs)
