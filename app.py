import re
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
        "分析したいキーワードを入力してください（スペースや読点で複数指定可。例：大宮 濃厚）", ""
    )

    if keyword_input:
        cleaned_input = (
            keyword_input.replace(" ", " ")
            .replace("、", " ")
            .replace(",", " ")
        )
        keywords = cleaned_input.split()

        if keywords:
            total_shops = len(df)

            # 1. AND検索で店舗を絞り込み
            filtered_df = df.copy()
            for kw in keywords:
                filtered_df = filtered_df[
                    filtered_df["すべての口コミ"].str.contains(kw, na=False)
                ]

            hit_shops = len(filtered_df)

            # --------------------------------------------------
            # 📊 ① 密度計算
            # --------------------------------------------------
            def calculate_multi_density(text, kw_list):
                if pd.isna(text) or len(str(text)) == 0:
                    return 0.0
                text_str = str(text)
                total_kw_len_count = 0
                for kw in kw_list:
                    count = text_str.count(kw)
                    total_kw_len_count += count * len(kw)
                total_len = len(text_str)
                return (total_kw_len_count / total_len) * 100

            df["キーワード密度(%)"] = df["すべての口コミ"].apply(
                lambda t: calculate_multi_density(t, keywords)
            )
            filtered_df["キーワード密度(%)"] = filtered_df["すべての口コミ"].apply(
                lambda t: calculate_multi_density(t, keywords)
            )

            # --------------------------------------------------
            # 🖌️ ② キーワードのハイライト処理
            # --------------------------------------------------
            def highlight_keywords(text, kw_list):
                if pd.isna(text):
                    return ""
                text_str = str(text)
                text_str = text_str.replace("\n", "<br>")

                for kw in kw_list:
                    if kw:
                        escaped_kw = re.escape(kw)
                        text_str = re.sub(
                            escaped_kw,
                            f"<mark style='background-color: #ffeb3b; color: #000000; font-weight: bold; border-radius: 3px; padding: 0 2px;'>{kw}</mark>",
                            text_str,
                        )
                return text_str

            display_keywords = " ＋ ".join(keywords)

            # --------------------------------------------------
            # 📈 ③ 全体の出現傾向
            # --------------------------------------------------
            st.header("📊 全体の出現傾向")
            if hit_shops > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label=f"「{display_keywords}」がすべて出現した店舗数",
                        value=f"{hit_shops} / {total_shops} 店舗",
                    )
                with col2:
                    avg_density = filtered_df["キーワード密度(%)"].mean()
                    st.metric(
                        label="ヒット店舗における平均出現率（文字密度）",
                        value=f"{avg_density:.3f} %",
                    )
            else:
                st.warning(
                    f"「{display_keywords}」がすべて含まれる口コミは見つかりませんでした。"
                )

            # --------------------------------------------------
            # 🗺️ ④ 地域特性
            # --------------------------------------------------
            st.header("🗺️ 地域特性（エリア別の平均出現率）")
            if hit_shops > 0:
                area_avg_density = (
                    df.groupby("検索エリア")["キーワード密度(%)"].mean().reset_index()
                )
                area_avg_density.columns = ["エリア", "全店舗での平均出現率(%)"]
                area_avg_density = area_avg_density.sort_values(
                    by="全店舗での平均出現率(%)", ascending=False
                )
                area_avg_density["全店舗での平均出現率(%)"] = area_avg_density[
                    "全店舗での平均出現率(%)"
                ].map(lambda x: f"{x:.4f}%")

                st.table(area_avg_density)

            # --------------------------------------------------
            # 📋 ⑤ 店舗ごとの詳細データ
            # --------------------------------------------------
            st.header("📋 店舗別の出現率（高い順）")
            if hit_shops > 0:
                sorted_df = filtered_df.sort_values(
                    by="キーワード密度(%)", ascending=False
                )

                for index, row in sorted_df.iterrows():
                    text_str = str(row["すべての口コミ"])
                    total_len = len(text_str)

                    counts_text = ", ".join(
                        [f"「{kw}」: {text_str.count(kw)}回" for kw in keywords]
                    )
                    label_text = f"【出現率: {row['キーワード密度(%)']:.3f}%】 📍 {row['店名']} （{row['検索エリア']}）"

                    with st.expander(label_text):
                        st.caption(f"住所: {row['住所']}")
                        st.write(
                            f"💡 **統計データ:** 口コミ総文字数 {total_len}文字 中、{counts_text} 登場しています。"
                        )
                        st.markdown("---")
                        st.markdown("**【AIによる要約】**")
                        st.write(row["300文字要約"])
                        st.markdown("---")

                        st.markdown("**【実際の口コミ（生データ）】**")
                        highlighted_text = highlight_keywords(
                            row["すべての口コミ"], keywords
                        )

                        # HTMLの枠組み。はみ出た文字は自動でスクロールできるようにCSSを設定
                        html_box = f"""
                        <div style="
                            background-color: #ffffff; 
                            color: #222222; 
                            padding: 15px; 
                            border-radius: 8px; 
                            line-height: 1.7; 
                            font-size: 14px;
                            font-family: sans-serif;
                            border: 1px solid #dddddd;
                            height: 300px;
                            overflow-y: auto;
                        ">
                            {highlighted_text}
                        </div>
                        """
                        # scrolling=True に修正してエラーを回避
                        st.components.v1.html(html_box, height=330, scrolling=True)
    else:
        st.info("上の検索窓にキーワードを入力すると、詳細な確率・密度分析が始まります。")
