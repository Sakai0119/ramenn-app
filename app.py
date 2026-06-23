import re
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="習志野・船橋 ラーメン特化分析アプリ", page_icon="🍜", layout="centered"
)

st.title("🍜 習志野・船橋 ラーメン網羅分析＆マッピング")
st.write("習志野市と船橋市のラーメン店を完全網羅し、口コミから算出した「おいしさ熱量スコア」と「具体的な金額」で地域特性を比較します。")


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

    # 💡 補助関数：生の口コミから、検索ワードを含む重要な1文を抜き出して300字以内の要約を自動生成する
    def generate_auto_summary(text, kw_list):
        if pd.isna(text) or len(str(text)) == 0:
            return "口コミがありません。"
        
        text_str = str(text).replace("\n", " ")
        # 文ごとにバラす（「。」「！」で区切る）
        sentences = re.split(r'(?<=[。！?])\s*', text_str)
        
        summary_sentences = []
        current_len = 0
        
        # まずは検索キーワードが含まれる重要な文章を優先してピックアップ
        for s in sentences:
            if any(kw in s for kw in kw_list) and s not in summary_sentences:
                if current_len + len(s) < 260:  # 余裕を持って文字数を制御
                    summary_sentences.append(s)
                    current_len += len(s)
        
        # キーワード入りの文だけだと短い場合、先頭の口コミから文章を補う
        if current_len < 100:
            for s in sentences:
                if s not in summary_sentences:
                    if current_len + len(s) < 280:
                        summary_sentences.append(s)
                        current_len += len(s)
                    else:
                        break
                        
        summary_text = "".join(summary_sentences)
        if len(summary_text) > 300:
            summary_text = summary_text[:297] + "..."
            
        return summary_text if summary_text else text_str[:250] + "..."

    # スコア列の追加
    df["おいしさスコア"] = df["すべての口コミ"].apply(calculate_delicious_score)
    
    # 住所から所属市を判別
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
    # 🗺️ グラフ表示セクション
    # ==================================================
    st.header("🗺️ 市別のラーメンポジショニングマップ")
    
    analysis_mode = st.radio(
        "表示するエリアを選択してください：",
        ["習志野市と船橋市を比較する", "習志野市のみ表示", "船橋市のみ表示"],
        horizontal=True
    )

    if analysis_mode == "習志野市のみ表示":
        plot_df = target_df[target_df["所属市区町村"] == "習志野市"]
        color_column = None
        title_text = "【習志野市】 ラーメンポジショニングマップ"
    elif analysis_mode == "船橋市のみ表示":
        plot_df = target_df[target_df["所属市区町村"] == "船橋市"]
        color_column = None
        title_text = "【船橋市】 ラーメンポジショニングマップ"
    else:
        plot_df = target_df
        color_column = "所属市区町村"
        title_text = "【習志野市 vs 船橋市】 ラーメン市場ポジショニング比較"

    if len(plot_df) > 0:
        fig = px.scatter(
            plot_df,
            x="価格",           
            y="おいしさスコア",
            color=color_column,
            hover_name="店名",
            hover_data=["住所"],
            range_x=[600, 1400],       
            range_y=[25, 105],         
            title=title_text,
            labels={"価格": "ラーメン1杯の推定価格（円）", "おいしさスコア": "おいしさ熱量スコア（味ポジティブ度）"}
        )
        
        fig.update_traces(
            marker=dict(
                size=16,               
                opacity=0.85,          
                line=dict(width=1.5, color='DarkSlateGrey') 
            )
        )
        
        fig.update_layout(
            plot_bgcolor="#f9f9f9",
            xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
            yaxis=dict(showgrid=True, gridcolor="#e0e0e0", dtick=10) 
        )
            
        st.plotly_chart(fig, use_container_width=True)
        st.write(f"💡 現在画面に表示されている店舗数: **{len(plot_df)} 店舗**")
    else:
        st.warning("選択されたエリアのデータがCSV内に見つかりませんでした。")

    st.markdown("---")

    # ==================================================
    # 🔍 キーワード検索・店舗一覧（要約＆強調強化）
    # ==================================================
    st.header("🔍 特定キーワードの密度・口コミ検索")
    keyword_input = st.text_input("調べたい特徴を入力（例：津田沼 濃厚、家系）", "")

    if keyword_input:
        cleaned_input = keyword_input.replace(" ", " ").replace("、", " ").replace(",", " ")
        keywords = cleaned_input.split()

        if keywords:
            search_df = plot_df.copy()
            for kw in keywords:
                search_df = search_df[search_df["すべての口コミ"].str.contains(kw, na=False)]

            hit_shops = len(search_df)
            display_keywords = " ＋ ".join(keywords)

            st.subheader(f"📊 「{display_keywords}」の出現傾向")
            if hit_shops > 0:
                st.info(f"選択中のエリア内で **{hit_shops} 店舗** がヒットしました。")
                
                sorted_search_df = search_df.sort_values(by="おいしさスコア", ascending=False)
                
                for index, row in sorted_search_df.iterrows():
                    label_text = f"【おいしさ: {row['おいしさスコア']:.1f}点】 📍 {row['店名']} （{row['所属市区町村']}）"
                    
                    with st.expander(label_text):
                        st.caption(f"住所: {row['住所']}")
                        st.write(f"💰 **価格:** {row['価格']} 円")
                        
                        # 💡 検索ワードをベースに「その場で300字要約」を動的生成
                        raw_summary = generate_auto_summary(row["すべての口コミ"], keywords)
                        
                        # 要約文のキーワードもハイライト
                        highlighted_summary = raw_summary
                        for kw in keywords:
                            highlighted_summary = re.sub(re.escape(kw), f"<mark style='background-color: #ffeb3b; color: #000000; font-weight: bold;'>{kw}</mark>", highlighted_summary)
                            
                        st.markdown("---")
                        st.markdown("**📝 【300字特徴要約（検索キーワード優先抽出）】**")
                        # HTMLコンポーネントを使って要約のマーカーを綺麗に描画
                        st.components.v1.html(f"<div style='color: #333333; font-size: 14px; line-height: 1.6; font-family: sans-serif;'>{highlighted_summary}</div>", height=90)
                        
                        st.markdown("---")
                        st.markdown("**📜 【実際の口コミ（生データ・キーワード強調）】**")
                        
                        # 生の口コミのハイライト
                        text_str = str(row["すべての口コミ"]).replace("\n", "<br>")
                        for kw in keywords:
                            text_str = re.sub(re.escape(kw), f"<mark style='background-color: #ffeb3b; color: #000000; font-weight: bold;'>{kw}</mark>", text_str)
                        
                        html_box = f"""
                        <div style="background-color: #ffffff; color: #222222; padding: 15px; border-radius: 8px; line-height: 1.7; font-size: 14px; font-family: sans-serif; border: 1px solid #dddddd; height: 200px; overflow-y: auto;">
                            {text_str}
                        </div>
                        """
                        st.components.v1.html(html_box, height=230, scrolling=True)
            else:
                st.warning("該当する店舗は見つかりませんでした。")
