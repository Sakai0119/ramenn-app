import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ラーメン口コミ密度分析アプリ", page_icon="🍜", layout="centered"
)

st.title("🍜 ラーメン口コミ密度分析アプリ")
st.write("各店舗の全口コミの文字数に対して、キーワードがどれくらいの割合（密度）で出現しているかを分析します。")


@st.cache_data
def load_data():
    try:
        return pd.read_csv("ramen_database_100.csv")
    except FileNotFoundError:
        return None


df = load_data()

if df is None:
    st.error("⚠️ 'ramen_database_100.csv' が見つかりません。")
else:
    keyword_input = st.text_input(
        "分析したいキーワードを入力してください（例：濃厚、家系、あっさり）", ""
    )

    if keyword_input:
        # スペース等で分解せず、今回は指定されたひとつの塊（フレーズ）として数えます
        kw = keyword_input.strip()

        if kw:
            total_shops = len(df)

            # キーワードが含まれるお店だけを抽出
            filtered_df = df[df["すべての口コミ"].str.contains(kw, na=False)].copy()
            hit_shops = len(filtered_df)

            # --------------------------------------------------
            # 📊 ① 各店舗の口コミ内での出現率（密度）を計算
            # --------------------------------------------------
            def calculate_density(text, keyword):
                if pd.isna(text) or len(str(text)) == 0:
                    return 0.0
                text_str = str(text)
                count = text_str.count(keyword)  # キーワードの登場回数
                kw_len = len(keyword)  # キーワードの文字数
                total_len = len(text_str)  # 全口コミの総文字数
                return ((count * kw_len) / total_len) * 100

            # 全データに対して密度を計算して新しい列を作る
            df["キーワード密度(%)"] = df["すべての口コミ"].apply(
                lambda t: calculate_density(t, kw)
            )
            filtered_df["キーワード密度(%)"] = filtered_df["すべての口コミ"].apply(
                lambda t: calculate_density(t, kw)
            )

            # --------------------------------------------------
            # 📈 ② 全体データのサマリー表示
            # --------------------------------------------------
            st.header("📊 全体の出現傾向")
            if hit_shops > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label="キーワードが出現した店舗数",
                        value=f"{hit_shops} / {total_shops} 店舗",
                    )
                with col2:
                    # ヒットしたお店の中での平均密度
                    avg_density = filtered_df["キーワード密度(%)"].mean()
                    st.metric(
                        label="ヒット店舗における平均出現率（文字密度）",
                        value=f"{avg_density:.3f} %",
                    )
            else:
                st.warning("該当するキーワードが含まれる口コミは見つかりませんでした。")

            # --------------------------------------------------
            # 🗺️ ③ 地域特性（エリア別の平均出現率）
            # --------------------------------------------------
            st.header("🗺️ 地域特性（エリア別の平均出現率）")
            if hit_shops > 0:
                st.write(
                    f"各エリアの店舗の口コミ全体で、「{kw}」が占める平均割合を算出しました："
                )

                # エリアごとに「キーワード密度(%)」の平均を計算（全店舗を対象にすることで地域特性を見る）
                area_avg_density = (
                    df.groupby("検索エリア")["キーワード密度(%)"].mean().reset_index()
                )
                area_avg_density.columns = ["エリア", "全店舗での平均出現率(%)"]

                # 出現率が高い順に並び替え
                area_avg_density = area_avg_density.sort_values(
                    by="全店舗での平均出現率(%)", ascending=False
                )

                # 表示用に小数点を綺麗に整形
                area_avg_density["全店舗での平均出現率(%)"] = area_avg_density[
                    "全店舗での平均出現率(%)"
                ].map(lambda x: f"{x:.4f}%")

                st.table(area_avg_density)

            # --------------------------------------------------
            # 📋 ④ 店舗ごとの詳細データ（出現率順に並び替え）
            # --------------------------------------------------
            st.header("📋 店舗別の出現率（高い順）")
            if hit_shops > 0:
                # 出現率（密度）が高い順にお店を並び替える
                sorted_df = filtered_df.sort_values(
                    by="キーワード密度(%)", ascending=False
                )

                for index, row in sorted_df.iterrows():
                    # 各お店の総文字数と出現回数を計算（表示用）
                    text_str = str(row["すべての口コミ"])
                    count = text_str.count(kw)
                    total_len = len(text_str)

                    label_text = f"【出現率: {row['キーワード密度(%)']:.3f}%】 📍 {row['店名']} （{row['検索エリア']}）"

                    with st.expander(label_text):
                        st.caption(f"住所: {row['住所']}")
                        st.write(
                            f"💡 **統計データ:** 口コミ総文字数 {total_len}文字 中、キーワード 「{kw}」 が **{count}回** 登場しています。"
                        )
                        st.markdown("---")
                        st.markdown("**【実際の口コミ（生データ）】**")
                        st.write(row["すべての口コミ"])
    else:
        st.info("上の検索窓にキーワードを入力すると、詳細な確率・密度分析が始まります。")
