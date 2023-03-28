#!/bin/bash

set -e
set -o nounset

cd $(dirname $0)

. env.sh

python -u -m bqm2 --defaultProject $PROJECT --defaultDataset $DEFAULT_DATASET --dumpToFolder /tmp/ .
