import os
from retrying import retry
from RESTclient import RESTclient

import logging
logger = logging.getLogger(__name__)

logging.getLogger('urllib3.connectionpool').setLevel(logging.CRITICAL)


SERVICENOW_HOST = 'e2esm.intel.com'


class ExecutionTimeExceeded(Exception):
    """ ExecutionTimeExceeded
    """
    pass


def filter_hardware_status(data, hardware_status=[]):
    """ return filtered records
        temporary method to workaround serviceNOW query bug not respecting filter on hardware status

        Args:
            data (dict): original data set
            hardware_status (str): hardware status
        Returns:
            dict: filtered data set
    """
    filtered_data = {
        'result': []
    }
    for item in data['result']:
        if item['child.hardware_status'] not in hardware_status:
            logger.debug('skipping "{}" because hardware status "{}" not in "{}"'.format(item['child'], item['child.hardware_status'], ','.join(hardware_status)))
            continue
        filtered_data['result'].append(item)
    return filtered_data


def filter_physical_servers_in_use(data):
    """ return filtered records
        temporary method to workaround serviceNOW query bug not respecting filter on hardware status or virtual

        Args:
            data (dict): original data set
        Returns:
            dict: filtered data set
    """
    filtered_data = {
        'result': []
    }
    for item in data['result']:
        if item['child.hardware_status'].lower() != 'in use':
            logger.debug('skipping "{}" because hardware status "{}" not "In Use"'.format(item['child'], item['child.hardware_status']))
            continue
        if item['child.virtual'].lower() != 'false':
            logger.debug('skipping "{}" because virtual "{}" not "false"'.format(item['child'], item['child.virtual']))
            continue
        filtered_data['result'].append(item)
    return filtered_data


def get_error_message(response):
    """ get error
    """
    try:
        error = response.json()
        return error.get('error', {}).get('message', '')
    except ValueError:
        return response.text


def retry_execution_time_exceeded(exception):
    """ return True if exception is ExecutionTimeExceeded
    """
    logger.debug('checking exception for retry candidacy')
    if isinstance(exception, ExecutionTimeExceeded):
        logger.debug('{} - retrying in a few seconds'.format(str(exception)))
        return True
    return False


