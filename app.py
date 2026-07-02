import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="千葉県 学生街ラーメン特性分析アプリ", page_icon="🍜", layout="centered"
)

st.title("🍜 千葉県 学生街ラーメン網羅分析ダッシュボード")
st.write("千葉県内の大学・専門学校・短期大学の周辺500m圏内にあるラーメン専門店を対象に、AIが分析した統計データを可視化します。")

# ==================================================
# 📊 学生街分析セクション
# ==================================================
st.header("📊 学生街ラーメンの3要素割合分析")
st.write("各学校周辺の店舗の『一番人気メニュー』から抽出した、味の濃さ・スープの種類・麺の太さのデータです。")

try:
    # 収集した学生街ラーメンのCSVを読み込み
    univ_df = pd.read_csv("chiba_univ_ramen.csv")
    total_univ_shops = len(univ_df)
    
    st.info(f"🎓 対象の学校周辺でヒットした合計ラーメン専門店数: **{total_univ_shops} 店舗**")

    if total_univ_shops > 0:
        # 画面を3列に分割して円グラフを横並びにする
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("💧 味の濃さ")
            density_counts = univ_df["味の濃さ"].value_counts().reset_index()
            density_counts.columns = ["味の濃さ", "店舗数"]
            fig1 = px.pie(density_counts, values="店舗数", names="味の濃さ", hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("🍜 スープの種類")
            type_counts = univ_df["種類"].value_counts().reset_index()
            type_counts.columns = ["種類", "店舗数"]
            fig2 = px.pie(type_counts, values="店舗数", names="種類", hole=0.3, color_discrete_sequence=px.colors.sequential.Agsunset)
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            st.subheader("🥢 麺の太さ")
            thickness_counts = univ_df["麺の太さ"].value_counts().reset_index()
            thickness_counts.columns = ["麺の太さ", "店舗数"]
            fig3 = px.pie(thickness_counts, values="店舗数", names="麺の太さ", hole=0.3, color_discrete_sequence=px.colors.sequential.YlOrBr)
            st.plotly_chart(fig3, use_container_width=True)

        # 💡 論文や発表スライドにコピペしやすいよう、データの一覧表も下部に表示します
        st.markdown("---")
        st.header("📋 対象店舗データ一覧")
        st.write("分析対象となった店舗の具体的な一覧です（最寄り学校別）。")
        
        # 実際の口コミは長すぎて表が見づらくなるため、除外して表示
        display_df = univ_df[["最寄り学校", "店名", "住所", "一番人気", "味の濃さ", "種類", "麺の太さ"]]
        st.dataframe(display_df, use_container_width=True)

    else:
        st.warning("⚠️ 'chiba_univ_ramen.csv' 内に有効な店舗データが含まれていません。データ収集スクリプトを再実行してください。")
            
except FileNotFoundError:
    st.warning("⚠️ 'chiba_univ_ramen.csv' が見つかりません。自動収集スクリプトを実行してCSVデータをリポジトリにアップロードしてください。")
