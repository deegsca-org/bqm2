#!/bin/bash

set -e
set -o nounset

cat providers.json | python parse_providers_json.py | gzip > parse_providers_json.py.json.gz

gsutil cp parse_providers_json.py.json.gz gs://input-impconfig/live/parse_providers_json.py.json.gz

