#!/bin/bash

set -e
set -o nounset

cat campaigns.json | python parse_campaigns_json.py | gzip > parse_campaigns_json.py.json.gz

gsutil cp parse_campaigns_json.py.json.gz gs://input-impconfig/live/parse_campaigns_json.py.json.gz
