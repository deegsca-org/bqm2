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
-v ~/Downloads/eyeota-test-37d40f8af2b4.json:/gcloud-private-key \
-v ~/.vimrc:/root/.vimrc \
-v ${QUERIES}:${MOUNT} \
--name bqm2 -v ~/.config:/root/.config \
-v $(pwd)/python:/python \
-v $(pwd)/test:/test \
-v $(pwd)/int-test:/int-test \
-v ~/.aws:/root/.aws \
-ti --rm $imagename:$current_commit $@
