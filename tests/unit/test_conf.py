import os
import tempfile

from migasfree_client.conf import MigasFreeConf


class TestMigasFreeConf:
    def setup_method(self):
        self.cmd = MigasFreeConf()

    def test_validate_server(self):
        assert self.cmd._validate_value('Server', 'migasfree.org') is True
        assert self.cmd._validate_value('Server', 'https://migasfree.org:443') is True
        assert self.cmd._validate_value('Server', 'http://migasfree.org') is True
        assert self.cmd._validate_value('Server', '') is False

    def test_validate_project(self):
        assert self.cmd._validate_value('Project', 'MIGASFREE') is True
        assert self.cmd._validate_value('Project', 'my-project.1') is True
        assert self.cmd._validate_value('Project', '') is False
        assert self.cmd._validate_value('Project', 'invalid project') is False

    def test_validate_computer_name(self):
        assert self.cmd._validate_value('Computer_Name', 'mcs-builder') is True
        assert self.cmd._validate_value('Computer_Name', 'my-pc.1') is True
        assert self.cmd._validate_value('Computer_Name', '') is True  # Empty to reset/disable
        assert self.cmd._validate_value('Computer_Name', 'invalid name') is False

    def test_validate_proxy(self):
        assert self.cmd._validate_value('Proxy', '') is True  # empty is valid (disables proxy)
        assert self.cmd._validate_value('Proxy', '192.168.1.1:3128') is True
        assert self.cmd._validate_value('Proxy', 'proxy.example.com:8080') is True
        assert self.cmd._validate_value('Proxy', 'http://proxy') is False
        assert self.cmd._validate_value('Proxy', 'proxy.example.com:70000') is False
        assert self.cmd._validate_value('Proxy', 'proxy.example.com') is False

    def test_set_config_value_new_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            conf_file = tf.name

        try:
            # File exists but is empty
            self.cmd._set_config_value(conf_file, 'client', 'Server', 'migasfree.org')
            with open(conf_file, encoding='utf-8') as f:
                content = f.read()
            assert '[client]' in content
            assert 'Server = migasfree.org' in content
        finally:
            os.unlink(conf_file)

    def test_set_config_value_existing_key(self):
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tf:
            tf.write('[client]\n# comment\nServer = old.org\nProject = OLD\n')
            conf_file = tf.name

        try:
            self.cmd._set_config_value(conf_file, 'client', 'Server', 'new.org')
            with open(conf_file, encoding='utf-8') as f:
                content = f.read()
            assert 'Server = new.org' in content
            assert 'Server = old.org' not in content
            assert '# comment' in content
            assert 'Project = OLD' in content
        finally:
            os.unlink(conf_file)

    def test_set_config_value_commented_key(self):
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tf:
            tf.write('[client]\n# Debug = True\nProject = OLD\n')
            conf_file = tf.name

        try:
            self.cmd._set_config_value(conf_file, 'client', 'Debug', 'False')
            with open(conf_file, encoding='utf-8') as f:
                content = f.read()
            assert '# Debug = True\nDebug = False' in content
            assert 'Project = OLD' in content
        finally:
            os.unlink(conf_file)

    def test_set_config_value_append_key(self):
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tf:
            tf.write('[client]\nServer = migasfree.org\n')
            conf_file = tf.name

        try:
            self.cmd._set_config_value(conf_file, 'client', 'Project', 'NEW_PROJECT')
            with open(conf_file, encoding='utf-8') as f:
                content = f.read()
            assert 'Server = migasfree.org' in content
            assert 'Project = NEW_PROJECT' in content
        finally:
            os.unlink(conf_file)

    def test_set_config_value_reset_key(self):
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tf:
            tf.write('[client]\nServer = migasfree.org\nComputer_Name = my-custom-pc\n')
            conf_file = tf.name

        try:
            self.cmd._set_config_value(conf_file, 'client', 'Computer_Name', '')
            with open(conf_file, encoding='utf-8') as f:
                content = f.read()
            assert 'Server = migasfree.org' in content
            assert '# Computer_Name = my-custom-pc' in content
            assert content == '[client]\nServer = migasfree.org\n# Computer_Name = my-custom-pc\n'
        finally:
            os.unlink(conf_file)
