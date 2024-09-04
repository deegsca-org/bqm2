#!/bin/bash

set -e -o nounset

export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token)

echo 'select 1' > test_oauth.querytemplate
echo '- is_script: true' > test_oauth_extract.querytemplate.vars
cat <<EOF > test_oauth_extract.querytemplate
export data options (
  uri='gs://{project}-bqm2-int-test/{dataset}/{table}/test-oauth*.csv',
  overwrite=True,
  format='CSV',
  header=False,
  field_delimiter='\000'
) as
select * from {project}.{dataset}.test_oauth;
create table {project}.{dataset}.{table} (dummy int);
EOF


python -m bqm2 --dumpToFolder /tmp . --defaultDataset=${dataset} --defaultProject=${project}
python -m bqm2 --execute . --defaultDataset=${dataset} --defaultProject=${project}
