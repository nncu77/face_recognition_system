#!/bin/sh
set -e

mkdir -p /app/data

# SQLite DB (data/embeddings.db) is ephemeral on most free tiers (HF
# Spaces non-persistent, Render free, etc). Re-seed the 6 demo users
# from t1.jpg on every boot so /api/recognize always has something to
# match against right after a container restart. Failures don't block
# uvicorn from starting.
echo "[entrypoint] seeding demo users from insightface t1.jpg..."
python scripts/seed_demo.py --reset || echo "[entrypoint] WARN seed failed — DB will be empty"

echo "[entrypoint] starting uvicorn on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
