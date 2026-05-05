---
title: Face Recognition System
emoji: 👤
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
license: mit
short_description: InsightFace + FastAPI 端到端人臉辨識（後端），前端在 Vercel
---

# 🎯 Face Recognition System | 端到端人臉辨識系統

> 基於 InsightFace + FastAPI 的人臉註冊 / 辨識 / 活體偵測 RESTful 服務 + Next.js 前端。

## 🚀 Live Demo

[![Frontend](https://img.shields.io/badge/Frontend-web--six--zeta--85.vercel.app-black?logo=vercel)](https://web-six-zeta-85.vercel.app)
[![Backend API](https://img.shields.io/badge/API-lilann--face--recognition--system.hf.space-yellow?logo=huggingface)](https://lilann-face-recognition-system.hf.space)
[![API Docs](https://img.shields.io/badge/Docs-OpenAPI%2FSwagger-blue)](https://lilann-face-recognition-system.hf.space/docs)

| 試這個 | 連結 |
|---|---|
| 🌐 **網頁前端**（Vercel） | <https://web-six-zeta-85.vercel.app> |
| 🔌 **後端 API**（HF Spaces Docker） | <https://lilann-face-recognition-system.hf.space> |
| 📚 **互動式 API 文件** | <https://lilann-face-recognition-system.hf.space/docs> |

> ⏰ 後端閒置會 sleep（HF Spaces 免費 tier）。第一次按可能要等 ~30 秒讓 280MB ArcFace 模型載入；之後 ~800ms / inference。

## ✨ 功能特色

- 🔍 **高準確率人臉辨識** — ArcFace (InsightFace buffalo_l)，LFW paper 99.83%
- 👁️ **活體偵測** — 透過眨眼 (EAR) 防止照片攻擊
- 🚀 **即時推論** — 145ms (GTX 1650 Ti GPU) / 790ms (i7 CPU) ／ 6 張臉同時偵測
- 🌐 **RESTful API** — FastAPI 後端 + OpenAPI docs，易於整合
- 🎨 **網頁介面** — Streamlit 5 tabs (辨識 / 註冊 / 活體 / 用戶 / 記錄)
- 📦 **Docker 化** — Dockerfile 已就位
- ⚠️ **License**：**框架程式碼 MIT 可商用**；**buffalo_l 預訓練權重 non-commercial research only**（要商用要換資料集 retrain 或向 InsightFace 商授權，詳見下方）

## 🏗️ 系統架構

```
[Camera/Image] → [Face Detection] → [Liveness Check]
                                          ↓
[Database] ← [Face Matching] ← [Feature Extraction]
```

## 🛠️ 技術棧

| 模組 | 技術 |
|------|------|
| 人臉偵測/特徵 | InsightFace (buffalo_l) |
| 活體偵測 | MediaPipe FaceMesh |
| 後端 | FastAPI + Uvicorn |
| 前端 (主) | **Next.js 14 + TypeScript + Tailwind** (`web/`) |
| 前端 (Dev tool) | Streamlit (`ui/`，快速 demo 用) |
| 資料庫 | SQLite |
| 部署 | Docker |

## 🚀 快速開始

```powershell
# 1. 建立 Python 虛擬環境
python -m venv venv
venv\Scripts\activate

# 2. 安裝後端套件
pip install -r requirements.txt

# 3. 啟動 FastAPI (port 8000)
uvicorn app.main:app --reload
```

### 開 Next.js 前端 (推薦)

```powershell
# 另開終端
cd web
npm install
npm run dev    # http://localhost:3000
```

CORS 已在 FastAPI 開好，前端 dev 模式直接呼叫 `http://localhost:8000`。
要改後端位置：`web/.env.local` 寫 `NEXT_PUBLIC_API_URL=https://your-api.example.com`。

### 或開 Streamlit 介面（內部 demo）

```powershell
# 另開終端
streamlit run ui/streamlit_app.py
```

> 第一次跑 `recognize` 或 `register` 時 InsightFace 會下載 buffalo_l 模型 (~280MB) 到 `models/`,需要網路。

## 🎬 一鍵 Demo（不用相機）

repo 內建 6 張不同人臉的 demo crops（從 `insightface/data/images/t1.jpg` 截出），seed 一次就能立刻測辨識：

```powershell
# 1. seed: 從 t1.jpg 偵測 6 張臉註冊成 Person 1..6
python scripts/seed_demo.py --reset

# 2. 啟 API
uvicorn app.main:app --reload

# 3. (另開終端) 對任一張 crop 跑 recognize
curl -X POST http://localhost:8000/api/recognize -F "image=@data/demo_crops/person3.jpg"
# → {"matched": true, "name": "Person 3", "similarity": 0.986, "bbox": [...], "det_score": 0.92}
```

實測 6/6 全對，similarity 都 > 0.98。`--gpu` 旗標可開啟 GPU 加速。

## 🚀 GPU 加速（可選）

預設 `USE_GPU=False` 跑 CPU。要啟用 GPU：

1. **裝 CUDA Toolkit + cuDNN**（onnxruntime-gpu 不內建）
   - CUDA 11.7 → cuDNN 8.5+
   - 從 NVIDIA 開發者帳號下載 cuDNN
2. **換 onnxruntime-gpu**
   ```powershell
   pip uninstall onnxruntime
   pip install onnxruntime-gpu==1.15.1   # CUDA 11.7
   # or onnxruntime-gpu==1.17.0           # CUDA 11.8
   ```
3. **開 USE_GPU**：寫進 `.env` 或設 env `USE_GPU=true`

CUDA DLL 找不到時會自動 fallback CPU，不會 crash。
看 log 第 2 行 `(active providers: ...)` 確認實際跑哪個。

## 📡 API

| Method | Path | 說明 |
|---|---|---|
| GET | `/` | 服務健康檢查 |
| POST | `/api/register` | multipart: `name` + `image` |
| POST | `/api/recognize` | multipart: `image` (+ optional `is_live`) |
| POST | `/api/liveness` | multipart: `frames` (≥5 張連拍) → blink 偵測 |
| GET | `/api/users` | 列出全部用戶 |
| DELETE | `/api/users/{user_id}` | 刪除用戶 |
| GET | `/api/logs?limit=50` | 最近辨識記錄 |

互動式 docs: http://localhost:8000/docs

## 🧪 測試

```powershell
pytest tests/ -v
```

Smoke tests 不需要 InsightFace model，純驗證 DB / utils / EAR 算式。

## 📊 效能數據

實測環境：i7 + 32GB RAM + NVIDIA GeForce GTX 1650 Ti / 4GB VRAM (Turing, 1024 CUDA cores) + CUDA 11.7 + cuDNN 8.9.7 + onnxruntime-gpu 1.15.1

測試圖：`insightface/data/images/t1.jpg` (1280×886, 6 faces)

| 模式 | 純推論 (Python timing) | API 端到端 (curl POST /api/recognize) |
|---|---|---|
| **CPU** | 790ms | 817ms median (5 runs: 798-887ms) |
| **GPU** | 145ms | 165ms median (10 runs: 161-184ms) |
| **加速** | **5.4×** | **4.95×** |

GPU 首次 cold inference 約 5.3 秒（cuDNN EXHAUSTIVE conv algo search 找最快 kernel，之後 cache）。Init 時間 GPU 約 2.7s vs CPU 1.1s。

辨識準確率（待量測 — paper 報告 buffalo_l 在 LFW 99.83%、ArcFace + ResNet50 backbone）。

支援人臉數：10,000+ 即時比對（cosine 線性掃 O(N)，512-dim embedding）。

## ⚠️ License 重要說明

| 元件 | License | 商用可行 |
|---|---|---|
| 本專案程式碼 | MIT | ✅ 可商用 |
| InsightFace **框架程式碼** | MIT | ✅ 可商用 |
| **InsightFace `buffalo_l` 預訓練權重** | **Non-commercial research only** | ❌ **不可商用** |
| 訓練資料集 (WebFace600K) | Research only | ❌ |
| MediaPipe (FaceMesh, 活體偵測用) | Apache 2.0 | ✅ |
| ONNX Runtime | MIT | ✅ |
| FastAPI / Streamlit / SQLAlchemy / Pydantic | 各自開源寬鬆 license | ✅ |

InsightFace model_zoo 明確標示：「**ALL models are available for non-commercial research purposes only.**」（[來源](https://github.com/deepinsight/insightface/tree/master/model_zoo)）

### 要走商用，三條路：

1. **跟 InsightFace 團隊商業授權**：他們有付費的 commercial-grade 權重 (contact@insightface.ai)
2. **用 commercial-OK 資料集自訓**：例如 [VGGFace2](https://www.robots.ox.ac.uk/~vgg/data/vgg_face2/)（學術 + 部分商用）或自建資料集
3. **換成商用 OK 的開源模型**：例如 [DeepFace](https://github.com/serengil/deepface) 內建的 ArcFace 部分權重，或 [face_recognition (dlib)](https://github.com/ageitgey/face_recognition)（dlib license MIT-like，但精度略低）
