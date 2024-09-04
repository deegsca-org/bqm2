#!/bin/bash

set -e
set -o nounset

cd $(dirname $0)

# just a basic test to see if the template values respond to different command line date arguments
# check it without effective-date-as-isoformat argument
current_date=$(date +%Y%m%d) 
grep_for=foo.test_${current_date}
python -m bqm2 --defaultDataset foo --varsFile global.vars --dumpToFolder /tmp/ . | grep -q ${grep_for}

# now pass the time from command line and grep for corresponding table name in the output
python -m bqm2 --defaultDataset foo --varsFile global.vars --dumpToFolder /tmp/ . --effective-date-as-isoformat '2012-01-01' | grep -q foo.test_20120101

# now pass the time from command line and grep for corresponding table name in the output
python -m bqm2 --defaultDataset foo --varsFile global.vars --dumpToFolder /tmp/ . --effective-date-as-isoformat '2050-01-01' | grep -q foo.test_20500101
