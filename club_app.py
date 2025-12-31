import streamlit as st
import pandas as pd
import os
from datetime import date

# --- 設定頁面配置 ---
st.set_page_config(page_title="東華熱舞罰錢系統", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F5F5F0; }
    .stButton>button { background-color: #7B8D8E; color: white; border-radius: 10px; border: none; }
    h1, h2, h3 { color: #4F5D5E; }
    div[data-testid="stMetric"] { background-color: #E2E6E6; padding: 10px; border-radius: 10px; color: #4A4A4A; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; }
    /* 刪除按鈕特別色 */
    .delete-btn > button { background-color: #d9534f !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 檔案名稱設定 ---
MEMBER_FILE = 'club_members.csv'    # 成員名單
HISTORY_FILE = 'club_history.csv'   # 詳細歷史紀錄
EVENT_FILE = 'config_events.csv'    # 活動類型設定
RULE_FILE = 'config_rules.csv'      # 罰款規則設定

# --- 資料讀取與儲存函數 ---
def load_csv(filename, default_data):
    if not os.path.exists(filename):
        df = pd.DataFrame(default_data)
        df.to_csv(filename, index=False)
        return df
    return pd.read_csv(filename)

def save_csv(df, filename):
    df.to_csv(filename, index=False)

# --- 主程式 ---
def main():
    st.title("💃 東華熱舞罰錢系統")
    
    # 載入資料
    df_members = load_csv(MEMBER_FILE, {"姓名": [], "總罰金": []})
    df_history = load_csv(HISTORY_FILE, {"日期": [], "姓名": [], "活動": [], "違規事項": [], "金額": []})
    df_events = load_csv(EVENT_FILE, {"活動名稱": ["例會", "社課", "宣傳", "拉贊", "成發"]})
    df_rules = load_csv(RULE_FILE, {"違規事項": ["遲到", "未到", "沒帶器材", "沒穿社服"], "金額": [50, 100, 30, 50]})

    # 側邊欄
    role = st.sidebar.radio("請選擇身份", ["一般成員 (查詢)", "管理員 (後台)"])

    # --- 1. 一般成員查詢介面 ---
    if role == "一般成員 (查詢)":
        st.subheader("查詢我的紀錄")
        all_names = df_members["姓名"].unique().tolist()
        
        if not all_names:
            st.info("目前沒有成員資料。")
        else:
            selected_name = st.selectbox("請選擇你的名字", all_names)
            if st.button("查詢"):
                member_info = df_members[df_members["姓名"] == selected_name].iloc[0] if not df_members[df_members["姓名"] == selected_name].empty else None
                if member_info is not None:
                    col1, col2 = st.columns([1, 2])
                    col1.metric("目前應繳總罰金", f"${member_info['總罰金']}")
                    
                    with col2:
                        st.write("📋 **詳細違規紀錄：**")
                        personal_history = df_history[df_history["姓名"] == selected_name]
                        if not personal_history.empty:
                            display_df = personal_history.copy()
                            display_df['內容'] = display_df['日期'] + " [" + display_df['活動'] + "] " + display_df['違規事項']
                            st.table(display_df[['內容', '金額']])
                        else:
                            st.success("目前沒有任何紀錄！")

    # --- 2. 管理員後台介面 ---
    elif role == "管理員 (後台)":
        password = st.sidebar.text_input("輸入管理員密碼", type="password")
        if password == "1234":
            st.success("登入成功")
            
            # 這裡新增了「刪除紀錄」的分頁
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 登記紀錄", "🗑️ 刪除紀錄", "⚙️ 規則設定", "➕ 成員管理", "🏆 排行榜"])
            
            # --- Tab 1: 登記 ---
            with tab1:
                st.write("### 新增一筆紀錄")
                if df_members.empty:
                    st.warning("請先去「成員管理」新增成員")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        rec_date = st.date_input("日期", date.today())
                        rec_member = st.selectbox("成員", df_members["姓名"])
                        rec_event = st.selectbox("活動類型", df_events["活動名稱"])
                    
                    with col2:
                        rule_choice = st.selectbox("違規/罰款事項", df_rules["違規事項"])
                        default_amount = int(df_rules[df_rules["違規事項"] == rule_choice]["金額"].values[0]) if not df_rules[df_rules["違規事項"] == rule_choice].empty else 0
                        rec_amount = st.number_input("罰金金額", value=default_amount)

                    if st.button("送出登記", type="primary"):
                        # 寫入歷史
                        new_record = pd.DataFrame({
                            "日期": [str(rec_date)],
                            "姓名": [rec_member],
                            "活動": [rec_event],
                            "違規事項": [rule_choice],
                            "金額": [rec_amount]
                        })
                        df_history = pd.concat([df_history, new_record], ignore_index=True)
                        save_csv(df_history, HISTORY_FILE)

                        # 更新總金額
                        idx = df_members[df_members["姓名"] == rec_member].index[0]
                        df_members.at[idx, "總罰金"] += rec_amount
                        save_csv(df_members, MEMBER_FILE)
                        
                        st.toast(f"已登記：{rec_member} ${rec_amount}")
                        st.rerun()

            # --- Tab 2: 刪除紀錄 (新功能) ---
            with tab2:
                st.write("### 🗑️ 撤銷/刪除紀錄")
                st.info("注意：刪除紀錄後，該成員的「總罰金」會自動扣除對應金額。")
                
                del_member = st.selectbox("請選擇要刪除紀錄的成員", df_members["姓名"].unique(), key="del_member")
                
                # 篩選出該成員的歷史紀錄
                member_history = df_history[df_history['姓名'] == del_member]
                
                if member_history.empty:
                    st.warning("該成員目前沒有任何紀錄。")
                else:
                    # 製作一個讓人類好讀的選項清單 (包含原本的 Index 才能準確刪除)
                    # 格式: [ID: 5] 2023-12-31 (例會) 遲到 - $50
                    options = {
                        f"[ID:{i}] {row['日期']} ({row['活動']}) {row['違規事項']} - ${row['金額']}": i 
                        for i, row in member_history.iterrows()
                    }
                    
                    selected_option = st.selectbox("選擇要刪除哪一筆？", list(options.keys()))
                    target_index = options[selected_option]
                    
                    # 再次確認按鈕
                    col_d1, col_d2 = st.columns([1,3])
                    if col_d1.button("確認刪除", type="secondary"):
                        # 1. 先抓出要扣回多少錢
                        refund_amount = df_history.loc[target_index, '金額']
                        
                        # 2. 刪除該筆歷史
                        df_history = df_history.drop(target_index)
                        save_csv(df_history, HISTORY_FILE)
                        
                        # 3. 從總金額中扣除
                        mem_idx = df_members[df_members["姓名"] == del_member].index[0]
                        df_members.at[mem_idx, "總罰金"] -= refund_amount
                        save_csv(df_members, MEMBER_FILE)
                        
                        st.success(f"已刪除紀錄，並從總額扣除 ${refund_amount}")
                        st.rerun()

            # --- Tab 3: 規則設定 ---
            with tab3:
                c1, c2 = st.columns(2)
                with c1:
                    st.write("活動類型設定")
                    edited_events = st.data_editor(df_events, num_rows="dynamic", key="event_editor")
                    if st.button("儲存活動"):
                        save_csv(edited_events, EVENT_FILE)
                        st.rerun()
                with c2:
                    st.write("罰款規則設定")
                    edited_rules = st.data_editor(df_rules, num_rows="dynamic", key="rule_editor")
                    if st.button("儲存規則"):
                        save_csv(edited_rules, RULE_FILE)
                        st.rerun()

            # --- Tab 4: 成員管理 ---
            with tab4:
                new_name = st.text_input("輸入新成員")
                if st.button("新增"):
                    if new_name and new_name not in df_members["姓名"].values:
                        new_row = pd.DataFrame({"姓名": [new_name], "總罰金": [0]})
                        df_members = pd.concat([df_members, new_row], ignore_index=True)
                        save_csv(df_members, MEMBER_FILE)
                        st.success(f"已新增 {new_name}")
                        st.rerun()
                    else:
                        st.error("成員已存在")

            # --- Tab 5: 排行榜 ---
            with tab5:
                st.write("### 🏆 東華熱舞罰金榜")
                st.dataframe(
                    df_members.sort_values(by="總罰金", ascending=False),
                    use_container_width=True,
                    column_config={"總罰金": st.column_config.ProgressColumn("累積金額", format="$%d", min_value=0, max_value=int(df_members["總罰金"].max()) if not df_members.empty else 100)}
                )
                with st.expander("查看所有詳細流水帳"):
                    st.dataframe(df_history.sort_values(by="日期", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()