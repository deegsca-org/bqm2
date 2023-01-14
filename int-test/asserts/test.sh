#!/bin/bash

# test design to check assertions and specifically the empty non empty row based approach

set -e
set -o nounset

cd $(dirname $0)
testfile=empty_table.localdata
echo > $testfile

python /python/bqm2.py --defaultDataset ${dataset} --execute . --maxRetry=1

for row in 1 2 3
do
    echo $row >> ${testfile}
done

# unset auto exit on error
set +e
python /python/bqm2.py --defaultDataset ${dataset} --execute . --maxRetry=1 

[ $? != 0 ]

echo For the second invocation of bqm2, we received an error.  That is expected.
