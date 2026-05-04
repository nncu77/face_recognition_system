# 🎯 Face Recognition System | 商用級人臉辨識系統

> 基於 InsightFace + FastAPI 的端到端人臉辨識解決方案,支援活體偵測,可商用授權。

## ✨ 功能特色

- 🔍 **高準確率人臉辨識** — ArcFace (InsightFace buffalo_l)，LFW paper 99.8%
- 👁️ **活體偵測** — 透過眨眼 (EAR) 防止照片攻擊
- 🚀 **即時推論** — 單張影像 < 50ms (GPU)
- 🌐 **RESTful API** — FastAPI 後端,易於整合
- 🎨 **網頁介面** — Streamlit 直覺操作
- 📦 **Docker 化** — 一鍵部署
- ✅ **商用授權** — 框架皆可商用 (見下方 License 注意)

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
| 前端 | Streamlit |
| 資料庫 | SQLite |
| 部署 | Docker |

## 🚀 快速開始

```powershell
# 1. 建立虛擬環境
python -m venv venv
venv\Scripts\activate

# 2. 安裝套件
pip install -r requirements.txt

# 3. 啟動 API
uvicorn app.main:app --reload

# 4. 啟動 UI (另開終端)
streamlit run ui/streamlit_app.py
```

> 第一次跑 `recognize` 或 `register` 時 InsightFace 會下載 buffalo_l 模型 (~280MB) 到 `models/`,需要網路。

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

## ⚠️ License 注意

- **InsightFace 框架本身**:MIT
- **buffalo_l 模型權重**:以 InsightFace model_zoo 公佈為準。部分 ArcFace 變體用 Glint360K / MS1M-V2 等資料集,商用前請 confirm 上游 dataset license
- **MediaPipe**:Apache 2.0 ✅
- **本專案程式碼**:MIT
