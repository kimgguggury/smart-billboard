# import sqlite3
# import pandas as pd

# # 🔧 DB 연결
# conn = sqlite3.connect("Smartboard.db")

# # ✅ ad 테이블 조회
# ad_df = pd.read_sql_query("SELECT * FROM ad", conn)

# # ✅ ad_stats 테이블 조회
# stats_df = pd.read_sql_query("SELECT * FROM ad_stats", conn)

# # ✅ group_key 기준으로 피벗: 성별별 view_count
# pivot_df = stats_df.pivot_table(
#     index="ad_id",
#     columns="group_key",
#     values="view_count",
#     fill_value=0
# ).reset_index()

# # ✅ ad_id 타입 맞추기 (int로 변환)
# pivot_df["ad_id"] = pivot_df["ad_id"].astype(int)

# # ✅ 병합: ad + ad_stats
# merged_df = pd.merge(ad_df, pivot_df, on="ad_id", how="left")

# # ✅ NaN → 0으로 대체
# merged_df = merged_df.fillna(0)

# # ✅ CSV로 저장
# merged_df.to_csv("ad_stats_report.csv", index=False, encoding="utf-8-sig")

# print("✅ ad_stats_report.csv 파일로 저장 완료!")

import sqlite3
import pandas as pd

# 🔧 DB 연결
conn = sqlite3.connect("Smartboard.db")

# ✅ ad 테이블 조회
ad_df = pd.read_sql_query("SELECT * FROM ad", conn)

# ✅ ad_stats 테이블 조회
stats_df = pd.read_sql_query("SELECT * FROM ad_stats", conn)

# ✅ group_key 대신 sex + age_group 조합된 column 만들기
stats_df["group_key"] = stats_df["sex"] + "-" + stats_df["age_group"].astype(str)

# ✅ 피벗 테이블 생성
pivot_df = stats_df.pivot_table(
    index="ad_id",
    columns="group_key",
    values="view_count",
    fill_value=0
).reset_index()

# ✅ ad_id 타입 맞추기 (int로 변환)
pivot_df["ad_id"] = pivot_df["ad_id"].astype(int)

# ✅ 병합: ad + ad_stats
merged_df = pd.merge(ad_df, pivot_df, on="ad_id", how="left")

# ✅ NaN → 0으로 대체
merged_df = merged_df.fillna(0)

# ✅ CSV로 저장
merged_df.to_csv("ad_stats_report.csv", index=False, encoding="utf-8-sig")

print("✅ ad_stats_report.csv 파일로 저장 완료!")
