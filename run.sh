#!/bin/bash

set -e

cd $(dirname $0)

. env.sh

docker build -t $imagename:$current_commit .

#if [ -z $SRC_DIR ]; then
#  echo "Must specify SRC_DIR. Path where a user's git repos are present."
#  exit 1;
#fi
#echo "SRC: $SRC_DIR"

if [[ ! -f ~/.aws/mfa ]]
then
    echo Please make you have a valid mfa credentials file
    exit 1
fi
#SECRET=${SECRET:-k8app__bq-third-party__staging__bqm2-json__gcloud-private-key}
# get creds
#mkdir -p /tmp/creds
#docker run -ti -v ~/.aws:/root/.aws -v /tmp/creds:/tmp/creds -e AWS_SHARED_CREDENTIALS_FILE=/root/.aws/mfa -e AWS_DEFAULT_REGION=us-east-1 docker.io/stops/secrets-manager-v2:5b20bdefaa python /src/client.py ${SECRET} /tmp/creds/gcloud-private-key


if [[ ! -f ~/.vimrc ]]
then
    touch ~/.vimrc
fi

docker run -e GOOGLE_APPLICATION_CREDENTIALS=/gcloud-private-key \
-e AWS_SHARED_CREDENTIALS_FILE=/root/.aws/mfa \
-v ~/Downloads/eyeota-test-37d40f8af2b4.json:/gcloud-private-key \
-v ~/.vimrc:/root/.vimrc \
--name bqm2 -v ~/.config:/root/.config \
-v $(pwd)/python:/python \
-v $(pwd)/test:/test \
-v $(pwd)/queries:/queries \
-v $(pwd)/int-test:/int-test \
-v ~/.aws:/root/.aws \
-ti --rm $imagename:$current_commit $@
