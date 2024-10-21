#!/bin/bash
set -ex

#======================================
# Autologin
#--------------------------------------
mkdir -p /etc/systemd/system/console-getty.service.d
cat >> /etc/systemd/system/console-getty.service.d/override.conf <<- EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear --keep-baud 115200,38400,9600 console linux
EOF

#======================================
# Create host OS shared mount path
#--------------------------------------
mkdir -p /system-root

#======================================
# Activate migration services
#--------------------------------------
for service in \
    suse-migration-container.service \
    suse-migration-container-prepare.service \
    suse-migration-container-product-setup.service \
    suse-migration-container-reboot.service
do
    systemctl enable "${service}"
done
