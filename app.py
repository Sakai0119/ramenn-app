import pandas as pd
import streamlit as st

# 1. ページの基本設定（ブラウザのタブに表示される名前とアイコン）
st.set_page_config(
    page_title="自分専用ラーメン食べログ", page_icon="🍜", layout="centered"
)

# 画面のタイトル
st.title("🍜 自分専用 ラーメン食べログ")
st.write(
    "Googleマップの口コミをAIが300文字に要約した、特製ラーメンデータベースです。"
)


# 2. データの読み込み（キャッシュ機能で2回目以降の読み込みを爆速に）
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
    # 3. 検索窓（UIパーツ）の設置
    keyword = st.text_input(
        "キーワードで探す（例：濃厚、新宿、家系、あっさり、つけ麺）", ""
    )

    # 4. 検索処理と結果の表示
    if keyword:
        # 入力された文字でデータをフィルタリング
        result = df[
            df["店名"].str.contains(keyword, na=False)
            | df["検索エリア"].str.contains(keyword, na=False)
            | df["300文字要約"].str.contains(keyword, na=False)
        ]

        st.subheader(f"🔍 「{keyword}」の検索結果 （{len(result)}件ヒット）")
        st.markdown("---")

        if len(result) == 0:
            st.warning("一致するラーメン店が見つかりませんでした。")
        else:
            # ヒットしたお店を1件ずつ綺麗に見せる
            for index, row in result.iterrows():
                # 枠で囲まれた見やすいコンテナを作る
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
        # 最初（未入力）の状態の表示
        st.info(
            "上の検索窓にキーワードを入力すると、お店の情報を絞り込めます。"
        )