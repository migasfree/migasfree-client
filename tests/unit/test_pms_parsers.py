# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import unittest
from unittest.mock import patch

from migasfree_client.pms.apt import Apt
from migasfree_client.pms.wpt import Wpt
from migasfree_client.pms.yum import Yum


class TestPmsParsers(unittest.TestCase):
    def test_apt_query_all_parser(self):
        """Test Apt.query_all parses dpkg --list output correctly"""
        apt = Apt()
        dpkg_output = """Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version      Architecture Description
+++-==============-============-============-=================================
ii  bash           5.2.15-2     amd64        GNU Bourne Again SHell
ii  curl           7.88.1-10    amd64        command line tool for transferring
ii  python3        3.11.2-1     all          interactive high-level object-orie
"""
        with patch('migasfree_client.pms.apt.execute', return_value=(0, dpkg_output, '')):
            result = apt.query_all()

        expected = ['bash_5.2.15-2_amd64.deb', 'curl_7.88.1-10_amd64.deb', 'python3_3.11.2-1_all.deb']
        self.assertEqual(result, expected)

    def test_yum_available_packages_parser(self):
        """Test Yum.available_packages parses yum list available output"""
        yum = Yum()
        yum_output = """Loaded plugins: fastestmirror
Available Packages
bash.x86_64                            4.4.20-4.el7_9                  updates
curl.x86_64                            7.29.0-59.el7_9.1               updates
custom-pkg.noarch                      1.0-1                           local
"""
        with patch('migasfree_client.pms.yum.execute', return_value=(0, yum_output, '')):
            result = yum.available_packages()

        expected = ['bash', 'curl', 'custom-pkg']
        self.assertEqual(result, expected)

    def test_wpt_query_all_parser(self):
        """Test Wpt.query_all parses wpt list output"""
        wpt = Wpt()
        wpt_output = """chrome_120.0.6099.110_x64
firefox_121.0_x64
vscode_1.85.1_x64
"""
        with patch('migasfree_client.pms.wpt.execute', return_value=(0, wpt_output, '')):
            result = wpt.query_all()

        expected = ['chrome_120.0.6099.110_x64.tar.gz', 'firefox_121.0_x64.tar.gz', 'vscode_1.85.1_x64.tar.gz']
        self.assertEqual(result, expected)

    def test_apt_version_parser(self):
        """Test Apt._get_pms_version parses apt --version output"""
        apt = Apt()

        # Test modern version
        with patch('migasfree_client.pms.apt.execute', return_value=(0, 'apt 2.9.21 (amd64)', '')):
            self.assertEqual(apt._get_pms_version(), (2, 9, 21))

        # Test old version format
        with patch('migasfree_client.pms.apt.execute', return_value=(0, 'apt 1.8.2.3 (amd64)', '')):
            self.assertEqual(apt._get_pms_version(), (1, 8, 2))

        # Test failure/unknown
        with patch('migasfree_client.pms.apt.execute', return_value=(1, '', '')):
            self.assertEqual(apt._get_pms_version(), (2, 0))


if __name__ == '__main__':
    unittest.main()
