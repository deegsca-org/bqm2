#FROM docker.io/stops/tf-muse-v3-lg:245d9bf016 as tf-muse

#FROM docker.io/stops/go-cloud-copy:98d373f20f as go-cloud-copy
#FROM docker.io/stops/go-sharethis:989d79a0b6 as go-sharethis


FROM python:3.6
# /go-cloud-copy is a utility for sending receiving and sending messages from 
# either stdin, stdout, or sqs queues. all combinations are supported.
# we may start using it in bqm2 for send sqs messages to get data into gcs
#COPY --from=go-cloud-copy /go-cloud-copy /go-cloud-copy

# this is used to generate embeddings within bqm2 apps if needed.  See bq-customer-filters app
#COPY --from=tf-muse /app/models/muse/004/ /app/models/muse/004/

# we include an encrypt/decrypt utility for hems
#COPY --from=go-sharethis /bin/crypt-util/main /go-sharethis/bin/crypt-util/main

RUN apt-get install -y g++
RUN pip install --upgrade pip
ADD /python /python
RUN pip install -r /python/requirements.txt
ENV PYTHONPATH /python
RUN apt-get update
RUN apt-get install -y vim jq unzip
ADD /root /root

## aws client
RUN apt-get install graphviz -y

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get install apt-transport-https ca-certificates -y
RUN apt-get update -y
RUN apt-get install google-cloud-sdk -y

ADD /test /test
RUN /test/test.sh
