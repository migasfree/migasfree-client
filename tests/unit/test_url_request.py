# -*- coding: utf-8 -*-

"""
Unit tests for migasfree_client.url_request module
"""

import errno
import json
import requests
import responses
from unittest.mock import patch, MagicMock

from migasfree_client.url_request import UrlRequest


class TestUrlRequestInitialization:
    """Tests for UrlRequest initialization"""

    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        url_req = UrlRequest()
        assert url_req._debug is False
        assert url_req._proxy == ''
        assert url_req._cert is False

    def test_init_with_debug(self):
        """Test initialization with debug enabled"""
        url_req = UrlRequest(debug=True)
        assert url_req._debug is True

    def test_init_with_proxy(self):
        """Test initialization with proxy"""
        proxy = 'http://proxy.example.com:8080'
        url_req = UrlRequest(proxy=proxy)
        assert url_req._proxy == proxy

    def test_init_with_keys(self):
        """Test initialization with encryption keys"""
        keys = {'private': '/path/to/private.pem', 'public': '/path/to/public.pem'}
        url_req = UrlRequest(keys=keys)
        assert url_req._private_key == '/path/to/private.pem'
        assert url_req._public_key == '/path/to/public.pem'

    def test_init_with_cert(self):
        """Test initialization with SSL certificate"""
        cert_path = '/path/to/cert.pem'
        url_req = UrlRequest(cert=cert_path)
        assert url_req._cert == cert_path

    def test_init_with_project(self):
        """Test initialization with project name"""
        url_req = UrlRequest(project='test-project')
        assert url_req._project == 'test-project'


class TestHttpRequests:
    """Tests for HTTP request operations"""

    @responses.activate
    def test_run_successful_request(self):
        """Test successful HTTP POST request"""
        url = 'http://example.com/api/endpoint'
        response_data = {'status': 'ok', 'message': 'Success'}

        responses.add(responses.POST, url + '/', json=response_data, status=200)

        url_req = UrlRequest()
        result = url_req.run(url, data='test data', safe=False)

        assert result == response_data

    @responses.activate
    def test_run_adds_trailing_slash(self):
        """Test that run() adds trailing slash to URL"""
        url = 'http://example.com/api/endpoint'

        responses.add(responses.POST, url + '/', json={'status': 'ok'}, status=200)

        url_req = UrlRequest()
        url_req.run(url, safe=False)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url + '/'

    @responses.activate
    def test_run_with_json_data(self):
        """Test request with JSON data"""
        url = 'http://example.com/api/endpoint'
        data = {'key': 'value', 'number': 123}

        responses.add(responses.POST, url + '/', json={'received': True}, status=200)

        url_req = UrlRequest()
        url_req.run(url, data=json.dumps(data), safe=False)

        # Verify request was made
        assert len(responses.calls) == 1

    @responses.activate
    def test_run_with_proxy(self):
        """Test request with proxy configuration"""
        url = 'http://example.com/api/endpoint'
        proxy = 'http://proxy.example.com:8080'

        responses.add(responses.POST, url + '/', json={'status': 'ok'}, status=200)

        url_req = UrlRequest(proxy=proxy)
        result = url_req.run(url, safe=False)

        assert result == {'status': 'ok'}

    @responses.activate
    def test_run_sets_user_agent(self):
        """Test that request sets custom user-agent"""
        url = 'http://example.com/api/endpoint'

        responses.add(responses.POST, url + '/', json={'status': 'ok'}, status=200)

        url_req = UrlRequest()
        url_req.run(url, safe=False)

        request = responses.calls[0].request
        assert 'migasfree-client' in request.headers['user-agent']


class TestErrorHandling:
    """Tests for error handling"""

    @responses.activate
    def test_run_connection_error(self):
        """Test handling of connection error"""
        url = 'http://example.com/api/endpoint'

        # We must use requests.exceptions.ConnectionError
        responses.add(
            responses.POST,
            url + '/',
            body=requests.exceptions.ConnectionError('Connection failed'),
        )

        url_req = UrlRequest()
        result = url_req.run(url, safe=False, exit_on_error=False)

        assert 'error' in result
        assert result['error']['code'] == errno.ECONNREFUSED

    @responses.activate
    def test_run_timeout_error(self):
        """Test handling of timeout error"""
        url = 'http://example.com/api/endpoint'

        # responses library doesn't directly support timeout simulation
        # We'll mock the requests.post to raise ReadTimeout
        with patch('requests.post') as mock_post:
            from requests.exceptions import ReadTimeout

            mock_post.side_effect = ReadTimeout('Request timed out')

            url_req = UrlRequest()
            result = url_req.run(url, safe=False, exit_on_error=False)

            assert 'error' in result
            assert result['error']['code'] == errno.ETIMEDOUT

    @responses.activate
    def test_run_http_404_error(self):
        """Test handling of 404 error"""
        url = 'http://example.com/api/endpoint'

        responses.add(responses.POST, url + '/', json={'error': 'Not found'}, status=404)

        url_req = UrlRequest()
        result = url_req.run(url, safe=False, exit_on_error=False)

        assert 'error' in result
        assert result['error']['code'] == 404

    @responses.activate
    def test_run_http_500_error(self):
        """Test handling of 500 server error"""
        url = 'http://example.com/api/endpoint'

        responses.add(
            responses.POST,
            url + '/',
            json={'error': 'Internal server error'},
            status=500,
        )

        url_req = UrlRequest()
        result = url_req.run(url, safe=False, exit_on_error=False)

        assert 'error' in result
        assert result['error']['code'] == 500

    @responses.activate
    def test_run_http_401_unauthorized(self):
        """Test handling of 401 unauthorized error"""
        url = 'http://example.com/api/endpoint'

        responses.add(responses.POST, url + '/', json={'error': 'Unauthorized'}, status=401)

        url_req = UrlRequest()
        result = url_req.run(url, safe=False, exit_on_error=False)

        assert 'error' in result
        assert result['error']['code'] == 401


