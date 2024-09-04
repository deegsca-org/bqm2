#!/bin/bash -x

set -eou pipefail

cd $(dirname $0)

folder=subfolder
mkdir -p $folder

cd $(dirname $0)/$folder

echo select 1 > apple.querytemplate
echo select '*' from '{dataset}.apple' > apple_depends.querytemplate

python -m bqm2 --execute . --defaultDataset ${dataset}
sleep 10

bq show --format json ${dataset}.apple_depends
bq show --format json ${dataset}.apple_depends | jq .lastModifiedTime > before
bq update --set_label foo:label_$(date +%s) ${dataset}.apple

# should not retrigger create of either apple or apple_depends
python -m bqm2 --execute . --defaultDataset ${dataset}
sleep 10

bq show --format json ${dataset}.apple_depends
bq show --format json ${dataset}.apple_depends | jq .lastModifiedTime > after

diff before after

# now wipe out apple description and apple_depends should get re-executed
bq update --description no_hash ${dataset}.apple

python -m bqm2 --execute . --defaultDataset ${dataset}

bq show --format json ${dataset}.apple_depends
bq show --format json ${dataset}.apple_depends | jq .lastModifiedTime > after_after

diff after after_after || exit 0

exit 1
