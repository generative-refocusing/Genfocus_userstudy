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

# 自定義 CSS
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
    """, unsafe_allow_html=True)

st.title("📸 Genfocus Sharpness Comparison")
st.markdown("""
### Instructions
1. Enter your **User Name** or **ID** to begin.
2. For each question, compare the **Left** and **Right** images.
3. Choose the one that looks **sharper**.
4. You must answer **all 30 questions** before clicking **Submit**.
---
""")

# --- 2. Google Sheets 連線設定 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Google Sheets connection configuration missing in Secrets.")

# --- 3. 讀取圖片 ---
IMG_DIR = "images"
if os.path.exists(IMG_DIR):
    img_files = sorted([f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
else:
    st.error(f"Directory '{IMG_DIR}' not found.")
    img_files = []

# --- 4. 問卷邏輯 ---
user_name = st.text_input("Step 1: Enter your name or ID", placeholder="e.g., Student_01")

if not user_name:
    st.info("👆 Please enter your name to display the questions.")
elif len(img_files) == 0:
    st.warning("No images found in the folder.")
else:
    # 建立一個用來存放答案的字典
    responses = {"User": user_name}
    
    # 使用 Form 容器
    with st.form("user_study_form"):
        st.subheader("Step 2: Compare and Choose")
        
        for img_name in img_files:
            q_id = img_name.split('_')[0]
            st.markdown(f"#### Question: {q_id}")
            
            img_path = os.path.join(IMG_DIR, img_name)
            st.image(img_path, use_column_width=True)
            
            choice = st.radio(
                f"Which one is sharper in {q_id}?",
                options=["Left", "Right"],
                key=f"radio_{img_name}",
                horizontal=True,
                index=None  # 強迫使用者勾選
            )
            responses[q_id] = choice
            st.divider()

        # 提交按鈕
        submitted = st.form_submit_button("Submit All Answers")

    # --- 5. 提交後的處理邏輯 ---
    if submitted:
        if None in responses.values():
            st.error("⚠️ You missed some questions. Please go back and answer all of them!")
        else:
            with st.spinner("Uploading your data to the cloud..."):
                try:
                    # [關鍵 1] 先清除快取，確保等等讀到的一定是當下最新版
                    st.cache_data.clear()
                    
                    # [關鍵 2] 讀取最新資料 (ttl=0 再次確保不快取)
                    # 這樣即使剛剛有人在你填寫時交卷了，你也會讀到他的資料，排在他後面
                    existing_data = conn.read(worksheet="Sheet1", ttl=0)
                    
                    # 處理空表的情況 (防止讀到全空的 DataFrame 報錯)
                    existing_data = existing_data.dropna(how="all")
                    
                    # [關鍵 3] 合併新資料
                    new_row = pd.DataFrame([responses])
                    updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                    
                    # [關鍵 4] 寫回 Google Sheet
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    st.success(f"🎉 Thank you, {user_name}! Your responses have been recorded.")
                    st.balloons()
                    
                    # 顯示你剛存進去的那一行讓使用者安心
                    st.write("Your submission record:")
                    st.dataframe(new_row)
                    
                except Exception as e:
                    # 錯誤處理區塊 (維持不變)
                    if "No columns to parse" in str(e):
                         st.error("Error: The Google Sheet is empty. Please add headers (User, Q01...).")
                    else:
                        st.error(f"Connection Error: {e}")
                    
                    st.warning("Could not save automatically. Please download CSV.")
                    csv_data = pd.DataFrame([responses]).to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results (CSV)",
                        data=csv_data,
                        file_name=f"result_{user_name}.csv",
                        mime="text/csv"
                    )

# --- 6. 頁尾 ---
st.markdown("---")
st.caption("Genfocus Research Group - User Study Tool")