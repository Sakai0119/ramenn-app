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
    # 🧪 データの前処理・スコア化（見やすさ改善版）
    # ==================================================
    # 味覚・料理を褒める言葉のバリエーションを強化
    positive_words = ["美味しい", "おいしい", "旨い", "うまい", "絶品", "味がいい", "スープが優秀", "麺がうまい", "激ウマ", "美味すぎる", "最高", "リピート"]

    def calculate_delicious_score(text):
        if pd.isna(text) or len(str(text)) == 0:
            return 0.0
        text_str = str(text)
        count = 0
        for word in positive_words:
            count += text_str.count(word)
        
        # 💡 スコアの補正：全体の文字数ではなく、文の数や密度に対するアプローチに変更
        # 低くなりすぎるのを防ぐため、係数(500)を掛けて「100点満点のダイナミックなスコア」に変形します
        raw_score = (count / len(text_str)) * 500
        
        # 最高でも100点、最低でも30点程度に収まるように補正してグラフのばらつきを綺麗にする
        adjusted_score = min(100.0, max(30.0, 30.0 + raw_score * 10))
        
        # 💡 少数第一位までに丸める
        return round(adjusted_score, 1)

    # データの計算と列追加
    df["おいしさスコア"] = df["すべての口コミ"].apply(calculate_delicious_score)
    
    # 住所から「習志野市」か「船橋市」かを自動判別する列を作る
    def detect_city(address):
        address_str = str(address)
        if "習志野" in address_str:
            return "習志野市"
        elif "船橋" in address_str:
            return "船橋市"
        else:
            return "その他エリア"

    df["所属市区町村"] = df["住所"].apply(detect_city)

    # 習志野市と船橋市のデータだけに絞り込む
    target_df = df[df["所属市区町村"].isin(["習志野市", "船橋市"])].copy()

    # ==================================================
    # 🗺️ グラフ表示セクション（視認性向上版）
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
        # Plotlyで具体的な金額を横軸にした散布図を描画
        fig = px.scatter(
            plot_df,
            x="価格",           
            y="おいしさスコア",
            color=color_column,
            hover_name="店名",
            hover_data=["住所"],
            range_x=[600, 1400],       # 横軸の範囲をラーメンの現実的なラインに狭めて見やすく
            range_y=[25, 105],         # 縦軸の範囲を固定して点数の高低を分かりやすく
            title=title_text,
            labels={"価格": "ラーメン1杯の推定価格（円）", "おいしさスコア": "おいしさ熱量スコア（味ポジティブ度）"}
        )
        
        # 💡 グラフを「見づらい」から「見やすい」にするためのプロット調整
        fig.update_traces(
            marker=dict(
                size=16,               # ドットのサイズを大きくしてタップ・ホバーしやすく
                opacity=0.85,          # 重なりが見えるように少し透明に
                line=dict(width=1.5, color='DarkSlateGrey') # ドットの輪郭を強調
            )
        )
        
        # 背景色の変更とグリッド線（補助線）の強化
        fig.update_layout(
            plot_bgcolor="#f9f9f9",
            xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
            yaxis=dict(showgrid=True, gridcolor="#e0e0e0", dtick=10) # 10点刻みで線を引く
        )
            
        st.plotly_chart(fig, use_container_width=True)
        st.write(f"💡 現在画面に表示されている店舗数: **{len(plot_df)} 店舗**")
    else:
        st.warning("選択されたエリアのデータがCSV内に見つかりませんでした。データ収集コードを実行して生成された最新のCSVをアップロードしてください。")

    st.markdown("---")

    # ==================================================
    # 🔍 キーワード検索・店舗一覧
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
                
                # ヒットした店舗をスコア順に並び替えて展開
                sorted_search_df = search_df.sort_values(by="おいしさスコア", ascending=False)
                
                for index, row in sorted_search_df.iterrows():
                    # 💡 ここも小数点第一位までの表示に合わせてスッキリ修正
                    label_text = f"【おいしさ: {row['おいしさスコア']:.1f}点】 📍 {row['店名']} （{row['所属市区町村']}）"
                    with st.expander(label_text):
                        st.caption(f"住所: {row['住所']}")
                        st.write(f"💰 **価格:** {row['価格']} 円")
                        st.markdown("---")
                        st.markdown("**【実際の口コミ（生データ）】**")
                        
                        # 簡易ハイライト
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
