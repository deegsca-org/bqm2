#!/bin/bash

set -e -o nounset

cd $(dirname $0)

python -m bqm2 --dumpToFolder /tmp . --defaultDataset=foo --defaultProject=bar > dump.txt


diff dump.txt dump.txt.expected
diff /tmp/foo.join_table.debug foo.join_table.debug.expected
diff /tmp/foo.join_view.debug foo.join_view.debug.expected

python -m bqm2 --execute . --defaultDataset=${dataset} --defaultProject=${project}

