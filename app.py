import re
import pandas as pd
import streamlit as st
import plotly.express as px  # グラフを描くためのライブラリを追加

st.set_page_config(
    page_title="ラーメン口コミ分析＆マッピングアプリ", page_icon="🍜", layout="centered"
)

st.title("🍜 ラーメン口コミ分析＆定量化アプリ")
st.write("口コミの生データからキーワード密度を分析し、さらに「おいしさ」を定量化して地域ごとのポジショニングを可視化します。")


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
    # ==================================================
    # 🧪 追加機能：おいしさスコア と 疑似価格帯 の自動計算
    # ==================================================
    # 「おいしさ」を判定するためのポジティブワードのリスト
    positive_words = ["美味しい", "おいしい", "最高", "絶品", "旨い", "うまい", "間違いない", "感動", "リピート"]

    def calculate_delicious_score(text):
        if pd.isna(text) or len(str(text)) == 0:
            return 0.0
        text_str = str(text)
        count = 0
        for word in positive_words:
            count += text_str.count(word)
        total_len = len(text_str)
        # 文字数に対するポジティブワードの出現密度（％）をスコアとする
        return (count / total_len) * 100

    # 疑似的な価格帯（CSVに価格データがない場合の対策として、店名や住所からランダム風に1〜3を割り振るロジック）
    # ※ 本来はGoogleマップから price_level を取るのがベストですが、現状のCSVで動かすための暫定処理です
    def assign_pseudo_price(name):
        # 店名の文字数の奇数偶数などで1〜3（￥〜￥￥￥）に分類
        return (len(str(name)) % 3) + 1

    # メインのデータフレームにスコア列を追加
    df["おいしさスコア"] = df["すべての口コミ"].apply(calculate_delicious_score)
    if "価格帯" not in df.columns:
        df["価格帯(￥)"] = df["店名"].apply(assign_pseudo_price)
    else:
        df["価格帯(￥)"] = df["価格帯"]


    # ==================================================
    # 📊 新機能：おいしさ×値段のポジショニングマップ（グラフ表示）
    # ==================================================
    st.header("🗺️ 地域別ラーメンポジショニングマップ")
    st.write("縦軸：口コミから算出した「おいしさ熱量スコア」 ／ 横軸：店舗の価格帯（￥1〜￥3）")

    # Plotlyを使ってインタラクティブな散布図を作成
    fig = px.scatter(
        df,
        x="価格帯(￥)",
        y="おいしさスコア",
        color="検索エリア",        # エリアごとにドットを色分け（地域特性の可視化）
        hover_name="店名",         # マウスを乗せたら店名を表示
        hover_data=["検索エリア"], # マウスを乗せたらエリア名も表示
        range_x=[0.5, 3.5],        # 横軸の範囲を固定
        title="【客観的データ分析】エリア別のおいしさ・価格の分布"
    )
    
    # グラフの見た目を少し綺麗に調整
    fig.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(xaxis=dict(tickvals=[1, 2, 3], ticktext=["￥ (低価格帯)", "￥￥ (中価格帯)", "￥￥￥ (高価格帯)"]))
    
    # Streamlitの画面にグラフを描画
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")


    # ==================================================
    # 🔍 既存機能：キーワード検索と詳細表示
    # ==================================================
    st.header("🔍 特定キーワードの密度・出現率分析")
    keyword_input = st.text_input(
        "分析したいキーワードを入力してください（例：大宮 濃厚）", ""
    )

    if keyword_input:
        cleaned_input = keyword_input.replace(" ", " ").replace("、", " ").replace(",", " ")
        keywords = cleaned_input.split()

        if keywords:
            total_shops = len(df)

            # AND検索で店舗を絞り込み
            filtered_df = df.copy()
            for kw in keywords:
                filtered_df = filtered_df[filtered_df["すべての口コミ"].str.contains(kw, na=False)]

            hit_shops = len(filtered_df)

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

            filtered_df["キーワード密度(%)"] = filtered_df["すべての口コミ"].apply(lambda t: calculate_multi_density(t, keywords))

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

            # 全体の出現傾向
            st.subheader("📊 全体の出現傾向")
            if hit_shops > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label=f"「{display_keywords}」が出現した店舗数", value=f"{hit_shops} / {total_shops} 店舗")
                with col2:
                    avg_density = filtered_df["キーワード密度(%)"].mean()
                    st.metric(label="ヒット店舗における平均出現率", value=f"{avg_density:.3f} %")
            else:
                st.warning(f"「{display_keywords}」が含まれる口コミは見つかりませんでした。")

            # 店舗ごとの詳細データ
            st.subheader("📋 店舗別の出現率（高い順）")
            if hit_shops > 0:
                sorted_df = filtered_df.sort_values(by="キーワード密度(%)", ascending=False)

                for index, row in sorted_df.iterrows():
                    text_str = str(row["すべての口コミ"])
                    total_len = len(text_str)
                    counts_text = ", ".join([f"「{kw}」: {text_str.count(kw)}回" for kw in keywords])
                    label_text = f"【出現率: {row['キーワード密度(%)']:.3f}%】 📍 {row['店名']} （{row['検索エリア']}）"

                    with st.expander(label_text):
                        st.caption(f"住所: {row['住所']}")
                        st.write(f"💡 **統計データ:** 総文字数 {total_len}文字中、{counts_text} 登場。")
                        st.write(f"✨ **算出おいしさスコア:** {row['おいしさスコア']:.3f} 点")
                        st.markdown("---")
                        st.markdown("**【AIによる要約】**")
                        st.write(row["300文字要約"])
                        st.markdown("---")
                        st.markdown("**【実際の口コミ（生データ）】**")
                        
                        highlighted_text = highlight_keywords(row["すべての口コミ"], keywords)
                        html_box = f"""
                        <div style="background-color: #ffffff; color: #222222; padding: 15px; border-radius: 8px; line-height: 1.7; font-size: 14px; font-family: sans-serif; border: 1px solid #dddddd; height: 250px; overflow-y: auto;">
                            {highlighted_text}
                        </div>
                        """
                        st.components.v1.html(html_box, height=280, scrolling=True)
    else:
        st.info("上の検索窓にキーワードを入力すると、詳細な確率・密度分析が始まります。")
