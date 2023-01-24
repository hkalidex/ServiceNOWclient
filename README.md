![alt text](https://ubit-teamcity-iag.intel.com/app/rest/builds/buildType:%28id:AseInternal_ServiceNOWclient%29/statusIcon "TC Build Status Icon")
[![Build Status](https://fms01lxuthub01.amr.corp.intel.com/api/badges/ase-internal/ServiceNOWclient/status.svg)](https://fms01lxuthub01.amr.corp.intel.com/ase-internal/ServiceNOWclient)


## ServiceNOWclient
A Python client for ServiceNOW REST API


#### Usage
```bash
export SERVICENOW_U=USER
export SERVICENOW_P=PASSWORD
python

>>> from ServiceNOWclient import ServiceNOWclient
>>> client = ServiceNOWclient.get_ServiceNOWclient()
>>> page = client.get_physical_servers(page_size=1)
>>> print(page)
```


### Development using Docker ###

For instructions on installing Docker:
https://github.intel.com/EnterpriseDocker/docker-auto-install-scripts

Clone the repository to a directory on your development server:
```bash
cd
git clone https://github.intel.com/ase-internal/ServiceNOWclient.git
cd ServiceNOWclient
```

Build the Docker image
```bash
docker build -t servicenowclient:latest  .
```

Run the Docker image
```bash
docker run \
--rm \
-v $HOME/ServiceNOWclient:/ServiceNOWclient \
-it servicenowclient:latest \
/bin/bash
```
Note: Run the image with the source directory mounted as a volume within the container; this will allow changes to be made to the source code and have those changes reflected inside the container where they can be tested using pybuilder

Execute the build
```bash
pyb -X
```
