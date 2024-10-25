Testing on local system (zypper dup mode)
=========================================

Run SLE12 test image (simple disk layout)
-----------------------------------------

.. code:: bash

   osc getbinaries home:marcus.schaefer:dms suse-migration-test-vm images_sle12 x86_64
   qemu-kvm \
       -m 4096 \
       -netdev user,id=user0,hostfwd=tcp::10022-:22 \
       -device virtio-net-pci,netdev=user0,mac=52:54:00:6a:40:f8 \
       -serial stdio \
   binaries/kiwi-test-image-disk-simple*.qcow2
   zypper ar https://download.opensuse.org/distribution/leap/15.5/repo/oss Leap
   zypper refresh

1. Testing in offline mode with kexec based reboot (run_migration)

   .. code:: bash

      run_migration

2. Testing in offline mode with grub(loopback) reboot

   .. code:: bash

      # Add repo for testing DMS activation:
      zypper ar https://download.opensuse.org/repositories/home:/marcus.schaefer:/dms/SLE_12_SP5 Migration
      zypper install suse-migration-sle15-activation
      zypper rr Migration
      reboot

3. [Optional] Testing in online upgrade mode (not officially supported by SUSE)

   .. code:: bash

      migrate --use-zypper-dup --reboot

4. Testing more complex disk layouts

   - Change suse-migration-test-vm to build different layouts
     e.g. with LVM, with btrfs, etc etc and repeat steps 1-1.2
   - Also test settings possible in `/etc/sle-migration-service.yml`


Testing in the cloud (zypper migration plugin)
==============================================

Run SLE12 on demand instance in some cloud e.g. AWS
and add repo for testing DMS activation

.. code:: bash

   zypper ar https://download.opensuse.org/repositories/home:/marcus.schaefer:/dms/SLE_12_SP5 Migration


1. Testing with kexec based reboot (run_migration)

   .. code:: bash

      sudo zypper in SLES15-Migration
      run_migration

2. Testing with grub(loopback) reboot

   .. code:: bash

      sudo zypper install SLES15-Migration suse-migration-sle15-activation
      reboot

3. [Optional] Testing in online upgrade mode (not officially supported by SUSE):

   .. code:: bash

      sudo zypper install suse-migration
      sudo migrate --product SLES/15.5/x86_64 --reboot

