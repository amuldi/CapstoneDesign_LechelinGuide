"""강남구 매장 추출 — 플랫폼 2개 이상 + 텍스트 리뷰 충분한 매장 후보."""
import duckdb, pathlib

SRC = "/Users/ijaehyeong/Downloads/순천향대_제공_리뷰_데이터/*.csv"
OUT = pathlib.Path(__file__).parent

con = duckdb.connect()
con.execute("SET preserve_insertion_order=false")

# 강남구 리뷰만 뽑아 중간 테이블로
con.execute(f"""
CREATE OR REPLACE TABLE gn AS
SELECT business_number, platform_shop_name, platform, shop_address,
       created_at::TIMESTAMP AS created_at,
       TRY_CAST(rating AS DOUBLE) AS rating,
       content, menus,
       TRY_CAST(order_count AS INTEGER) AS order_count,
       TRY_CAST(visit_count AS INTEGER) AS visit_count,
       review_type, keywords
FROM read_csv('{SRC}', union_by_name=true, ignore_errors=true,
              strict_mode=false, all_varchar=true, header=true)
WHERE shop_address LIKE '%강남구%'
""")

print("강남구 리뷰:", con.sql("SELECT count(*) FROM gn").fetchone()[0])

# 매장 키 = 사업자번호 + 정규화 주소 (지점 분리용)
con.execute("""
CREATE OR REPLACE TABLE shops AS
SELECT business_number,
       regexp_replace(shop_address, '\\s+', ' ', 'g') AS addr,
       any_value(platform_shop_name)                   AS name,
       count(*)                                        AS reviews,
       count(*) FILTER (WHERE content IS NOT NULL
                          AND length(trim(content)) >= 10) AS text_reviews,
       count(DISTINCT platform)                        AS platforms,
       round(avg(rating), 2)                           AS avg_rating,
       max(created_at)                                 AS last_review
FROM gn
GROUP BY 1, 2
""")

cand = con.sql("""
SELECT * FROM shops
WHERE platforms >= 2 AND text_reviews >= 200
ORDER BY text_reviews DESC
""").df()

print(f"\n후보 매장 (플랫폼 2개 이상 + 텍스트 200건 이상): {len(cand)}곳")
print(cand.head(25).to_string(index=False))

cand.to_csv(OUT / "gangnam_candidates.csv", index=False)
con.execute(f"COPY gn TO '{OUT}/gangnam_reviews.parquet' (FORMAT PARQUET)")
print(f"\n저장: {OUT}/gangnam_candidates.csv, gangnam_reviews.parquet")
