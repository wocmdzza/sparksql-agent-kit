-- Synthetic sample only: mimics the shape of a legacy daily SparkSQL job.
-- No company data. Used to verify the extractor before it ever touches real scripts.
INSERT OVERWRITE TABLE dws_user_active_daily PARTITION (dt = '${bizdate}')
WITH dedup AS (
  SELECT user_id, MAX(login_time) AS last_login
  FROM ods_user_login_log
  WHERE dt = '${bizdate}' AND login_status = 1
  GROUP BY user_id
)
SELECT
  a.user_id,
  b.user_level,
  a.last_login
FROM dedup a
LEFT JOIN dim_user_profile b
  ON a.user_id = b.user_id
WHERE b.dt = '${bizdate}';
