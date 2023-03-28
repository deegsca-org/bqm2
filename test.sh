#!/bin/bash

set -e 
set -o nounset

echo executing pytest
pytest --cov --cov-branch --cov-report term-missing -vv -s src/
echo finished pytest

echo executing pycodestyle
pycodestyle --max-line-length=100 src/ --exclude='src/test_*'
echo finished pycodestyle
