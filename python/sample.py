"""

-- Find the top 100 names from the year 2017.
CREATE TEMP TABLE top_names(name STRING)
AS
 SELECT name
 FROM `bigquery-public-data`.usa_names.usa_1910_current
 WHERE year = 2017
 ORDER BY number DESC LIMIT 100
;
-- Which names appear as words in Shakespeare's plays?
SELECT
 name AS shakespeare_name
FROM top_names
WHERE name IN (
 SELECT word
 FROM `bigquery-public-data`.samples.shakespeare
);

"""

from google.cloud.bigquery.client import Client
from google.cloud.bigquery import QueryJobConfig as QJC


