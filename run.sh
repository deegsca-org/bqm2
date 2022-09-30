#!/bin/bash

set -e
set -o nounset

cd $(dirname $0)

. env.sh

docker build -t $imagename:$current_commit .

if [[ ! -f ~/.vimrc ]]
then
    touch ~/.vimrc
fi

echo mounting ${QUERIES} to ${MOUNT}
docker run -e GOOGLE_APPLICATION_CREDENTIALS=/gcloud-private-key \
-e AWS_SHARED_CREDENTIALS_FILE=/root/.aws/mfa \
-v ${GOOGLE_APPLICATION_SERVICE_ACCOUNT}:/gcloud-private-key \
-v ~/.vimrc:/root/.vimrc \
-v ${QUERIES}:${MOUNT} \
--name bqm2 \
-v $(pwd)/python:/python \
-v $(pwd)/test:/test \
-v $(pwd)/int-test:/int-test \
-v ~/.aws:/root/.aws \
-ti --rm $imagename:$current_commit $@
