#!/bin/bash -x
set -e

# run script only as root
if [ $(id -u) != 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

# set proxy
export http_proxy="http://proxy-chain.intel.com:911"
export https_proxy="https://proxy-chain.intel.com:911"
export PYTHONDONTWRITEBYTECODE=1

# install required packages
apt-get update
apt-get install -y gcc python-dev python-virtualenv

if [ -z "$1" ]
then
    # create and activate virtual environment
    python3 -m venv venv
    source venv/bin/activate
fi

# install pybuilder
pip install pybuilder
if [ -z "$1" ]
then
    chmod +x venv/bin/pyb
fi

# install dependencies
# pip install -r requirements-build.txt
# pip install -r requirements.txt
pyb install_dependencies

# execute build
pyb clean
pyb -X

user="${SUDO_USER:-$USER}"
group=`groups $user | awk -F' ' '{print $3}'`
# change ownership of venv and target directories
chown -R $user:$group .coverage
if [ -z "$1" ]
then
    chown -R $user:$group venv
fi
chown -R $user:$group target
