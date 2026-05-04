"""Streamlit UI — 4 tabs: Recognize / Register / Users / Logs"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import get_db
from app.face_engine import get_engine
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

tab1, tab2, tab3, tab4 = st.tabs(["🔍 辨識", "📝 註冊", "👥 用戶管理", "📜 辨識記錄"])


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
            import uuid
            uid = uuid.uuid4().hex[:12]
            db.add_user(uid, name, emb)
            st.success(f"已註冊:{name} (user_id = {uid})")


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