class ServiceNOWclient(RESTclient):

    def __init__(self, hostname, **kwargs):
        """ class constructor

            Args:
                kwargs (dict): arbritrary number of key word arguments

            Returns:
                ServiceNOWclient: instance of ServiceNOWclient
        """
        logger.debug('executing ServiceNOWclient constructor')
        super(ServiceNOWclient, self).__init__(hostname, **kwargs)

    @retry(retry_on_exception=retry_execution_time_exceeded, wait_random_min=20000, wait_random_max=40000, stop_max_attempt_number=3)
    def get_page(self, query, limit, offset):
        """ get page
        """
        endpoint = query.split('?')[0]
        query += '&sysparm_offset={}'.format(offset)
        query += '&sysparm_limit={}'.format(limit)
        logger.debug('retrieving page from endpoint {} with offset {} and limit {}'.format(endpoint, offset, limit))
        page = self.get(query)
        logger.debug('retrieved {} page from endpoint {} with offset {} and limit {}'.format(len(page.get('result', [])), endpoint, offset, limit))
        return page

    def get_all_pages(self, query, limit, apply_filter=None, **kwargs):
        """ get all pages
        """
        endpoint = query.split('?')[0]
        logger.debug('retrieving all pages from endpoint {}'.format(endpoint))
        offset = 0
        while True:
            page = self.get_page(query, limit, offset)
            if page and page['result']:
                logger.debug('page result detected - yielding')
                if apply_filter:
                    filtered_page = apply_filter(page, **kwargs)
                    yield filtered_page
                else:
                    yield page
                offset = offset + limit + 1
            else:
                logger.debug('page result not detected - exiting')
                break
        logger.debug('retrieved all pages from endpoint {}'.format(endpoint))

    def get_physical_hardware(self, page_size=1000, hardware_status=['In Use']):
        """ get physical hardware records
        """
        logger.debug('retrieving physical hardware records using page size {} and hardware status {}'.format(page_size, hardware_status))
        query = (
            '/api/now/table/cmdb_rel_ci'
                '?sysparm_query='
                    'type.name%3DAllocated%20to%3A%3AAllocated%20from'
                    '%5Echild.model_id.nameNOT%20LIKEvirtual'
                    '%5Echild.sys_class_nameINSTANCEOFcmdb_ci_server'
                    '%5Eparent.sys_class_nameINSTANCEOFu_service_application'
                    '%5Echild.hardware_status%3DIn Use'
                    '%5Eu_support_serviceNOT%20LIKEdesign'
                    '%5Eu_support_service!%3D91401c92ff308d4c8193dc8c3a6d0e6e'
                    '%5EORu_support_service%3DNULL'
                    '%5Eu_support_service!%3Dbdd45892558a52000221ce673d64e498'
                    '%5EORu_support_service%3DNULL'
                    '%5EORDERBYchild.sys_id'
                '&sysparm_fields='
                    'child,'
                    'child.sys_id,'
                    'child.assigned_to,'
                    'child.assigned_to.user_name,'
                    'child.hardware_status,'
                    'child.ip_address,'
                    'child.cpu_name,'
                    'child.os,'
                    'child.model_id,'
                    'child.cpu_count,'
                    'child.ram,'
                    'child.disk_space,'
                    'parent.ref_u_service_application.u_software_product.u_iap_application_id,'
                    'child.sys_class_name,'
                    'parent.sys_class_name'
                '&sysparm_exclude_reference_link=true'
                '&sysparm_display_value=true')
        return self.get_all_pages(query, page_size, apply_filter=filter_hardware_status, hardware_status=hardware_status)

    def get_physical_servers(self, page_size=10):
        """ get physical servers
        """
        logger.debug('retrieving physical server records using page size {}'.format(page_size))
        query = (
            '/api/now/table/cmdb_rel_ci'
                '?sysparm_query='
                    'type.name=Allocated to::Allocated from'
                    '^child.sys_class_nameINSTANCEOFcmdb_ci_server'
                    '^parent.sys_class_nameINSTANCEOFu_service_application'
                    '^child.model_id.nameNOT LIKEvirtual'
                    '^child.hardware_status=In Use'
                    '^ORDERBYchild.sys_id'
                '&sysparm_fields='
                    'child,'
                    'child.sys_id,'
                    'child.virtual,'
                    'child.assigned_to,'
                    'child.assigned_to.user_name,'
                    'child.hardware_status,'
                    'child.ip_address,'
                    'child.cpu_name,'
                    'child.os,'
                    'child.model_id.name,'
                    'child.cpu_count,'
                    'child.ram,'
                    'child.disk_space,'
                    'parent.ref_u_service_application.u_software_product.u_iap_application_id,'
                    'child.sys_class_name,'
                    'parent.sys_class_name'
                '&sysparm_exclude_reference_link=true'
                '&sysparm_display_value=true')

        return self.get_all_pages(query, page_size, apply_filter=filter_physical_servers_in_use)

    @classmethod
    def get_ServiceNOWclient(cls, hostname=None, username=None, password=None):
        """ return instance of ServiceNOWclient

            Args:
                hostname (str): the host and endpoint for the PAAS REST API
                api_key (str): the PAAS REST API key

            Returns:
                ServiceNOWclient: instance of ServiceNOWclient
        """
        if not hostname:
            hostname = os.environ.get('SERVICENOW_H')
            if not hostname:
                hostname = SERVICENOW_HOST

        return ServiceNOWclient(
            hostname,
            username=username if username else os.environ.get('SERVICENOW_U'),
            password=password if password else os.environ.get('SERVICENOW_P'))

    def process_response(self, response, **kwargs):
        """ process request response - override
        """
        if not response.ok:
            error_message = get_error_message(response)
            logger.error(error_message)
            if 'maximum execution time exceeded' in error_message:
                raise ExecutionTimeExceeded(error_message)
            response.raise_for_status()

        try:
            return response.json()

        except ValueError:
            return response
