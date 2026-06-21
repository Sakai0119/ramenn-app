import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ラーメン口コミ分析アプリ", page_icon="🍜", layout="centered"
)

st.title("🍜 ラーメン口コミ分析アプリ")
st.write("Googleマップの生の口コミデータから、キーワードの出現割合や地域特性を分析します。")


@st.cache_data
def load_data():
    try:
        # 新しいCSV（「すべての口コミ」列がある状態）を読み込む
        return pd.read_csv("ramen_database_100.csv")
    except FileNotFoundError:
        return None


df = load_data()

if df is None:
    st.error("⚠️ 'ramen_database_100.csv' が見つかりません。")
else:
    keyword_input = st.text_input(
        "分析したいキーワードを入力してください（スペースや読点で複数指定可。例：大宮 濃厚）", ""
    )

    if keyword_input:
        keywords = (
            keyword_input.replace(" ", " ")
            .replace("、", " ")
            .replace(",", " ")
            .split()
        )

        total_shops = len(df)

        # 生の口コミ（「すべての口コミ」列）を対象に検索
        filtered_df = df.copy()
        for kw in keywords:
            filtered_df = filtered_df[
                filtered_df["すべての口コミ"].str.contains(kw, na=False)
            ]

        hit_shops = len(filtered_df)

        # --------------------------------------------------
        # 📊 ① 出現割合の計算
        # --------------------------------------------------
        st.header("📊 キーワード出現データ")
        if hit_shops > 0:
            appearance_ratio = (hit_shops / total_shops) * 100
            st.metric(
                label=f"「{' ＋ '.join(keywords)}」を含む店舗の割合",
                value=f"{appearance_ratio:.1f} %",
                delta=f"全 {total_shops} 店舗中 {hit_shops} 店舗で出現",
            )
        else:
            st.warning("該当するキーワードが含まれる口コミは見つかりませんでした。")

        # --------------------------------------------------
        # 🗺️ ② 地域特性の分析
        # --------------------------------------------------
        st.header("🗺️ 地域特性（エリア別の出現傾向）")
        if hit_shops > 0:
            # エリアごとの全体の分母と、ヒットした分子を正確に集計
            area_total = df["検索エリア"].value_counts()
            area_hit = filtered_df["検索エリア"].value_counts()

            area_stats = []
            for area in area_total.index:
                hits = area_hit.get(area, 0)
                total = area_total[area]
                ratio = (hits / total) * 100
                area_stats.append(
                    {
                        "エリア": area,
                        "ヒット店舗数": f"{hits} / {total} 店舗",
                        "エリア内での出現割合": f"{ratio:.1f}%",
                    }
                )

            st.table(pd.DataFrame(area_stats))

        # --------------------------------------------------
        # 🔍 ③ 該当店舗の生口コミ表示
        # --------------------------------------------------
        st.header("📋 該当する店舗と口コミ一覧")
        if hit_shops > 0:
            for index, row in filtered_df.iterrows():
                with st.expander(f"📍 {row['店名']} （エリア: {row['検索エリア']}）"):
                    st.caption(f"住所: {row['住所']}")
                    st.markdown("**【AIによる要約】**")
                    st.write(row["300文字要約"])
                    st.markdown("---")
                    st.markdown("**【実際の口コミ（生データ）】**")
                    st.write(row["すべての口コミ"])
    else:
        st.info("上の検索窓にキーワードを入力すると、分析が始まります。")
