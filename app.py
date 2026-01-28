import streamlit as st
import pandas as pd
import os
from streamlit_gsheets import GSheetsConnection

# --- 1. 網頁基本配置 ---
st.set_page_config(
    page_title="Genfocus Sharpness Study",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義 CSS 讓圖片顯示更美觀
st.markdown("""
    <style>
    .stRadio [data-testid="stMarkdownContainer"] {
        font-size: 1.2rem;
        font-weight: bold;
    }
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_stdio=True)

st.title("📸 Genfocus Sharpness Comparison")
st.markdown("""
### Instructions
1. Enter your **User Name** or **ID** to begin.
2. For each question, two images are displayed side-by-side.
3. Compare them carefully and choose which one looks **sharper** (Left or Right).
4. You must answer **all 30 questions** before clicking the **Submit** button at the bottom.
---
""")

# --- 2. Google Sheets 連線設定 ---
# 建立連線物件
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Google Sheets connection failed. Please check your Secrets configuration.")

# --- 3. 讀取圖片 ---
IMG_DIR = "images"
if os.path.exists(IMG_DIR):
    # 這裡會根據檔名排序，確保是 Q01_xx.png, Q02_xx.png ...
    img_files = sorted([f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
else:
    st.error(f"Directory '{IMG_DIR}' not found. Please upload images to the repository.")
    img_files = []

# --- 4. 問卷邏輯 ---
# 先確認使用者有填名字
user_name = st.text_input("Step 1: Enter your name or ID", placeholder="e.g., Student_01")

if not user_name:
    st.info("👆 Please enter your name to display the questions.")
elif len(img_files) == 0:
    st.warning("No images found in the folder.")
else:
    # 使用 st.form 確保不會每按一題就重新整理網頁
    with st.form("user_study_form"):
        st.subheader("Step 2: Compare and Choose")
        responses = {"User": user_name}
        
        for img_name in img_files:
            # 提取題號，例如 "Q01_19.png" -> "Q01"
            q_id = img_name.split('_')[0]
            
            st.markdown(f"#### Question: {q_id}")
            
            # 顯示圖片
            img_path = os.path.join(IMG_DIR, img_name)
            st.image(img_path, use_column_width=True, caption=f"Comparison {q_id}")
            
            # 單選按鈕
            choice = st.radio(
                f"Which one is sharper in {q_id}?",
                options=["Left", "Right"],
                key=f"radio_{img_name}",
                horizontal=True,
                index=None  # 預設不選，強迫使用者決定
            )
            responses[q_id] = choice
            st.divider()

        # 提交按鈕
        submitted = st.form_submit_button("Submit All Answers")
        
        if submitted:
            # 檢查是否有漏填
            if None in responses.values():
                st.error("⚠️ You missed some questions. Please go back and answer all of them!")
            else:
                with st.spinner("Saving your responses..."):
                    try:
                        # 1. 讀取現有資料
                        existing_data = conn.read()
                        
                        # 2. 轉換新資料為 DataFrame
                        new_row = pd.DataFrame([responses])
                        
                        # 3. 合併並寫回
                        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                        conn.update(data=updated_df)
                        
                        st.success(f"🎉 Thank you, {user_name}! Your responses have been successfully recorded.")
                        st.balloons()
                        
                        # 顯示結果供參考
                        st.dataframe(new_row)
                    except Exception as e:
                        st.error(f"An error occurred while saving: {e}")
                        # 備案：如果資料庫寫入失敗，提供下載按鈕
                        csv = pd.DataFrame([responses]).to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV manually", csv, f"result_{user_name}.csv", "text/csv")

# --- 5. 頁尾 ---
st.markdown("---")
st.caption("Genfocus Research Group - User Study Tool")