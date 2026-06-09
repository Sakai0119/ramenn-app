import pandas as pd
import streamlit as st

# 1. ページの基本設定
st.set_page_config(
    page_title="自分専用ラーメン食べログ", page_icon="🍜", layout="centered"
)

st.title("🍜 自分専用 ラーメン食べログ")
st.write(
    "Googleマップの口コミをAIが300文字に要約した、特製ラーメンデータベースです。"
)


# 2. データの読み込み
@st.cache_data
def load_data():
    try:
        return pd.read_csv("ramen_database_100.csv")
    except FileNotFoundError:
        return None


df = load_data()

if df is None:
    st.error(
        "⚠️ 'ramen_database_100.csv' が見つかりません。アプリと同じフォルダにCSVファイルを置いてください。"
    )
else:
    # 3. 検索窓の設置
    keyword_input = st.text_input(
        "キーワードで探す（スペースで区切ると複数条件で絞り込めます。例：新宿 濃厚）",
        "",
    )

    # 4. 検索処理と結果の表示
    if keyword_input:
        # 全角スペースや読点（、,）をすべて半角スペースに統一して、キーワードをリストに分解する
        keywords = (
            keyword_input.replace(" ", " ")
            .replace("、", " ")
            .replace(",", " ")
            .split()
        )

        # 最初のデータ全件をベースにする
        filtered_df = df.copy()

        # 入力されたすべてのキーワードで順番に絞り込む（AND検索）
        for kw in keywords:
            filtered_df = filtered_df[
                filtered_df["店名"].str.contains(kw, na=False)
                | filtered_df["検索エリア"].str.contains(kw, na=False)
                | filtered_df["300文字要約"].str.contains(kw, na=False)
            ]

        # 表示用のキーワード文字列
        display_keywords = " ＋ ".join(keywords)
        st.subheader(
            f"🔍 「{display_keywords}」の検索結果 （{len(filtered_df)}件ヒット）"
        )
        st.markdown("---")

        if len(filtered_df) == 0:
            st.warning("一致するラーメン店が見つかりませんでした。")
        else:
            for index, row in filtered_df.iterrows():
                with st.container():
                    st.markdown(f"### {row['店名']}")
                    st.caption(
                        f"📍 エリア: {row['検索エリア']}  |  🗺️ 住所: {row['住所']}"
                    )
                    st.markdown(
                        f"**【AIによる口コミ要約】**\n\n{row['300文字要約']}"
                    )
                    st.markdown("---")
    else:
        st.info(
            "上の検索窓にキーワードを入力すると、お店の情報を絞り込めます。"
        )
