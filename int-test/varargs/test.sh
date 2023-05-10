#!/bin/bash

# test design to check assertions and specifically the empty non empty row based approach

set -e
set -o nounset

cd $(dirname $0)
testfile=testvarfile
echo -n 'value' > $testfile

# basic unadorned invocation ensures nothing prevents our users from seeing the usage
python -u -m bqm2 > /dev/null 2>&1


# now we kick the tires a little bit with --var command line option which allows 
# arbitrary key.val to be delivered via command line to app
python -u -m bqm2 --var project=dummyproject --var list='["a"]' --var nested='[{"a":"c"}, {"a": "d"}]' --var val=file:$testfile --var dataset=testdataset --print-global-args | jq . > list.actual
diff list.actual list.expected

python -u -m bqm2 --var yyyymmdd=20220101 --var project=dummyproject --var nested='[{"a":"c","b":"bval"}, {"a": "d","b":"bval2"}]' --var list='["a", "b", "c"]' --var val=file:$testfile --var dataset=testdataset --dumpToFolder /tmp . ./local > dependencies.actual
diff dependencies.actual dependencies.expected

python -u -m bqm2 --var yyyymmdd=20220101 --var project=${project} --var nested='[{"a":"c","b":"bval"}, {"a":"d","b":"bval2"}]' --var list='["a", "b", "c"]' --var val=file:$testfile --var dataset=${dataset} --execute . local
