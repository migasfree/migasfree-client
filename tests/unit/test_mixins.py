import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.mixins.evaluator import CodeEvaluatorMixin
from migasfree_client.mixins.hardware import HardwareCollectorMixin
from migasfree_client.mixins.software import SoftwareManagerMixin


class MockBase:
    def __init__(self):
        self._computer_id = '123'
        self.migas_computer_name = 'test-pc'
        self._graphic_user = 'root'
        self.console = MagicMock()
        self.console.status.return_value.__enter__.return_value = None
        self._url_request = MagicMock()
        self._debug = False
        self.URLS = {'get_hardware_required': 'hr', 'upload_hardware': 'uh', 'evaluate': 'ev', 'upload_software': 'us'}
        self.pms = MagicMock()

    def api_endpoint(self, url):
        return url

    def operation_failed(self, msg):
        pass

    def operation_ok(self, msg=None):
        pass

    def _show_message(self, msg):
        pass

    def _report_error(self, msg):
        pass

    def _write_error(self, msg):
        pass

    def _check_pms(self):
        pass

    def _api_call(self, m, d):
        return {'status': 'ok'}

    def _handle_response(self, r):
        return r


class TestHardwareCollectorMixin(unittest.TestCase):
    def setUp(self):
        class Comp(MockBase, HardwareCollectorMixin):
            def __init__(self):
                MockBase.__init__(self)

        self.comp = Comp()

    def test_hardware_capture_is_required(self):
        self.comp._url_request.run.return_value = {'capture': True}
        res = self.comp.hardware_capture_is_required()
        self.assertTrue(res)


class TestCodeEvaluatorMixin(unittest.TestCase):
    def setUp(self):
        class Comp(MockBase, CodeEvaluatorMixin):
            def __init__(self):
                MockBase.__init__(self)

        self.comp = Comp()

    @patch('migasfree_client.utils.timeout_execute')
    @patch('migasfree_client.utils.write_file')
    @patch('os.remove')
    def test_eval_attributes(self, mock_remove, mock_write, mock_execute):
        mock_execute.return_value = (0, 'result', '')
        props = [{'prefix': 'P1', 'language': 'bash', 'code': 'echo 1'}]
        with patch('migasfree_client.network.get_network_info', return_value={'ip': '1.1.1.1'}), patch(
            'migasfree_client.utils.get_user_info', return_value={'fullname': 'Full Name'}
        ):
            res = self.comp._eval_attributes(props)
            self.assertEqual(res['sync_attributes']['P1'], 'result')


class TestSoftwareManagerMixin(unittest.TestCase):
    def setUp(self):
        class Comp(MockBase, SoftwareManagerMixin):
            def __init__(self):
                MockBase.__init__(self)

        self.comp = Comp()

    def test_upload_software(self):
        self.comp.pms.query_all.return_value = ['pkg1']
        with patch('migasfree_client.utils.write_file'), patch('migasfree_client.utils.compare_lists', return_value=[]):
            self.comp.upload_software([], {})
            self.comp.pms.query_all.assert_called()


if __name__ == '__main__':
    unittest.main()
