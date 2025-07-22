#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : KIWI - Image System
# COPYRIGHT     : (c) 2023 SUSE Software Solutions Germany GmbH
#               :
# AUTHORS       : Marcus Schaefer <ms@suse.de>
#               : Keith Berger <kberger@suse.com>
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : configuration script for SUSE based
#               : operating systems
#----------------
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
suseRemoveService guestregister

# disable and mask lvmetad
systemctl disable lvm2-lvmetad.socket
systemctl disable lvm2-lvmetad.service
systemctl mask lvm2-lvmetad.socket
systemctl mask lvm2-lvmetad.service

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService haveged

#======================================
# Activate migration services
#--------------------------------------
suseInsertService suse-migration-mount-system
suseInsertService suse-migration-post-mount-system
suseInsertService suse-migration-ssh-keys
suseInsertService suse-migration-pre-checks
suseInsertService suse-migration-setup-host-network
suseInsertService suse-migration-setup-name-resolver
suseInsertService suse-migration-prepare
suseInsertService suse-migration
suseInsertService suse-migration-console-log
suseInsertService suse-migration-grub-setup
suseInsertService suse-migration-update-bootloader
suseInsertService suse-migration-product-setup
suseInsertService suse-migration-regenerate-initrd
suseInsertService suse-migration-kernel-load
suseInsertService suse-migration-reboot

# Disable password based login via ssh
sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' \
    /etc/ssh/sshd_config

# Remove the password for root and migration user
# Note the string matches the password set in the config file
# FIXME: The line below must be active on production
# sed -i 's/$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0/*/' /etc/shadow

# Setup ownership for migration user data
chown -R migration:users /home/migration
