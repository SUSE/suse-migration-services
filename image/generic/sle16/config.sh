#!/bin/bash

set -eux

#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#======================================
# Setup default target, multi-user
#--------------------------------------
baseSetRunlevel 3

#======================================
# Deactivate services
#--------------------------------------
# cloud-regionsrv-client packages(s) activates that service
# on install. For migration we don't need this service.
# The installation of that packages and its relatives happens
# to satisfy the dependencies on the zypper plugin side but
# not for actually registering a guest to the public cloud
# infrastructure. We expect that step to be already done
systemctl disable guestregister.service

# disable and mask lvmetad
systemctl disable lvm2-lvmetad.socket
systemctl disable lvm2-lvmetad.service
systemctl mask lvm2-lvmetad.socket
systemctl mask lvm2-lvmetad.service

#======================================
# Activate services
#--------------------------------------
systemctl enable sshd.service
#======================================
# Activate migration services
#--------------------------------------
systemctl enable suse-migration-mount-system.service
systemctl enable suse-migration-apparmor-selinux.service
systemctl enable suse-migration-post-mount-system.service
systemctl enable suse-migration-btrfs-snapshot-pre-migration.service
systemctl enable suse-migration-btrfs-snapshot-post-migration.service
systemctl enable suse-migration-ssh-keys
systemctl enable suse-migration-pre-checks.service
systemctl enable suse-migration-setup-host-network.service
systemctl enable suse-migration-setup-name-resolver.service
systemctl enable suse-migration-prepare.service
systemctl enable suse-migration.service
systemctl enable suse-migration-console-log.service
systemctl enable suse-migration-grub-setup.service
systemctl enable suse-migration-update-bootloader.service
systemctl enable suse-migration-product-setup.service
systemctl enable suse-migration-regenerate-initrd.service
systemctl enable suse-migration-kernel-load.service
systemctl enable suse-migration-wicked-networkmanager.service
systemctl enable suse-migration-ha.service
systemctl enable suse-migration-reboot.service
systemctl enable NetworkManager.service
# needed for network setup migration
mkdir -p /etc/sysconfig/network/providers

# Remove the password for root and migration user
# Note the string matches the password set in the config file
# FIXME: The line below must be active on production
# sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

# Setup ownership for migration user data
chown -R migration:users /home/migration

# Add s390 specific network rules to migration config
if [ "$(arch)" = "s390x" ]; then
    mkdir -p /etc/migration-config.d
    cat <<EOF > /etc/migration-config.d/50-s390x.yml
preserve:
  rules:
    - /etc/udev/rules.d/*qeth*.rules
    - /etc/udev/rules.d/*-cio-ignore*.rules
EOF
fi
