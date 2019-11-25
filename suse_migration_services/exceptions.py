# Copyright (c) 2018 SUSE Linux LLC.  All rights reserved.
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


class DistMigrationException(Exception):
    """
    Base class to handle all known exceptions.

    Specific exceptions are implemented as sub classes of DistMigrationException

    :param string message: Exception message text
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return format(self.message)


class DistMigrationCommandException(DistMigrationException):
    """
    Exception raised if an external command called via a Command
    instance has returned with an exit code != 0 or could not
    be called at all.
    """


class DistMigrationCommandNotFoundException(DistMigrationException):
    """
    Exception raised if any executable command cannot be found in
    the evironment PATH variable.
    """


class DistMigrationSystemNotFoundException(DistMigrationException):
    """
    Exception raised if no fstab file could be found on the
    existing partition nodes
    """


class DistMigrationSystemMountException(DistMigrationException):
    """
    Exception raised if a mount process in the list of
    filesystems from the fstab file has failed
    """


class DistMigrationNameResolverException(DistMigrationException):
    """
    Exception raised if the migration host system does not provide
    an /etc/resolv.conf file
    """


class DistMigrationHostNetworkException(DistMigrationException):
    """
    Exception raised if the activation of the migration host network
    failed for the reason reported by either mount or systemctl
    """


class DistMigrationZypperMetaDataException(DistMigrationException):
    """
    Exception raised if the bind mount import of the migration
    host /etc/zypp location failed
    """


class DistMigrationZypperException(DistMigrationException):
    """
    Exception raised if the zypper migration call has failed
    """


class DistMigrationGrubConfigException(DistMigrationException):
    """
    Exception raised if the grub update call has failed
    """


class DistMigrationKernelRebootException(DistMigrationException):
    """
    Exception raised if the kernel reboot call has failed
    """


class DistMigrationLoggingException(DistMigrationException):
    """
    Exception raised if the initial creation of the log file to
    store the zypper migration plugin output has failed
    """


class DistMigrationProductSetupException(DistMigrationException):
    """
    Exception raised if the syncing of the product information
    from the bind mounted etc/products.d location into the
    migrated system has failed
    """


class DistMigrationProductNotFoundException(DistMigrationException):
    """
    Exception raised if the target product to migrate is not found
    """


class DistMigrationSUSEBaseProductException(DistMigrationException):
    """
    Exception raised if the syncing of the product information
    from the bind mounted etc/products.d location into the
    migrated system has failed
    """


class DistMigrationConfigDataException(DistMigrationException):
    """
    Exception raised if the custom config file is invalid or corrupt
    """


class DistMigrationSystemNotRegisteredException(DistMigrationException):
    """
    Exception raised if the system is not registered
    """
