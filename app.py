import pandas as pd
import streamlit as st

# 1. ページの基本設定
st.set_page_config(
    page_title="ラーメン口コミ分析アプリ", page_icon="🍜", layout="centered"
)

st.title("🍜 ラーメン口コミ分析アプリ")
st.write("Googleマップの生の口コミデータから、キーワードの出現割合や地域特性を分析します。")


# 2. データの読み込み
@st.cache_data
def load_data():
    try:
        # ※CSV内に「すべての口コミ」という列がある前提
        return pd.read_csv("ramen_database_100.csv")
    except FileNotFoundError:
        return None


df = load_data()

if df is None:
    st.error("⚠️ 'ramen_database_100.csv' が見つかりません。")
else:
    # 3. 検索窓の設置
    keyword_input = st.text_input(
        "分析したいキーワードを入力してください（例：家系、あっさり、つけ麺）", ""
    )

    if keyword_input:
        # スペースや読点でキーワードを分解
        keywords = (
            keyword_input.replace(" ", " ")
            .replace("、", " ")
            .replace(",", " ")
            .split()
        )

        # 全店舗数
        total_shops = len(df)

        # 生の口コミ（「すべての口コミ」列）を対象にAND検索で絞り込み
        filtered_df = df.copy()
        for kw in keywords:
            # 「すべての口コミ」列からキーワードを探す
            filtered_df = filtered_df[
                filtered_df["すべての口コミ"].str.contains(kw, na=False)
            ]

        hit_shops = len(filtered_df)

        # --------------------------------------------------
        # 📊 ① 出現割合の計算
        # --------------------------------------------------
        st.header("📊 キーワード出現データ")
        if hit_shops > 0:
            # 全体におけるヒット率
            appearance_ratio = (hit_shops / total_shops) * 100
            st.metric(
                label=f"「{' ＋ '.join(keywords)}」を含む店舗の割合",
                value=f"{appearance_ratio:.1f} %",
                delta=f"全 {total_shops} 店舗中 {hit_shops} 店舗で出現",
            )
        else:
            st.warning("該当するキーワードが含まれる口コミは見つかりませんでした。")

        # --------------------------------------------------
        # 🗺️ ② 地域特性の分析（エリアごとの集計）
        # --------------------------------------------------
        st.header("🗺️ 地域特性（エリア別の出現傾向）")
        if hit_shops > 0:
            st.write("キーワードが含まれるお店が、どのエリアに多いかを分析しました：")

            # 全体のエリア別店舗数
            area_total = df["検索エリア"].value_counts()
            # ヒットしたお店のエリア別店舗数
            area_hit = filtered_df["検索エリア"].value_counts()

            # エリアごとの出現率を計算してデータフレームにまとめる
            area_stats = []
            for area in area_total.index:
                hits = area_hit.get(area, 0)
                total = area_total[area]
                ratio = (hits / total) * 100
                area_stats.append(
                    {
                        "エリア": area,
                        "ヒット店舗数": f"{hits}店舗",
                        "エリア内での出現割合": f"{ratio:.1f}%",
                    }
                )

            # 結果をテーブル（表）で綺麗に表示
            st.table(pd.DataFrame(area_stats))
        else:
            st.write("データがありません。")

        # --------------------------------------------------
        # 🔍 ③ 該当店舗の生口コミ表示
        # --------------------------------------------------
        st.header("📋 該当する店舗と口コミ一覧")
        if hit_shops > 0:
            for index, row in filtered_df.iterrows():
                with st.expander(f"📍 {row['店名']} （エリア: {row['検索エリア']}）"):
                    st.caption(f"住所: {row['住所']}")
                    st.markdown("**【実際の口コミ（生データ）】**")
                    st.write(row["すべての口コミ"])
    else:
        st.info("上の検索窓にキーワードを入力すると、分析が始まります。")