class TestSafeRequests:
    """Tests for encrypted/safe requests"""

    @responses.activate
    @patch('migasfree_client.url_request.wrap')
    @patch('migasfree_client.url_request.unwrap')
    def test_run_safe_request(self, mock_unwrap, mock_wrap):
        """Test safe (encrypted) request"""
        url = 'http://example.com/api/endpoint'
        data = {'message': 'secret'}
        wrapped_data = 'encrypted_data_here'
        response_data = {'msg': 'encrypted_response'}

        mock_wrap.return_value = wrapped_data
        mock_unwrap.return_value = {'status': 'ok'}

        responses.add(responses.POST, url + '/', json=response_data, status=200)

        keys = {'private': '/path/to/private.pem', 'public': '/path/to/public.pem'}
        url_req = UrlRequest(keys=keys, project='test')
        url_req.run(url, data=data, safe=True, exit_on_error=False)

        # Verify wrap was called
        mock_wrap.assert_called_once()
        # Verify unwrap was called with response
        mock_unwrap.assert_called_once()

    @responses.activate
    def test_run_safe_sets_content_type_json(self, private_key_path, public_key_path):
        """Test that safe request sets content-type to application/json"""
        url = 'http://example.com/api/endpoint'

        responses.add(responses.POST, url + '/', json={'msg': 'response'}, status=200)

        keys = {'private': private_key_path, 'public': public_key_path}

        with patch('migasfree_client.url_request.wrap', return_value='encrypted'):
            url_req = UrlRequest(keys=keys, project='test')
            url_req.run(url, data={'test': 'data'}, safe=True, exit_on_error=False)

            request = responses.calls[0].request
            assert request.headers['content-type'] == 'application/json'


class TestFileUpload:
    """Tests for file upload functionality"""

    @responses.activate
    @patch('migasfree_client.url_request.read_file')
    @patch('migasfree_client.url_request.build_magic')
    @patch('migasfree_client.url_request.write_file')
    @patch('os.remove')
    def test_run_with_file_upload(self, mock_remove, mock_write, mock_magic, mock_read):
        """Test request with file upload"""
        url = 'http://example.com/api/upload'
        file_path = '/tmp/test_file.txt'
        file_content = b'file content here'

        mock_read.return_value = file_content
        mock_magic_instance = MagicMock()
        mock_magic_instance.file.return_value = 'text/plain'
        mock_magic.return_value = mock_magic_instance

        responses.add(responses.POST, url + '/', json={'uploaded': True}, status=200)

        url_req = UrlRequest()
        # Must pass data as dict for file upload to work with update()
        result = url_req.run(url, data={}, upload_files=[file_path], safe=False, exit_on_error=False)

        # Verify file was read
        mock_read.assert_called_once_with(file_path)
        assert result == {'uploaded': True}


class TestResponseProcessing:
    """Tests for response processing"""

    @responses.activate
    def test_evaluate_response_json(self):
        """Test evaluating JSON response"""
        url = 'http://example.com/api/endpoint'
        response_data = {'key': 'value', 'number': 42}

        responses.add(responses.POST, url + '/', json=response_data, status=200)

        url_req = UrlRequest()
        result = url_req.run(url, safe=False)

        assert result == response_data

    @responses.activate
    @patch('migasfree_client.url_request.unwrap')
    def test_evaluate_response_safe(self, mock_unwrap):
        """Test evaluating safe/encrypted response"""
        url = 'http://example.com/api/endpoint'
        decrypted_data = {'decrypted': 'data'}

        mock_unwrap.return_value = decrypted_data

        responses.add(responses.POST, url + '/', json={'msg': 'encrypted_message'}, status=200)

        keys = {'private': '/path/to/private.pem', 'public': '/path/to/public.pem'}

        with patch('migasfree_client.url_request.wrap', return_value='encrypted'):
            url_req = UrlRequest(keys=keys, project='test')
            result = url_req.run(url, data={}, safe=True, exit_on_error=False)

            assert result == decrypted_data


class TestUtilityMethods:
    """Tests for utility methods"""

    @patch('os.path.exists', return_value=False)
    @patch('os.makedirs')
    def test_check_tmp_path_creates_directory(self, mock_makedirs, mock_exists):
        """Test _check_tmp_path creates directory if it doesn't exist"""
        result = UrlRequest._check_tmp_path()

        mock_makedirs.assert_called_once()
        assert result is True

    @patch('os.path.exists', return_value=True)
    def test_check_tmp_path_exists(self, mock_exists):
        """Test _check_tmp_path when directory already exists"""
        result = UrlRequest._check_tmp_path()

        assert result is True

    @patch('os.path.exists', return_value=False)
    @patch('os.makedirs', side_effect=OSError('Permission denied'))
    def test_check_tmp_path_fails(self, mock_makedirs, mock_exists):
        """Test _check_tmp_path returns False on error"""
        result = UrlRequest._check_tmp_path()

        assert result is False
