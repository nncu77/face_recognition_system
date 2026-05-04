"""Streamlit UI — 5 tabs: Recognize / Register / Liveness / Users / Logs"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import get_db
from app.face_engine import get_engine
from app.liveness import LivenessDetector
from app.utils import read_image_bytes


st.set_page_config(page_title="Face Recognition System", page_icon="👤", layout="wide")
st.title("👤 Face Recognition System")
st.caption(
    f"Model: {settings.FACE_MODEL_NAME} · Threshold: {settings.RECOGNITION_THRESHOLD}"
)


@st.cache_resource
def _engine_cached():
    return get_engine()


db = get_db()
engine = _engine_cached()

tab1, tab2, tab_live, tab3, tab4 = st.tabs(
    ["🔍 辨識", "📝 註冊", "👁️ 活體驗證", "👥 用戶管理", "📜 辨識記錄"]
)


# ---- tab1: recognize ----

with tab1:
    st.header("辨識")
    src = st.radio("來源", ["相機", "上傳檔案"], horizontal=True, key="rec_src")

    if src == "相機":
        photo = st.camera_input("對著相機")
    else:
        photo = st.file_uploader("上傳照片", type=["jpg", "jpeg", "png"], key="rec_up")

    if photo is not None:
        img = read_image_bytes(photo.getvalue())
        with st.spinner("比對中..."):
            user_id, score = engine.recognize(img, db)
            db.log_recognition(user_id, score, is_live=False)

        if user_id:
            user = db.get_user(user_id)
            st.success(
                f"✅ 比對成功:**{user['name']}** (similarity = {score:.3f})"
            )
        else:
            st.warning(f"❌ 找不到匹配的人臉 (best similarity = {score:.3f})")


# ---- tab2: register ----

with tab2:
    st.header("註冊新用戶")
    name = st.text_input("姓名")
    src = st.radio("來源", ["相機", "上傳檔案"], horizontal=True, key="reg_src")

    if src == "相機":
        photo = st.camera_input("拍攝", key="reg_cam")
    else:
        photo = st.file_uploader("上傳照片", type=["jpg", "jpeg", "png"], key="reg_up")

    if photo is not None and name:
        img = read_image_bytes(photo.getvalue())
        with st.spinner("產生 embedding..."):
            emb = engine.get_embedding(img)
        if emb is None:
            st.error("未偵測到人臉，請換一張")
        else:
            uid = uuid.uuid4().hex[:12]
            db.add_user(uid, name, emb)
            st.success(f"已註冊:{name} (user_id = {uid})")


# ---- tab_live: liveness ----

with tab_live:
    st.header("活體驗證 (眨眼偵測)")
    st.caption(
        f"連拍 ≥{settings.LIVENESS_REQUIRED_BLINKS * 2 + 1} 張，期間自然眨眼 "
        f"{settings.LIVENESS_REQUIRED_BLINKS} 次以上。閾值 EAR < "
        f"{settings.LIVENESS_BLINK_THRESHOLD} 視為閉眼。"
    )

    if "live_frames" not in st.session_state:
        st.session_state.live_frames = []

    snap = st.camera_input("拍攝 (重複拍 5+ 張，過程中眨眼)", key="live_cam")

    col1, col2, col3 = st.columns(3)
    if col1.button("➕ 收這張 frame") and snap is not None:
        st.session_state.live_frames.append(snap.getvalue())
        st.rerun()
    if col2.button("🔄 重置 frames"):
        st.session_state.live_frames = []
        st.rerun()
    col3.metric("已收集 frames", len(st.session_state.live_frames))

    if st.button(
        "🔍 跑活體偵測", disabled=len(st.session_state.live_frames) == 0, type="primary"
    ):
        detector = LivenessDetector()
        frames_with_face = 0
        with st.spinner("分析中..."):
            for raw in st.session_state.live_frames:
                img = read_image_bytes(raw)
                if detector.update(img) is not None:
                    frames_with_face += 1

        is_live = detector.blink_count >= settings.LIVENESS_REQUIRED_BLINKS
        if is_live:
            st.success(
                f"✅ 活體驗證通過 (偵測到 {detector.blink_count} 次眨眼)"
            )
        else:
            st.warning(
                f"❌ 未通過 (僅 {detector.blink_count} / "
                f"{settings.LIVENESS_REQUIRED_BLINKS} 次眨眼)"
            )

        st.json(
            {
                "blink_count": detector.blink_count,
                "frames_processed": len(st.session_state.live_frames),
                "frames_with_face": frames_with_face,
                "ear_history": [round(e, 3) for e in detector.ear_history],
            }
        )
        if detector.ear_history:
            st.line_chart(list(detector.ear_history))


# ---- tab3: users ----

with tab3:
    st.header("用戶管理")
    users = db.get_all_users()
    if not users:
        st.info("尚無註冊用戶")
    else:
        for u in users:
            col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
            col1.code(u["user_id"])
            col2.write(u["name"])
            col3.caption(str(u.get("created_at", "")))
            if col4.button("🗑️", key=f"del_{u['user_id']}"):
                db.delete_user(u["user_id"])
                st.rerun()


# ---- tab4: logs ----

with tab4:
    st.header("辨識記錄")
    logs = db.get_recent_logs(50)

    if not logs:
        st.info("尚無辨識記錄")
    else:
        st.dataframe(logs, use_container_width=True)
