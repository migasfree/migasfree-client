# Copyright (c) 2011-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

from .data import (
    _bytes_to_str,
    cast_to_bool,
    compare_lists,
    escape_quotes,
    get_config,
    grep,
    remove_commented_lines,
    sanitize_path,
)
from .fs import (
    build_magic,
    compare_files,
    md5sum,
    read_file,
    remove_file,
    write_file,
    write_file_if_changed,
)
from .mfc import (
    check_lock_file,
    get_hardware_uuid,
    get_mfc_computer_name,
    get_mfc_project,
    get_mfc_release,
    get_smbios_version,
    get_trait,
    get_uuid_from_mac,
    migrate_legacy_server_config,
    process_is_active,
    trait_value_exists,
)
from .process import (
    ALL_OK,
    _create_subprocess,
    _kill_process,
    _stream_output_nonblocking,
    demote,
    execute,
    timeout_execute,
)
from .session import (
    execute_as_user,
    get_current_user,
    get_graphic_pid,
    get_graphic_user,
    get_user_display_graphic,
    is_xsession,
    is_zenity,
    query_yes_no,
)
from .system import (
    get_distro_name,
    get_distro_project,
    get_hostname,
    get_user_info,
    is_linux,
    is_root_user,
    is_windows,
    slugify,
)
