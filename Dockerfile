FROM python:3.6.5-stretch

ENV http_proxy http://proxy-chain.intel.com:911
ENV https_proxy http://proxy-chain.intel.com:911

RUN mkdir /ServiceNOWclient

COPY dockerfiles /ServiceNOWclient/dockerfiles

RUN mkdir -p /etc/ssl/certs
RUN cp /ServiceNOWclient/dockerfiles/cabundle.pem /etc/ssl/certs/cabundle.pem

WORKDIR /ServiceNOWclient

RUN cp dockerfiles/apt.conf /etc/apt/apt.conf
RUN apt-get update
RUN apt-get install -y wget git python-dev gcc python-virtualenv

COPY . /ServiceNOWclient/

RUN pip install pybuilder
RUN pyb install_dependencies
RUN pyb clean
RUN pyb install

# Unset the proxy variables because it actually causes more problems than it solves.
# In the event that you need to use the proxy, specify it in-line with docker run --env http_proxy=http://proxy-chain.intel.com:911
# Or use no_proxy if you have know all the intranet subnets you'll be accessing.

ENV http_proxy=
ENV https_proxy=

WORKDIR /ServiceNOWclient
CMD pyb -X
