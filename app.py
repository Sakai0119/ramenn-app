import re
from openai import OpenAI
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="習志野・船橋 ラーメン特化分析アプリ", page_icon="🍜", layout="centered"
)

st.title("🍜 習志野・船橋 ラーメン網羅分析＆マッピング")
st.write("習志野市と船橋市のラーメン店を完全網羅し、口コミから算出した「おいしさ熱量スコア」と「具体的な金額」で地域特性を比較します。")

# ==================================================
# 🔑 OpenAI クライアントの初期化
# ==================================================
client = None
if "openai" in st.secrets and "api_key" in st.secrets["openai"]:
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
else:
    st.warning("⚠️ OpenAIのAPIキーが設定されていません。StreamlitのSecretsに設定してください。")


@st.cache_data
def load_data():
    for filename in ["ramen_database_kanto.csv", "ramen_database_massive.csv", "ramen_database_100.csv"]:
        try:
            return pd.read_csv(filename)
        except FileNotFoundError:
            continue
    return None


df = load_data()

if df is None:
    st.error("⚠️ CSVファイルが見つかりません。GitHubにデータCSVをアップロードしてください。")
else:
    # ==================================================
    # 🧪 データの前処理・スコア化
    # ==================================================
    positive_words = ["美味しい", "おいしい", "旨い", "うまい", "絶品", "味がいい", "スープが優秀", "麺がうまい", "激ウマ", "美味すぎる", "最高", "リピート"]

    def calculate_delicious_score(text):
        if pd.isna(text) or len(str(text)) == 0:
            return 0.0
        text_str = str(text)
        count = 0
        for word in positive_words:
            count += text_str.count(word)
        raw_score = (count / len(text_str)) * 500
        adjusted_score = min(100.0, max(30.0, 30.0 + raw_score * 10))
        return round(adjusted_score, 1)

    @st.cache_data(show_spinner=False)
    def generate_gpt_summary(shop_name, text, kw_list):
        if client is None:
            return "（APIキーが設定されていないため要約をスキップしました）"
        if pd.isna(text) or len(str(text).strip()) == 0:
            return "口コミデータがありません。"
        
        keywords_str = "、".join(kw_list)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは優秀なグルメレビュアーです。提供されたラーメン店の口コミ群から、そのお店の味、特徴、雰囲気を客観的に分析し、300文字程度（最大320文字）の綺麗な日本語の要約文を作成してください。"},
                    {"role": "user", "content": f"店舗名: {shop_name}\n特に注目してほしい検索キーワード: {keywords_str}\n\n口コミデータ:\n{str(text)[:2000]}"}
                ],
                max_tokens=400,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ 要約生成エラー: {e}"

    df["おいしさスコア"] = df["すべての口コミ"].apply(calculate_delicious_score)
    
    def detect_city(address):
        address_str = str(address)
        if "習志野" in address_str:
            return "習志野市"
        elif "船橋" in address_str:
            return "船橋市"
        else:
            return "その他エリア"

    df["所属市区町村"] = df["住所"].apply(detect_city)
    target_df = df[df["所属市区町村"].isin(["習志野市", "船橋市"])].copy()

    # ==================================================
    # 🗺️ グラフ表示
