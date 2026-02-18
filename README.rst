Distribution Migration System
=============================

.. |GitHub Action Unit Types| image:: https://github.com/SUSE/suse-migration-services/actions/workflows/ci-testing.yml/badge.svg
   :target: https://github.com/SUSE/suse-migration-services/actions
.. |SLE12to15Doc| replace:: `Documentation: SLE12-to-SLE15 <https://documentation.suse.com/suse-distribution-migration-system/15/html/distribution-migration-system/index.html>`__
.. |SLE15to16Doc| replace:: `Documentation: SLE15-to-SLE16 <https://documentation.suse.com/sles/16.0/html/SLES-upgrading/index.html#sle16-upgrade-distribution-migration-system>`__

|GitHub Action Unit Types|

**Migrate a SUSE distribution from one major version to another with the Distribution Migration System**

..  contents::
    :local:

SUSE Documentation
==================

SUSE provides several places to document the use of the Distribution Migration
System depending on the migration target. The following list shows where to
find them:

  * |SLE12to15Doc|
  * |SLE15to16Doc|

General Information
===================

The Distribution Migration System is a collection of several software packages
and images. Together they form a non interactive migration procedure which
runs in an isolated environment, either as a live system or as
an OCI container instance. The migration process inside of this
isolated environment is driven by a collection of systemd controlled
services.

All Distribution Migration System components are publicly build in a
rolling release development project at
`Public Distribution Migration System <https://build.opensuse.org/project/show/devel:DMS>`__.
Stable variants of the Distribution Migration System are provided as part of
the standard SUSE Linux Enterprise distribution maintenance cycles.

The following chapters provide information about the Distribution Migration
System with regards to the public Distribution Migration System release. It
is considered best practice to test the Distribution Migration System for
the desired operation mode and distribution target before running the process
on a production system. As such the following information and data exists to
provide guidance prior to performing the real upgrade.

Upgrade combinations of other SUSE systems like SLE-to-Leap or
to-Tumbleweed are possible and described in some of the following
test scenarios. The primary function and focus is SUSE Linux Enterprise.

Login credentials:
  The following login information applies to all local test systems:

  .. code:: bash

      root: linux

Distribution Migration System Configuration:
  Some test systems provide preconfigured setup values. The main
  Distribution Migration System configuration file is present at
  **/etc/sle-migration-service.yml**. For further information about
  configuration options please read:
  `Distribution Migration System Config <https://documentation.suse.com/suse-distribution-migration-system/15/html/distribution-migration-system/index.html#id-optional-customization-of-the-upgrade-process>`__

Offline Migration:
  The Distribution Migration System supports several operation modes. In
  offline migration mode a live migration system has to be started. This system
  is provided as a package to the user and pre installed on the test VMs. In
  production users need to install the appropriate live migration image. The
  following image packages exists:

  * SLES15-Migration
  * SLES15-SAP_Migration
  * SLES16-Migration
  * SLES16-SAP_Migration

Network Access in Offline Migration:
  In offline mode one of the Distribution Migration System services
  replicates the host system SSH configuration into the migration live system.
  As user access is granted via:

  .. code:: bash

      ssh migration@IP

Upgrade Modes:
  There are two upgrade modes supported by the **zypper** package manager.
  The **zypper dup** mode and the **zypper migration** mode. In **dup** mode
  all repositories to upgrade the system to the new target OS must be
  configured by the user prior starting the migration. This is the
  most flexible upgrade mode as any repo setup can be used for the upgrade.
  This mode also requires in depth knowledge about the current system as well
  as the target system, the installed software components and the correct
  collection of repositories such that the zypper dependency resolver can
  calculate the package updates. In **migration** mode a request to the
  repository server that the system being migrated is connected to is
  performed. On success a list of repositories is returned suitable to upgrade
  the system. This is the most simple upgrade mode and also the default.
  However, this mode only works for registered systems. Selecting between the
  two modes is done by enabling/disabling the **migration** mode.
  Enable **dup** mode in **/etc/sle-migration-service.yml** as follows:

  .. code:: bash

      use_zypper_migration: false
  
Migration Startup:
  There are three ways to perform the migration

  1. **Offline via run_migration**. This startup method requires the installation
     of one of the mentioned **XXX-Migration** migration live image packages
     which also pulls in the **run_migration** tool. **run_migration** starts the
     migration live image via **kexec** and therefore initiates the migration
     process

  2. **Offline via activation package followed by a reboot**. This startup method
     requires the installation of one of the mentioned **XXX-Migration** migration
     live image packages and the installation of the appropriate
     **suse-migration-XXX-activation** activation package. The activation
     package adds a new menu entry to the grub bootloader and makes it the
     default boot entry. On the next reboot of the system the migration
     process is initiated.

  3. **Online via migrate**. This startup methods runs in a container on the
     system to migrate. No reboot is required. The **migrate** tool will
     pull the requested migration container from the opensuse registry
     and starts a container instance via **podman** which initiates
     the migration process. The online migration falls outside the support
     conditions of SUSE Linux Enterprise. The resulting migrated system is
     supported following the SUSE support guidelines.

SLE12 >> SLE15
==============

Testing on local system (zypper dup mode)
-----------------------------------------

In this mode a local VM image based on SLE12 will be upgraded to Leap15.
The required Leap15 repositories must be configured by the user prior
starting the migration.

Repository Setup:
  Please note the test system used here comes with no repositories set.
  This is a very uncommon situation. Usually the production system has several
  repos set matching the current target. In the production system you would
  have to clear out all those repos and set a collection of repos for the new
  target system and the custom software eventually installed

To prepare for this migration call the following commands:

