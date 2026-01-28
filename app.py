import streamlit as st
import pandas as pd
import os

# --- 網頁標題與設定 ---
st.set_page_config(page_title="Genfocus Sharpness Study", layout="wide")

st.title("📸 Genfocus Sharpness Comparison")
st.markdown("""
### Instructions
1. Enter your **User Name**.
2. For each question, compare the **Left** and **Right** images.
3. Choose the one that you perceive as **sharper**.
4. Click **Submit** at the bottom when you are finished.
---
""")

# --- 1. 使用者名稱 ---
user_name = st.text_input("Step 1: Enter your name or ID", placeholder="e.g., Guest_01")

# --- 2. 載入圖片列表 ---
IMG_DIR = "images"
if os.path.exists(IMG_DIR):
    # 確保排序正確 Q01, Q02...
    img_files = sorted([f for f in os.listdir(IMG_DIR) if f.endswith(('.png', '.jpg'))])
else:
    st.error("Cannot find the 'images' folder. Please check your file structure.")
    img_files = []

# --- 3. 問卷主體 ---
if user_name and img_files:
    # 使用 Form 確保按下 Submit 才一次性上傳
    with st.form("study_form"):
        responses = {"User": user_name}
        
        # 逐題顯示
        for img_name in img_files:
            # 取得題號 Q01, Q02...
            q_id = img_name.split('_')[0]
            
            st.write(f"#### Question: {q_id}")
            st.image(os.path.join(IMG_DIR, img_name), use_column_width=True)
            
            choice = st.radio(
                f"Which image is sharper in {q_id}?",
                ["Left", "Right"],
                key=img_name,
                horizontal=True,
                index=None # 預設不勾選，強迫使用者選擇
            )
            responses[q_id] = choice
            st.markdown("---")

        # 提交按鈕
        submitted = st.form_submit_button("Submit All Answers")
        
        if submitted:
            if None in responses.values():
                st.error("Please answer all questions before submitting!")
            else:
                st.success(f"Thank you, {user_name}! Your responses have been recorded.")
                # 這裡目前是顯示結果，稍後我們會加上存檔邏輯
                st.dataframe(pd.DataFrame([responses]))
                st.balloons()
else:
    st.info("Please enter your name to start the survey.")