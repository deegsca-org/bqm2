FROM python:3.10

RUN apt-get install -y g++
RUN pip install --upgrade pip
ADD /requirements.txt /
RUN pip install -r /requirements.txt
ENV PYTHONPATH /src
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

ADD /src /src
ADD /int-test /int-test
ADD /test.sh /test.sh

RUN /test.sh
