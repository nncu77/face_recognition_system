FROM python:3.10-slim

WORKDIR /app

# OpenCV / MediaPipe runtime libs
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python deps (cached layer if requirements.txt unchanged)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download buffalo_l (~280MB) into the image at build time so cold
# starts on Hugging Face Spaces / Render etc don't make the first user
# request wait 30+ seconds for InsightFace to fetch the model.
RUN mkdir -p /app/models && \
    python -c "from insightface.app import FaceAnalysis; \
fa = FaceAnalysis(name='buffalo_l', root='/app/models', providers=['CPUExecutionProvider']); \
fa.prepare(ctx_id=0, det_thresh=0.5); \
print('OK: buffalo_l cached at /app/models')"

# App + scripts + bundled demo crops (no need for ui/ Streamlit or
# web/ Next.js — backend only here)
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY data/demo_crops/ ./data/demo_crops/
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh && mkdir -p /app/data && chmod 777 /app/data

EXPOSE 8000

# entrypoint = re-seed demo users (DB is ephemeral on free tiers) +
# launch uvicorn
CMD ["./entrypoint.sh"]
