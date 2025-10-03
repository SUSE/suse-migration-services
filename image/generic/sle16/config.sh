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

# optimize iso size (based from Agama live image)

# remove the GPU drivers, not needed when running in text mode only,
# the related firmware is deleted by the script below
rm -rf /usr/lib/modules/*/kernel/drivers/gpu

# remove Bluetooth drivers
rm -rf /usr/lib/modules/*/kernel/drivers/bluetooth
rm -rf /usr/lib/modules/*/kernel/net/bluetooth

# Clean-up logs
rm /var/log/zypper.log /var/log/zypp/history

du -h -s /usr/{share,lib}/locale/

# keep the en_US translations
ls -1 -I en -I en_US -I "C.utf8" /usr/share/locale/ | xargs -I% sh -c "echo 'Removing translations %...' && rm -rf /usr/share/locale/%"

# delete locale definitions for unsupported languages (explicitly keep the C and en_US locales)
ls -1 -I "en_US.utf8" -I "C.utf8" /usr/lib/locale/ | xargs -I% sh -c "echo 'Removing locale %...' && rm -rf /usr/lib/locale/%"

# delete unused translations (MO files)
for t in Linux-PAM e2fsprogs gawk gettext-runtime grub2 iputils kbd libgpg-error mit-krb5 p11-kit pam-config rpm shadow.mo sudo sudoers xfsprogs zypp zypper; do
  rm -f /usr/share/locale/*/LC_MESSAGES/$t.mo
done
du -h -s /usr/{share,lib}/locale/

# remove documentation
du -h -s /usr/share/doc/packages/
rm -rf /usr/share/doc/packages/*
# remove man pages
du -h -s /usr/share/man
rm -rf /usr/share/man/*

# remove unused SUSEConnect libzypp plugins
rm -f /usr/lib/zypper/commands/zypper-search-packages

## removing drivers and firmware makes the Live ISO smaller

# driver and firmware cleanup
# Note: openSUSE Tumbleweed Live completely removes firmware for some server
# network cars, because you very likely won't run TW KDE Live on a server.
# But for Agama installer it makes more sense to run on server. So we keep it
# and remove the drivers for sound cards and TV cards instead. Those do not
# make sense on a server.
du -h -s /lib/modules /lib/firmware

# delete sound drivers
#rm -rfv /lib/modules/*/kernel/sound
# delete TV cards and radio cards
#rm -rfv /lib/modules/*/kernel/drivers/media/

# (need to port those scripts to python)
# remove the multimedia drivers 
# set DEBUG=1 to print the deleted drivers
/tmp/driver_cleanup.py --delete
# remove the script and data, not needed anymore
rm /tmp/driver_cleanup.py /tmp/module.list*

# remove the unused firmware (not referenced by kernel drivers)
/tmp/fw_cleanup.py --delete
# remove the script, not needed anymore
rm /tmp/fw_cleanup.py
du -h -s /lib/modules /lib/firmware

################################################################################
# The rest of the file was copied from the openSUSE Tumbleweed Live ISO
# https://build.opensuse.org/projects/openSUSE:Factory:Live/packages/livecd-tumbleweed-kde/files/config.sh?expand=1
#

# Stronger compression for the initrd
echo 'compress="xz -9 --check=crc32 --memlimit-compress=50%"' >> /etc/dracut.conf.d/less-storage.conf

# Kernel modules (+ firmware) for X13s
if [ "$(arch)" == "aarch64" ]; then
	echo 'add_drivers+=" clk-rpmh dispcc-sc8280xp gcc-sc8280xp gpucc-sc8280xp nvmem_qcom-spmi-sdam qcom_hwspinlock qcom_q6v5 qcom_q6v5_pas qnoc-sc8280xp pmic_glink pmic_glink_altmode smp2p spmi-pmic-arb leds-qcom-lpg "'  > /etc/dracut.conf.d/x13s_modules.conf
	echo 'add_drivers+=" nvme phy_qcom_qmp_pcie pcie-qcom-ep i2c_hid_of i2c_qcom_geni leds-qcom-lpg pwm_bl qrtr pmic_glink_altmode gpio_sbu_mux phy_qcom_qmp_combo panel-edp msm phy_qcom_edp "' >> /etc/dracut.conf.d/x13s_modules.conf
	echo 'install_items+=" /lib/firmware/qcom/sc8280xp/LENOVO/21BX/qcadsp8280.mbn.xz /lib/firmware/qcom/sc8280xp/LENOVO/21BX/qccdsp8280.mbn.xz "' >> /etc/dracut.conf.d/x13s_modules.conf
fi

# delete some AMD GPU firmware
rm -rf /lib/firmware/amdgpu/{gc_,isp,psp}*

# Decompress kernel modules, better for squashfs (boo#1192457)
find /lib/modules/*/kernel -name '*.ko.xz' -exec xz -d {} +
find /lib/modules/*/kernel -name '*.ko.zst' -exec zstd --rm -d {} +
for moddir in /lib/modules/*; do
  depmod "$(basename "$moddir")"
done

# the new, optional nvidia gsp firmware blobs are huge - ~ 70MB
if [ -e /lib/firmware/nvidia ]; then
  du -h -s /lib/firmware/nvidia
  find /lib/firmware/nvidia -name gsp | xargs -r rm -rf
  du -h -s /lib/firmware/nvidia
fi

# Not needed, boo#1166406
rm -f /boot/vmlinux*.[gx]z
rm -f /lib/modules/*/vmlinux*.[gx]z

# Remove generated files (boo#1098535)
rm -rf /var/cache/zypp/* /var/lib/zypp/AnonymousUniqueId /var/lib/systemd/random-seed
