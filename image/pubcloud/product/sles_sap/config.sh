#!/bin/bash
set -eux
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Patch DMS to work with old zypper
#--------------------------------------
patch -p0 < /zypper.patch
rm -f /zypper.patch

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
systemctl enable haveged.service

#======================================
# Activate migration services
#--------------------------------------
systemctl enable suse-migration-mount-system
systemctl enable suse-migration-post-mount-system
systemctl enable suse-migration-ssh-keys
systemctl enable suse-migration-pre-checks
systemctl enable suse-migration-setup-host-network
systemctl enable suse-migration-setup-name-resolver
systemctl enable suse-migration-prepare
systemctl enable suse-migration
systemctl enable suse-migration-console-log
systemctl enable suse-migration-grub-setup
systemctl enable suse-migration-update-bootloader
systemctl enable suse-migration-product-setup
systemctl enable suse-migration-regenerate-initrd
systemctl enable suse-migration-kernel-load
systemctl enable suse-migration-reboot

# Disable password based login via ssh
sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' \
    /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' \
    /etc/ssh/sshd_config

# Remove the password for root and migration user
# Note the string matches the password set in the config file
# sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

# Setup ownership for migration user data
chown -R migration:users /home/migration
