"""플랫폼별 평점 격차 확인 — 데모의 핵심 주장이 실제 데이터로 성립하는지."""
import duckdb, pandas as pd

con = duckdb.connect()
con.execute("CREATE VIEW gn AS SELECT * FROM 'gangnam_reviews.parquet'")
cand = pd.read_csv("gangnam_candidates.csv")
con.register("cand", cand)

print("=== 강남구 전체 플랫폼 구성 ===")
print(con.sql("""
SELECT platform, count(*) AS reviews,
       round(avg(TRY_CAST(rating AS DOUBLE)), 2) AS avg_rating,
       round(100.0 * count(*) FILTER (WHERE TRY_CAST(rating AS DOUBLE) = 5) / count(*), 1) AS pct_5star,
       count(*) FILTER (WHERE content IS NOT NULL AND length(trim(content)) >= 10) AS text_reviews
FROM gn GROUP BY 1 ORDER BY 2 DESC
""").df().to_string(index=False))

print("\n=== 후보 매장별 플랫폼 평점 격차 (상위 20) ===")
gap = con.sql("""
WITH pr AS (
  SELECT g.business_number, c.name, g.platform,
         count(*) AS n,
         round(avg(TRY_CAST(g.rating AS DOUBLE)), 2) AS rating
  FROM gn g JOIN cand c
    ON g.business_number = c.business_number
   AND regexp_replace(g.shop_address, '\\s+', ' ', 'g') = c.addr
  WHERE g.rating IS NOT NULL
  GROUP BY 1,2,3
  HAVING count(*) >= 20
)
SELECT name,
       count(*) AS platforms,
       round(max(rating) - min(rating), 2) AS gap,
       string_agg(platform || ' ' || rating || ' (' || n || ')', ' · ' ORDER BY rating DESC) AS detail
FROM pr GROUP BY 1
HAVING count(*) >= 2
ORDER BY gap DESC
LIMIT 20
""").df()
print(gap.to_string(index=False))

print(f"\n격차 0.3 이상인 매장: {(gap['gap'] >= 0.3).sum()} / {len(gap)}")
