#!/usr/bin/env python3

# This script removes unused firmware files (not referenced by any kernel
# driver) from the system. By default the script runs in safe mode and only
# lists the unused firmware file, use the "--delete" argument to delete the
# found files.

import os
import sys
import glob
import subprocess

def resolve_symlinks(path, fw_dir):
    """
    Find all symlinks until the final file is found. If a file is passed,
    the file only is returned.
    Returns a list of files/symlinks.
    """
    ret = [path]
    current_path = path

    while os.path.islink(current_path):
        # Do not use os.path.realpath as it skips all intermediate symlinks
        target = os.readlink(current_path)
        # os.path.join handles if target is absolute
        abs_target = os.path.abspath(os.path.join(os.path.dirname(current_path), target))

        # A cycle or a broken link is detected, or the link points outside
        # of the firmware directory
        if abs_target in ret or not os.path.exists(abs_target) or not abs_target.startswith(fw_dir):
            break

        print(f"Adding symlink {current_path.removeprefix(fw_dir)} -> {target} ({abs_target})")
        ret.append(abs_target)
        current_path = abs_target

    return ret

def main():
    """Main function."""
    # Really delete or just do a smoke test?
    do_delete = len(sys.argv) > 1 and sys.argv[1] == "--delete"

    # Firmware location
    fw_dir = "/lib/firmware/"

    # In the Live ISO there should be just one kernel installed
    try:
        kernel_dirs = glob.glob("/lib/modules/*")
        if not kernel_dirs:
            print("Error: No kernel module directories found in /lib/modules/", file=sys.stderr)
            sys.exit(1)
        kernel_dir = kernel_dirs[0]
    except IndexError:
        print("Error: No kernel module directories found in /lib/modules/", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning kernel modules in {kernel_dir}...")

    # List of referenced firmware names from the kernel modules
    required_firmware = set()

    # Traverse the kernel drivers tree and extract the needed firmware files
    for root, _, files in os.walk(kernel_dir):
        for filename in files:
            if filename.endswith((".ko", ".ko.xz", ".ko.zst")):
                path = os.path.join(root, filename)
                try:
                    result = subprocess.run(
                        ['/usr/sbin/modinfo', '-F', 'firmware', path],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode != 0:
                        continue
                    
                    driver_fw = result.stdout.strip().split('\n')

                    for fw_name in driver_fw:
                        if not fw_name:
                            continue

                        patterns_to_glob = []
                        base_pattern = os.path.join(fw_dir, fw_name)

                        if not fw_name.endswith("*"):
                            patterns_to_glob.append(base_pattern)
                            patterns_to_glob.append(base_pattern + ".xz")
                            patterns_to_glob.append(base_pattern + ".zst")
                        else:
                            patterns_to_glob.append(base_pattern)

                        matching_files = []
                        for p in patterns_to_glob:
                            matching_files.extend(glob.glob(p))

                        if "*" in fw_name and matching_files:
                            expanded_str = ", ".join([os.path.basename(f) for f in matching_files])
                            print(f"Pattern {fw_name!r} expanded to: {expanded_str}")

                        fw_files = []
                        for f in matching_files:
                            fw_files.extend(resolve_symlinks(f, fw_dir))
                        
                        for f in fw_files:
                            required_firmware.add(f.removeprefix(fw_dir))

                except FileNotFoundError:
                    print("Error: /usr/sbin/modinfo not found. Is kmod package installed?", file=sys.stderr)
                    sys.exit(1)

    print("Removing unused firmware...")
    unused_size = 0

    # Traverse the firmware tree and delete files not referenced by any kernel module
    for root, _, files in os.walk(fw_dir):
        for filename in files:
            fw_path = os.path.join(root, filename)
            
            if os.path.isdir(fw_path):
                continue

            fw_name = fw_path.removeprefix(fw_dir)

            if fw_name not in required_firmware:
                try:
                    # os.path.getsize follows symlinks
                    unused_size += os.path.getsize(fw_path)
                    if do_delete:
                        os.remove(fw_path)
                    else:
                        print(f"Found unused firmware {fw_path}")
                except FileNotFoundError:
                    # This handles dangling symlinks
                    if do_delete:
                        if os.path.islink(fw_path):
                            os.remove(fw_path)
                    else:
                        print(f"Found unused dangling symlink {fw_path}")

    # Do some cleanup at the end
    if do_delete:
        print("Removing dangling symlinks...")
        subprocess.run(['find', fw_dir, '-xtype', 'l', '-delete'], check=False)
        print("Removing empty directories...")
        subprocess.run(['find', fw_dir, '-type', 'd', '-empty', '-delete'], check=False)

    print(f"Unused firmware size: {unused_size} ({unused_size >> 20} MiB)")

if __name__ == "__main__":
    main()
