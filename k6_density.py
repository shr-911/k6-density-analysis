import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import streamlit as st

# =========================
# CSV読み込み
# =========================

# 6行目から読み込む
k6_df = pd.read_csv(
    "k6.csv",
    skiprows=3,
    encoding="cp932"  # Shift-JIS
)

# 都道府県一覧
prefectures = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県",
    "沖縄県"
]
# =========================
# 都道府県と直下の総数を取得
# =========================
k6_result = []
current_prefecture = None

for _, row in k6_df.iterrows():
    # １行目を取得
    first_value = re.sub(r'\s+', '', str(row.iloc[0]))
    # 年代別の数値を無視
    if first_value == "nan":
        continue

    # CSV表記と都道府県名を比較
    matched = [
        prefecture for prefecture in prefectures
        if first_value == prefecture.rstrip("都府県")
        or first_value == prefecture[:2]  # 京都府
        or first_value == prefecture
    ]

    if matched:
        current_prefecture = matched[0]

    elif current_prefecture is not None and first_value == "総数":
        k6_result.append({
            "都道府県": current_prefecture,
            "総数": row.iloc[2],
            "10点以上": row.iloc[5],
        })

        current_prefecture = None

k6_result_df = pd.DataFrame(k6_result)

k6_result_df["総数"] = pd.to_numeric(
    k6_result_df["総数"],
    errors="coerce"
)

k6_result_df["10点以上"] = pd.to_numeric(
    k6_result_df["10点以上"],
    errors="coerce"
)

st.title("K6調査結果")
st.dataframe(k6_result_df)

# =========================
# 人口密度
# =========================
population_df = pd.read_csv(
    "population_density.csv",
    skiprows=12,
    encoding="cp932"  # Shift-JIS
)

population_df = population_df[["地域", "#A01201_総面積１km2当たり人口密度【人】"]].copy()

population_df = population_df.rename(
    columns={
        "地域": "都道府県",
        "#A01201_総面積１km2当たり人口密度【人】": "人口密度"
    },
)

# =========================
# 都道府県と人口密度を結合
# =========================
merged_df = pd.merge(
    k6_result_df,
    population_df,
    on="都道府県",
    how="inner",
    validate="one_to_one"
)

# 10点以上の割合を計算
merged_df["10点以上の割合"] = merged_df["10点以上"] / merged_df["総数"] * 100
merged_df["10点以上の割合"] = merged_df["10点以上の割合"].round(2)

st.title("K6調査結果と人口密度の結合結果")
st.dataframe(merged_df)

merged_df["人口密度"] = merged_df["人口密度"].str.replace(",", "", regex=False)  # カンマを削除

merged_df["人口密度"] = pd.to_numeric(
    merged_df["人口密度"], 
    errors="coerce"
)

merged_df["人口密度_log"] = np.log10(merged_df["人口密度"])


print(f"相関係数：{merged_df['人口密度'].corr(merged_df['10点以上の割合'])}")
print(f"相関係数（対数変換後）：{merged_df['人口密度_log'].corr(merged_df['10点以上の割合'])}")

st.title("相関係数")
st.write(f"相関係数：{merged_df['人口密度'].corr(merged_df['10点以上の割合'])}")
st.write(f"相関係数（対数変換後）：{merged_df['人口密度_log'].corr(merged_df['10点以上の割合'])}")

# =========================
# グラフの描画
# =========================
plt.rcParams["font.family"] = "Hiragino Sans"  # 日本語フォントを指定

fig, axes = plt.subplots(1, 2, figsize=(12, 6))

axes[0].scatter(
    merged_df["人口密度"], 
    merged_df["10点以上の割合"]
)

axes[0].set_title("人口密度と10点以上の割合の関係")
axes[0].set_xlabel("人口密度(人/km²)")
axes[0].set_ylabel("10点以上の割合(%)")

axes[1].scatter(
    merged_df["人口密度"], 
    merged_df["10点以上の割合"]
)

axes[1].set_title("人口密度と10点以上の割合の関係（対数軸）")
axes[1].set_xlabel("人口密度(人/km²)")
axes[1].set_ylabel("10点以上の割合(%)")
axes[1].set_xscale("log")

# plt.show()
st.pyplot(fig)

# =========================
# 上位帯の傾向を確認
# =========================
top_density = merged_df.sort_values(by="人口密度", ascending=False).head(10)
bottom_density = merged_df.sort_values(by="人口密度", ascending=True).head(10)

st.title("人口密度上位10都道府県の傾向")
st.dataframe(top_density)
st.write(f"相関係数：{top_density['人口密度'].corr(top_density['10点以上の割合'])}")
st.write(f"相関係数（対数変換後）：{top_density['人口密度_log'].corr(top_density['10点以上の割合'])}")

st.title("人口密度下位10都道府県の傾向")
st.dataframe(bottom_density)
st.write(f"相関係数：{bottom_density['人口密度'].corr(bottom_density['10点以上の割合'])}")
st.write(f"相関係数（対数変換後)：{bottom_density['人口密度_log'].corr(bottom_density['10点以上の割合'])}")

