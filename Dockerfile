FROM python:3.10-slim

WORKDIR /app

# 系統依賴 (OpenCV / MediaPipe runtime libs)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8501

# 啟動 FastAPI (改成 streamlit run ui/streamlit_app.py 可啟動 UI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
