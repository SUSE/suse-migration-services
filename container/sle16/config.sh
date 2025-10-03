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

# needed for network setup migration
mkdir -p /etc/sysconfig/network/providers

#======================================
# Activate migration services
#--------------------------------------
for service in \
    suse-migration-container.service \
    suse-migration-container-prepare.service \
    suse-migration-container-product-setup.service \
    suse-migration-container-reboot.service \
    suse-migration-container-grub-setup.service \
    suse-migration-container-apparmor-selinux.service \
    suse-migration-container-btrfs-snapshot-pre-migration.service \
    suse-migration-container-btrfs-snapshot-post-migration.service \
    suse-migration-container-regenerate-initrd.service \
    suse-migration-container-wicked-networkmanager.service \
    suse-migration-container-ha.service
do
    systemctl enable "${service}"
done

#======================================
# Udev rules
#--------------------------------------
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
