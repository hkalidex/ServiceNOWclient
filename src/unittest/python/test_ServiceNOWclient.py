
import unittest
from mock import patch
# from mock import mock_open
from mock import call
from mock import Mock
from ServiceNOWclient import ServiceNOWclient

from ServiceNOWclient.servicenowclient import filter_hardware_status
from ServiceNOWclient.servicenowclient import SERVICENOW_HOST
from ServiceNOWclient.servicenowclient import get_error_message
from ServiceNOWclient.servicenowclient import ExecutionTimeExceeded
from ServiceNOWclient.servicenowclient import retry_execution_time_exceeded

import sys
import logging
logger = logging.getLogger(__name__)

consoleHandler = logging.StreamHandler(sys.stdout)
logFormatter = logging.Formatter(
    "%(asctime)s %(threadName)s %(name)s [%(funcName)s] %(levelname)s %(message)s")
consoleHandler.setFormatter(logFormatter)
rootLogger = logging.getLogger()
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.DEBUG)


class TestServiceNOWclient(unittest.TestCase):

    def setUp(self):

        pass

    def tearDown(self):

        pass

    def test__filter_hardware_status_Should_ReturnExepcted_When_Called(self, *patches):
        data = {
            'result': [
                {
                    'child': 'item1',
                    'child.hardware_status': 'In Stock'
                }, {
                    'child': 'item2',
                    'child.hardware_status': 'Retired'
                }, {
                    'child': 'item3',
                    'child.hardware_status': 'In Use'
                }, {
                    'child': 'item4',
                    'child.hardware_status': 'In Use'
                }
            ]
        }
        result = filter_hardware_status(data, ['In Use'])
        expected_result = {
            'result': [
                {
                    'child': 'item3',
                    'child.hardware_status': 'In Use'
                }, {
                    'child': 'item4',
                    'child.hardware_status': 'In Use'
                }
            ]
        }
        self.assertEqual(result, expected_result)

    @patch('ServiceNOWclient.servicenowclient.os.environ.get', return_value=None)
    @patch('ServiceNOWclient.servicenowclient.ServiceNOWclient')
    def test__get_ServiceNOWclient_Should_SetDefaultHostname_When_HostnameNotSpecifiedAndNotInEnvironment(self, servicenowclient_patch, *patches):
        ServiceNOWclient.get_ServiceNOWclient(username='username', password='password')
        self.assertTrue(call(SERVICENOW_HOST, username='username', password='password') in servicenowclient_patch.mock_calls)

    @patch('ServiceNOWclient.servicenowclient.os.environ.get', return_value='value')
    @patch('ServiceNOWclient.servicenowclient.ServiceNOWclient')
    def test__get_ServiceNOWclient_Should_GetUsernameFromEnvironment_When_UsernameNotSpecified(self, servicenowclient_patch, *patches):
        ServiceNOWclient.get_ServiceNOWclient(hostname='hostname', password='password')
        self.assertTrue(call('hostname', username='value', password='password') in servicenowclient_patch.mock_calls)

    @patch('ServiceNOWclient.servicenowclient.os.environ.get', return_value='value')
    @patch('ServiceNOWclient.servicenowclient.ServiceNOWclient')
    def test__get_ServiceNOWclient_Should_GetPasswordFromEnvironment_When_PasswordNotSpecified(self, servicenowclient_patch, *patches):
        ServiceNOWclient.get_ServiceNOWclient(hostname='hostname', username='username')
        self.assertTrue(call('hostname', username='username', password='value') in servicenowclient_patch.mock_calls)

    @patch('ServiceNOWclient.ServiceNOWclient.get')
    def test__get_page_Should_AddOffsetAndLimitToQuery_When_Called(self, get_patch, *patches):
        client = ServiceNOWclient('hostname', username='username', password='password')
        query = '/api/now/table/cmdb_relci?sysparm_query=type.name'
        results = client.get_page(query, 100, 200)
        get_patch.assert_called_once_with('/api/now/table/cmdb_relci?sysparm_query=type.name&sysparm_offset=200&sysparm_limit=100')

    @patch('ServiceNOWclient.ServiceNOWclient.get_page')
    def test__get_all_pages_Should_ReturnExpected_When_Called(self, get_page_patch, *patches):
        get_page_patch.side_effect = [
            {
                'result': 1
            }, {
                'result': 2
            }, {
                'result': []
            }
        ]
        client = ServiceNOWclient('hostname', username='username', password='password')
        result = client.get_all_pages('query', 100)
        self.assertEqual(next(result), ({'result': 1}))
        self.assertEqual(next(result), ({'result': 2}))
        with self.assertRaises(StopIteration):
            next(result)

    @patch('ServiceNOWclient.ServiceNOWclient.get_page')
    def test__get_all_pages_Should_CallApplyFilter_When_ApplyFilterSpecified(self, get_page_patch, *patches):
        get_page_patch.side_effect = [
            {
                'result': 1
            }, {
                'result': 2
            }, {
                'result': []
            }
        ]
        client = ServiceNOWclient('hostname', username='username', password='password')
        filter_mock = Mock()
        filter_mock.return_value = 'filtered result'
        result = client.get_all_pages('query', 100, apply_filter=filter_mock, arg1='arg1', arg2='arg2')
        self.assertEqual(next(result), ('filtered result'))
        filter_mock.assert_called_with({'result': 1}, arg1='arg1', arg2='arg2')

    @patch('ServiceNOWclient.ServiceNOWclient.get_all_pages')
    def test__get_physical_hardware_Should_CallExepcted_When_Called(self, get_all_pages_patch, *patches):
        client = ServiceNOWclient('hostname', username='username', password='password')
        result = client.get_physical_hardware()
        self.assertEqual(result, get_all_pages_patch.return_value)

    def test__get_error_message_Should_ReturnExpected_When_ResponseJson(self, *patches):
        response_mock = Mock()
        response_mock.json.return_value = {
            'error': {
                'message': 'this is the error message'
            }
        }
        result = get_error_message(response_mock)
        self.assertEqual(result, response_mock.json.return_value['error']['message'])

    def test__get_error_message_Should_ReturnExpected_When_ResponseNotJson(self, *patches):
        response_mock = Mock()
        response_mock.text = 'this is the error message'
        response_mock.json.side_effect = [
            ValueError
        ]
        result = get_error_message(response_mock)
        self.assertEqual(result, response_mock.text)

    def test__retry_execution_time_exceeded_Should_ReturnTrue_When_ExecptionIsExecutionTimeExceeded(self, *patches):
        exception_mock = ExecutionTimeExceeded()
        self.assertTrue(retry_execution_time_exceeded(exception_mock))

    def test__retry_execution_time_exceeded_Should_ReturnFalse_When_ExecptionIsNotExecutionTimeExceeded(self, *patches):
        exception_mock = ValueError()
        self.assertFalse(retry_execution_time_exceeded(exception_mock))

    @patch('ServiceNOWclient.servicenowclient.get_error_message')
    def test__process_response_Should_RaiseExecutionTimeExceeded_When_ExecutionTimExceededInErrorMessage(self, get_error_message_patch, *patches):
        get_error_message_patch.return_value = 'com.glide.sys.TransactionCancelledException: Transaction cancelled: maximum execution time exceeded'
        response_mock = Mock()
        response_mock.ok = False
        client = ServiceNOWclient('hostname', username='username', password='password')
        with self.assertRaises(ExecutionTimeExceeded):
            client.process_response(response_mock)

    @patch('ServiceNOWclient.servicenowclient.get_error_message')
    def test__process_response_Should_CallRaiseForStatus_When_ExecutionTimExceededNotInErrorMessage(self, get_error_message_patch, *patches):
        get_error_message_patch.return_value = 'some error happened'
        response_mock = Mock()
        response_mock.ok = False
        client = ServiceNOWclient('hostname', username='username', password='password')
        client.process_response(response_mock)
        response_mock.raise_for_status.assert_called_once_with()

    def test__process_response_Should_ReturnExpected_When_ResponseJson(self, *patches):
        response_mock = Mock()
        response_mock.ok = True
        response_mock.json.return_value = {}
        client = ServiceNOWclient('hostname', username='username', password='password')
        result = client.process_response(response_mock)
        self.assertEqual(result, response_mock.json.return_value)

    def test__process_response_Should_ReturnExpected_When_ResponseNotJson(self, *patches):
        response_mock = Mock()
        response_mock.ok = True
        response_mock.json.side_effect = [
            ValueError
        ]
        client = ServiceNOWclient('hostname', username='username', password='password')
        result = client.process_response(response_mock)
        self.assertEqual(result, response_mock)
