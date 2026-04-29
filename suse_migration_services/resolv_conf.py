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

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults

log = logging.getLogger(Defaults.get_migration_log_name())


class ResolvConf:
    """
    ** Managing /etc/resolv.conf during migration **
    """

    def __init__(self):
        self.root_path = Defaults.get_system_root_path()

    def setup_target_root(self):
        """
        Setup etc/resolv.conf in the target /system-root.
         * if it's a link to netconfig or NetworkManager it will be deleted
         * if it customized it will be moved to a static file and symlinked,
           to prevent dns resolvers to overwrite it.
        """
        conf = os.path.normpath(os.path.join(self.root_path, 'etc/resolv.conf'))
        if (os.path.islink(conf)):
            link_target = self.readlink_chroot()

            if not link_target:
                log.warning("Failed to resolv link {} with root:{}".format(
                    conf, self.root_path)
                )
            elif link_target.endswith('/netconfig/resolv.conf'):
                log.info('Delete link {} -> netconfig/resolv.conf'.format(conf))
                os.unlink(conf)
            elif link_target.endswith('/NetworkManager/resolv.conf'):
                log.info('Delete link {} -> NetworkManager/resolv.conf'.format(conf))
                os.unlink(conf)
        else:
            if self.is_custom_resolv_conf(conf):
                self.create_static_resolv(self.root_path)

    def setup_live_system(self, dest_root='/'):
        """
        Setup /etc/resolv.conf in the live system (host).

        This method identifies if the resolver configuration in the migration
        source is customized. If so, it preserves that configuration on the
        live system by creating a static resolv.conf.

        :param dest_root: The root directory where etc/resolv.conf should be
                         configured. Defaults to '/' for the live system.
        """
        src = os.path.normpath(os.path.join(self.root_path, 'etc/resolv.conf'))
        dest = os.path.normpath(os.path.join(dest_root, 'etc/resolv.conf'))

        if (os.path.islink(src)):
            link_target = self.readlink_chroot()

            if not link_target:
                log.warning("Failed to resolv link {} with root:{}".format(
                    src, self.root_path)
                )
            else:
                if self.is_custom_resolv_conf(link_target):
                    Command.run(['cp', '--remove-destination', link_target, dest])
                    self.create_static_resolv(dest_root)
        else:
            if self.is_custom_resolv_conf(src):
                Command.run(['cp', '--remove-destination', src, dest])
                self.create_static_resolv(dest_root)

    def create_static_resolv(self, root_dir):
        # Create a symlink to custom resolv.conf, ensure it will not
        # be overwritten by NetworkManager/netconfig
        previous_dir = os.getcwd()
        os.chdir(os.path.join(root_dir, 'etc'))
        resolv_static = 'resolv.conf.static'
        if os.path.exists('resolv.conf.static'):
            resolv_static += datetime.now().strftime('-%Y-%m-%d-%H%M')
        log.info('Create symlink /etc/resolv.conf -> {}'.format(resolv_static))
        shutil.move('resolv.conf', resolv_static)
        os.symlink(resolv_static, 'resolv.conf')
        os.chdir(previous_dir)

    def read_netconfig_md5(self):
        md5_file = os.path.join(
            self.root_path, 'var/adm/netconfig/md5/etc/resolv.conf')
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

    def generate_netconfig_md5(self, file, erx):
        if not os.path.exists(file) or not erx:
            return None
        filtered_content = ""
        with open(file, 'r') as f:
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

        # On sle12, netconfig checks via md5sum if the resolv.conf is
        # customized.
        netconfig_md5, erx = self.read_netconfig_md5()
        if netconfig_md5:
            md5_2 = self.generate_netconfig_md5(file, erx)
            if netconfig_md5 == md5_2:
                return False

        with open(file, 'r') as resolv:
            for line in resolv:
                # check if it contains "Generated by NetworkManager"
                if line.startswith('# Generated by NetworkManager'):
                    return False
        return True

    def readlink_chroot(self):
        """
        Resolves a symlink to its path within a new root directory.
        It follow symlinks even if they are broken.
        """

        output = Command.run(
            ['chroot', self.root_path, 'readlink', '-m', '/etc/resolv.conf']
        ).output.strip()

        if len(output) == 0:
            return None

        return os.path.join(self.root_path, output.lstrip('/'))
