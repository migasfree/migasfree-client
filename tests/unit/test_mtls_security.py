import os
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from migasfree_client.mtls import import_mtls_certificate


class TestMtlsSecurity(unittest.TestCase):
    def test_import_mtls_certificate_tar_slip(self):
        # Create a malicious tar file with a path traversal member
        with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_tar:
            tar_path = tmp_tar.name

        try:
            with tarfile.open(tar_path, 'w') as tar, tempfile.NamedTemporaryFile(delete=True):
                # Create a file that tries to escape the extraction directory
                # Note: we use a name that starts with '../'
                info = tarfile.TarInfo(name='../../../../tmp/malicious.p12')
                info.size = 0
                tar.addfile(info)

            with patch('migasfree_client.mtls.MTLS_PATH', tempfile.gettempdir()):
                # Try to import it
                result = import_mtls_certificate(tar_path, 'test_server')

            # It should fail with the traversal message
            self.assertFalse(result['success'])
            self.assertEqual(result['message'], 'Possible path traversal attack in tar file')

        finally:
            if os.path.exists(tar_path):
                os.unlink(tar_path)


if __name__ == '__main__':
    unittest.main()
