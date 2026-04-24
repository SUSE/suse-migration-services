# Copyright (c) 2026 SUSE Linux LLC.  All rights reserved.
#
# This file is part of suse-migration-services.
#
# suse-migration-services is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# suse-migration-services is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with suse-migration-services. If not, see <http://www.gnu.org/licenses/>
#
import hashlib
import logging
import os
import shutil
import re
from datetime import datetime

log = logging.getLogger('ResolvConf')


class ResolvConf:
    """
    **Managing /etc/resolv.conf **
    """

    def __init__(self, target_root, src_dir, dest_dir=None):
        self.target_root = target_root
        self.src_dir = src_dir
        self.dest_dir = dest_dir if dest_dir else src_dir

    def prepare_resolv_conf(self):
        resolv_conf = os.path.normpath(os.path.join(self.src_dir, 'resolv.conf'))
        resolv_conf_dest = os.path.normpath(os.path.join(self.dest_dir, 'resolv.conf'))

        if (os.path.islink(resolv_conf)):
            resolv_realpath = self.resolve_chroot_symlink(resolv_conf, self.target_root)
            if not resolv_realpath:
                log.warning("Failed to resolv link {} with root:{}".format(
                    resolv_conf, self.target_root)
                )
            elif resolv_realpath.endswith('/netconfig/resolv.conf'):
                if os.path.lexists(resolv_conf_dest):
                    log.info('Delete link {} -> netconfig/resolv.conf'.format(resolv_conf_dest))
                    os.unlink(resolv_conf_dest)
            elif resolv_realpath.endswith('/NetworkManager/resolv.conf'):
                if os.path.lexists(resolv_conf_dest):
                    log.info('Delete link {} -> NetworkManager/resolv.conf'.format(resolv_conf_dest))
                    os.unlink(resolv_conf_dest)

            # If src_dir and dest_dir are equal, nothing to do, as links already work.
            # Otherwise, we are likely in the live-iso so lets get the link target.
            elif (self.src_dir != self.dest_dir):
                # custom link we are trying to preserve it, if target exists
                if self.is_custom_resolv_conf(resolv_realpath):
                    self.copy(resolv_realpath, resolv_conf_dest)
                    self.create_static_resolv()

        else:
            if self.is_custom_resolv_conf(resolv_conf):
                self.copy(resolv_conf, resolv_conf_dest)
                self.create_static_resolv()

    def copy(self, src, dst):
        if src == dst:
            return
        if os.path.islink(dst):
            os.unlink(dst)
        shutil.copy(src, dst)

    def create_static_resolv(self):
        # Create a symlink to custom resolv.conf, ensure it will not
        # be overwritten by NetworkManager/netconfig
        previous_dir = os.getcwd()
        os.chdir(self.dest_dir)
        resolv_static = 'resolv.conf.static'
        if os.path.exists('resolv.conf.static'):
            resolv_static += datetime.now().strftime('-%Y-%m-%d-%H%M')
        log.info('Create symlink /etc/resolv.conf -> {}'.format(resolv_static))
        shutil.move('resolv.conf', resolv_static)
        os.symlink(resolv_static, 'resolv.conf')
        os.chdir(previous_dir)

    def read_netconfig_md5(self):
        md5_file = os.path.join(
            self.target_root, 'var/adm/netconfig/md5/etc/resolv.conf')
        if os.path.exists(md5_file):
            with open(md5_file, 'r') as f:
                match = re.search(
                    r'^#([^\n\r]*)\r?\n([0-9a-fA-F]{32})',
                    f.read(),
                    re.MULTILINE
                )
                if match:
                    return match.group(2), match.group(1)
        return None, None

    def create_netconfig_md5(self, file_path, erx):
        if not os.path.exists(file_path) or not erx:
            return None
        filtered_content = ""
        with open(file_path, 'r') as f:
            for line in f:
                # from functions.netconfig::_read_erx_data()
                # { if(length(erx) && match($0, erx) > 0) { print $0; next; } }
                # !/^#|^[[:space:]]*$/     { print $0; }
                if erx and re.search(erx, line):
                    filtered_content += line.rstrip('\n') + '\n'
                    continue
                if not re.match(r'^#|^\s*$', line):
                    filtered_content += line.rstrip('\n') + '\n'
        return hashlib.md5(filtered_content.encode()).hexdigest()

    def is_custom_resolv_conf(self, file):
        if not os.path.exists(file):
            return False

        # On sle12 netconfig check via md5sum if the resolv.conf is
        # customized.
        netconfig_md5, erx = self.read_netconfig_md5()
        if netconfig_md5:
            if netconfig_md5 == self.create_netconfig_md5(file, erx):
                return False

        with open(file, 'r') as resolv:
            for line in resolv:
                # check if it contains "Generated by NetworkManager"
                if line.startswith('# Generated by NetworkManager'):
                    return False

                # check if there are nameservers configured
                elif line.lstrip().startswith('nameserver'):
                    return True
        return False

    def resolve_chroot_symlink(self, symlink_path, new_root):
        """
        Resolves a symlink to its path within a new root directory.
        It follow symlinks even if they are broken.
        """
        symlink_path = os.path.abspath(symlink_path)
        new_root = os.path.abspath(new_root)

        if not os.path.islink(symlink_path):
            raise ValueError(f"'{symlink_path}' is not a valid symlink.")

        target = os.readlink(symlink_path)

        if os.path.isabs(target):
            target_stripped = target.lstrip(os.sep)
            resolved_path = os.path.join(new_root, target_stripped)
        else:
            symlink_dir = os.path.dirname(symlink_path)
            raw_joined_path = os.path.join(symlink_dir, target)
            resolved_path = os.path.normpath(raw_joined_path)
            if os.path.commonpath([new_root, resolved_path]) != new_root:
                return None

        if os.path.islink(resolved_path):
            return self.resolve_chroot_symlink(resolved_path, new_root)
        return resolved_path