.. code:: bash

    wget https://download.opensuse.org/repositories/devel:/DMS/images_sle12/kiwi-test-image-disk-simple.x86_64.qcow2
    qemu-kvm \
        -m 4096 \
        -netdev user,id=user0,hostfwd=tcp::10022-:22 \
        -device virtio-net-pci,netdev=user0,mac=52:54:00:6a:40:f8 \
        -serial stdio \
    binaries/kiwi-test-image-disk-simple.x86_64.qcow2

    # Login to the system and setup the target repository

    zypper ar https://download.opensuse.org/distribution/leap/15.5/repo/oss Leap
    zypper refresh

* Upgrade in offline mode with kexec based reboot (run_migration)

    .. code:: bash

        run_migration

* Upgrade in offline mode with grub(loopback) reboot

    .. code:: bash

        zypper ar \
            https://download.opensuse.org/repositories/devel:/DMS/SLE_12_SP5 \
            Migration
        zypper install suse-migration-sle15-activation
        zypper rr Migration
        reboot

* Upgrade in online mode, container based

    .. code:: bash

        migrate \
            --use-zypper-dup \
            --migration-system registry.opensuse.org/devel/dms/containers_sle15/migration:latest \
            --reboot

Testing in the cloud (zypper migration plugin)
----------------------------------------------

In this mode a remote cloud instance in your preferred cloud service
provider needs to be started first e.g. AWS. Make sure to run a SLE12
on demand (SUSE registered) instance. The following link can be used
to run an instance of `SUSE Linux Enterprise Server 12 <https://aws.amazon.com/marketplace/pp/prodview-57pmygill5vnw>`__

To prepare for this migration call the following commands:

.. code:: bash

    # Login to the instance

    sudo zypper ar \
        https://download.opensuse.org/repositories/devel:/DMS/SLE_12_SP5 \
        Migration

* Upgrade in offline mode with kexec based reboot (run_migration)

    .. code:: bash

        sudo zypper in SLES15-Migration
        sudo zypper rr Migration
        sudo run_migration

* Upgrade in offline mode with grub(loopback) reboot

    .. code:: bash

        sudo zypper install SLES15-Migration suse-migration-sle15-activation
        sudo zypper rr Migration
        sudo reboot

* Upgrade in online mode, container based

    .. code:: bash

        sudo zypper install suse-migration
        sudo zypper rr Migration
        sudo migrate \
            --product SLES/15.5/x86_64 \
            --migration-system registry.opensuse.org/devel/dms/containers_sle15/migration:latest \
            --reboot

SLE15 >> SLE16
==============

Testing on local system (zypper dup mode)
-----------------------------------------

In this mode a local VM image based on SLE15 will be upgraded to Leap16.
The required Leap16 repositories must be configured by the user prior
starting the migration.

Repository Setup:
  Please note the test system used here comes with no repositories set.
  This is a very uncommon situation. Usually the production system has several
  repos set matching the current target. In the production system you would
  have to clear out all those repos and set a collection of repos for the new
  target system and the custom software eventually installed

To prepare for this migration call the following commands:

.. code:: bash

    wget https://download.opensuse.org/repositories/devel:/DMS/images_sle15/kiwi-test-image-disk-simple.x86_64.qcow2
    qemu-kvm \
        -cpu Broadwell-v2 \
        -m 4096 \
        -netdev user,id=user0,hostfwd=tcp::10022-:22 \
        -device virtio-net-pci,netdev=user0,mac=52:54:00:6a:40:f8 \
        -serial stdio \
    binaries/kiwi-test-image-disk-simple.x86_64.qcow2

    # Login to the system and setup the target repository

    zypper ar https://download.opensuse.org/distribution/leap/16.0/repo/oss Leap
    zypper refresh

* Upgrade in offline mode with kexec based reboot (run_migration)

    .. code:: bash

        run_migration

* Upgrade in offline mode with grub(loopback) reboot

    .. code:: bash

        zypper ar \
            https://download.opensuse.org/repositories/devel:/DMS/SLE_15_SP7 \
            Migration
        zypper install suse-migration-sle16-activation
        zypper rr Migration
        reboot

* Upgrade in online mode, container based

    .. code:: bash

        migrate \
            --use-zypper-dup \
            --migration-system registry.opensuse.org/devel/dms/containers_sle16/migration:latest \
            --reboot

Testing in the cloud (zypper migration plugin)
----------------------------------------------

In this mode a remote cloud instance in your preferred cloud service
provider needs to be started first e.g. AWS. Make sure to run a SLE15
on demand (SUSE registered) instance. The following link can be used
to run an instance of `SUSE Linux Enterprise Server 15 <https://aws.amazon.com/marketplace/pp/prodview-o5wqlcnuzvyv2>`__

To prepare for this migration call the following commands:

.. code:: bash
  
    # Login to the instance
  
    sudo zypper ar \
        https://download.opensuse.org/repositories/devel:/DMS/SLE_15_SP7 \
        Migration

* Upgrade in offline mode with kexec based reboot (run_migration)

    .. code:: bash

        sudo zypper in SLES16-Migration
        sudo zypper rr Migration
        sudo run_migration

* Upgrade in offline mode with grub(loopback) reboot

    .. code:: bash

        sudo zypper install SLES16-Migration suse-migration-sle16-activation
        sudo zypper rr Migration
        sudo reboot

* Upgrade in online mode, container based

    .. code:: bash

        sudo zypper install suse-migration
        sudo zypper rr Migration
        sudo migrate \
            --product SLES/16.0/x86_64 \
            --migration-system registry.opensuse.org/devel/dms/containers_sle16/migration:latest \
            --reboot

Contributing
============

The Python project uses `poetry` to setup a development environment
for the desired Python version. To get into a development shell
call:

.. code:: bash

    poetry shell

In order to leave the development mode just call:

.. code:: bash

    exit