fig, ax = plt.subplots(1, 2, figsize=(12, 6))

x = top_density["人口密度"]
y = top_density["10点以上の割合"]

ax[0].scatter(x, y)
ax[0].set_title("人口密度上位10都道府県の10点以上の割合")
ax[0].set_xlabel("人口密度(人/km²)")
ax[0].set_ylabel("10点以上の割合(%)")

x = bottom_density["人口密度"]
y = bottom_density["10点以上の割合"]

ax[1].scatter(x, y)
ax[1].set_title("人口密度下位10都道府県の10点以上の割合")
ax[1].set_xlabel("人口密度(人/km²)")
ax[1].set_ylabel("10点以上の割合(%)")

# plt.show()
st.pyplot(fig)

# 人口密度順に４つのグループに分けて分析
merged_df["density_group"] = pd.qcut(
    merged_df["人口密度"], 
    4, 
    labels=["低", "中低", "中高", "高"]
    )

correlations = (
    merged_df.groupby("density_group", observed=True)
    .apply(lambda x: x["人口密度"].corr(x["10点以上の割合"]))
)

st.title("人口密度グループごとの相関係数")
st.dataframe(correlations)

# 各都道府県を除外
results = []

for prefecture in merged_df["都道府県"]:
    temp_df = merged_df[merged_df["都道府県"] != prefecture]
    correlation = temp_df["人口密度"].corr(temp_df["10点以上の割合"])
    results.append((prefecture, correlation))

results_df = pd.DataFrame(results, columns=["都道府県", "相関係数"])

st.title("各都道府県を除外した場合の相関係数")
st.dataframe(results_df.sort_values(by="相関係数", ascending=False))

# =========================
# 単身世帯数の追加
# =========================
single_households_df = pd.read_csv(
    "single_households.csv",
    skiprows=14,
    encoding="cp932"  # Shift-JIS
)

single_households_df = single_households_df.rename(columns={
    "全国，都道府県，市区町村（人口集中地区）": "都道府県",
    "世帯の家族類型": "世帯類型",
    "総数": "世帯数"
})

print(single_households_df.head())
print(single_households_df.shape)

result = []
prefecture = ""
total_households_count = 0
single_households_count = 0

for _, row in single_households_df.iterrows():
    if prefecture != row["都道府県"]:
        prefecture = row["都道府県"]

    if row["世帯類型"] == "総数":
        total_households_count = int(row["世帯数"].replace(",", ""))
    
    if row["世帯類型"] == "単独世帯":
        single_households_count = int(row["世帯数"].replace(",", ""))
        result.append({
            "都道府県": prefecture,
            "総世帯数": total_households_count,
            "単身世帯数": single_households_count,
            "単身世帯率": single_households_count / total_households_count * 100
        })

households_df = pd.DataFrame(result)

merged_df = pd.merge(
    merged_df,
    households_df,
    on="都道府県",
    how="inner",
    validate="one_to_one"
)

st.title("K6調査結果と人口密度、単身世帯率の結合結果")
st.dataframe(merged_df[["都道府県", "総世帯数", "単身世帯数", "単身世帯率", "人口密度", "10点以上の割合"]])

# 散布図で表示
st.title("単身世帯率と10点以上の割合の関係")
x = merged_df["単身世帯率"].astype(float)
y = merged_df["10点以上の割合"].astype(float)

fig, ax = plt.subplots()
ax.scatter(x, y)
ax.set_xlabel("単身世帯率（%）")
ax.set_ylabel("K6 10点以上の割合（%）")
ax.set_title("単身世帯率とK6 10点以上の割合")
st.pyplot(fig)

st.write(f"単身世帯率と10点以上の割合の相関係数: {x.corr(y):.3f}")

# 相関係数行列を表示
st.title("人口密度、単身世帯率、10点以上の割合の相関係数")
cols = ["人口密度", "単身世帯率", "10点以上の割合"]
correlation_matrix = merged_df[cols].astype(float).corr()
st.write(correlation_matrix)

# =========================
# 偏相関係数の計算
# =========================
r_xy = merged_df["人口密度"].astype(float).corr(merged_df["10点以上の割合"].astype(float))
r_xz = merged_df["人口密度"].astype(float).corr(merged_df["単身世帯率"].astype(float))
r_yz = merged_df["10点以上の割合"].astype(float).corr(merged_df["単身世帯率"].astype(float))

# 偏相関係数の計算
partial_correlation = (r_xy - r_xz * r_yz) / np.sqrt((1 - r_xz**2) * (1 - r_yz**2))

st.title("偏相関係数の計算結果")
st.write(f"人口密度と10点以上の割合の偏相関係数（単身世帯率を制御）: {partial_correlation:.3f}")

# 人口密度とK6の相関係数とp値を計算
from scipy.stats import pearsonr
r, p = pearsonr(merged_df["人口密度"].astype(float), merged_df["10点以上の割合"].astype(float))
st.write(f"人口密度と10点以上の割合の相関係数: {r:.3f}")
st.write(f"p値: {p:.3f}")
