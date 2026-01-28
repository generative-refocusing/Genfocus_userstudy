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

    # --- 5. 提交後的處理邏輯 (在 Form 外面，解決 download_button 報錯) ---
    if submitted:
        if None in responses.values():
            st.error("⚠️ You missed some questions. Please go back and answer all of them!")
        else:
            with st.spinner("Saving your responses to Google Sheets..."):
                try:
                    # 讀取現有資料
                    existing_data = conn.read()
                    new_row = pd.DataFrame([responses])
                    
                    # 合併並上傳
                    updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    
                    st.success(f"🎉 Thank you, {user_name}! Your responses have been recorded.")
                    st.balloons()
                    st.dataframe(new_row)
                    
                except Exception as e:
                    # 錯誤處理
                    if "No columns to parse" in str(e):
                        st.error("Error: The Google Sheet is empty. Please add column headers (User, Q01, Q02...) to the first row.")
                    else:
                        st.error(f"Connection Error: {e}")
                    
                    # 備案：手動下載
                    st.warning("Could not save to Google Sheets. Please download your results and send them to the researcher manually.")
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