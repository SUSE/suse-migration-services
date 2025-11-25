
import os
import subprocess
import tempfile
import unittest
from unittest import mock


class RunMigrationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = self.temp_dir_obj.name
        self.addCleanup(self.temp_dir_obj.cleanup)

        # Create a fake kexec script
        self.kexec_path = os.path.join(self.temp_dir, 'kexec')
        self.kexec_out = os.path.join(self.temp_dir, 'kexec.out')
        with open(self.kexec_path, 'w') as f:
            f.write(f'#!/bin/sh\necho "$@" > {self.kexec_out}\n')
        os.chmod(self.kexec_path, 0o755)

        # Create other fake commands
        self.create_fake_command('systemctl')
        self.create_fake_command('lsblk', stdout='dev/vda1 /')
        self.create_fake_command('findmnt', stdout='some-uuid')
        self.create_fake_command('mdadm', exit_code=1)  # Don't detect raid
        self.create_fake_command('xargs', stdout='')  # no extra boot options
        self.create_fake_command('mount')
        self.create_fake_command('umount')
        self.create_fake_command('mktemp', stdout=f'{self.temp_dir}/boot')
        self.create_fake_command('cp')
        self.create_fake_command('rm')
        self.create_fake_command('zypper', stdout='x86_64_v2')
        self.create_fake_command('wicked')
        self.create_fake_command('udevadm')
        self.create_fake_command('snapper')

        # Create a fake migration ISO
        iso_dir = os.path.join(self.temp_dir, 'migration-image')
        os.makedirs(iso_dir)
        self.iso_path = os.path.join(iso_dir, 'SLE-15-SP4-x86_64-Migration.iso')
        with open(self.iso_path, 'w') as f:
            f.write('fake iso content')

        # Create fake boot files
        boot_dir = os.path.join(self.temp_dir, 'boot', 'boot', 'x86_64', 'loader')
        os.makedirs(boot_dir)
        with open(os.path.join(boot_dir, 'linux'), 'w') as f:
            f.write('kernel')
        with open(os.path.join(boot_dir, 'initrd'), 'w') as f:
            f.write('initrd')

        # Fake /proc/cmdline
        self.proc_cmdline = os.path.join(self.temp_dir, 'proc_cmdline')
        with open(self.proc_cmdline, 'w') as f:
            f.write('BOOT_IMAGE=/boot/vmlinuz-5.14.21-150400.24.66-default root=UUID=xxxx quiet')

        self.env = os.environ.copy()
        self.env['PATH'] = f'{self.temp_dir}:{self.env["PATH"]}'
        self.env['EUID'] = '0'

    def create_fake_command(self, name, stdout='', exit_code=0):
        cmd_path = os.path.join(self.temp_dir, name)
        with open(cmd_path, 'w') as f:
            f.write('#!/bin/sh\n')
            f.write(f'echo "{stdout}"\n')
            f.write(f'exit {exit_code}\n')
        os.chmod(cmd_path, 0o755)

    @mock.patch('os.geteuid', return_value=0)
    def test_no_automated_reboot_flag(self, mock_geteuid):
        """Test that --no-automated-reboot adds migration.noreboot to kexec."""
        # The script is a bash script, so we can't easily mock dependencies
        # without a lot of work. Instead we execute it as a subprocess and
        # provide fake commands on the PATH.

        # Path to the script to test
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'run_migration'))

        # Create a modified script for testing
        with open(script_path) as f:
            original_script = f.read()

        modified_script = original_script
        modified_script = modified_script.replace(
            'migration_iso=$(get_migration_image)',
            f'migration_iso="{self.iso_path}"'
        )
        modified_script = modified_script.replace(
            'boot_dir=$(extract_kernel_and_initrd "${migration_iso}")',
            f'boot_dir="{self.temp_dir}/boot"'
        )
        modified_script = modified_script.replace(
            '< /proc/cmdline',
            f'< {self.proc_cmdline}'
        )

        test_script_path = os.path.join(self.temp_dir, 'run_migration_test')
        with open(test_script_path, 'w') as f:
            f.write(modified_script)
        os.chmod(test_script_path, 0o755)

        # Run the script with the flag
        subprocess.run(
            [test_script_path, '--no-automated-reboot'],
            env=self.env,
            check=True
        )

        # Check the arguments passed to our fake kexec
        with open(self.kexec_out) as f:
            kexec_args = f.read()

        self.assertIn('migration.noreboot', kexec_args)


if __name__ == '__main__':
    unittest.main()
