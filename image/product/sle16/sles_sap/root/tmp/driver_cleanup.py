#!/usr/bin/env python3

# This script removes not needed drivers from the Live ISO. It deletes the drivers which are either
# not relevant for the installer (sound cards, TV cards, joysticks, NFC...) or the hardware is
# obsolete and very likely not used in modern systems (PCMCIA, Appletalk...).
#
# By default the script runs in safe mode and only lists the drivers to delete, use the "--delete"
# argument to really delete the drivers.
#
# The script uses the "module.list" file from the installation-images package
# (https://github.com/openSUSE/installation-images/blob/master/etc/module.list). The file should be
# updated manually from time to time. Hot fixes or Agama specific changes should be added into the
# module.list.extra file.
#
# The file lists the drivers or whole directories which should be present in the installation
# system. If the line starts with "-" then that driver or directory should be removed. It is usually
# connected with the previous line, it allows to include a whole directory with drivers but delete
# just a specific driver or subdirectory below it.
#
# The file is actually a list of Perl regexps, hopefully only the basic regexp features which work
# also in Python will be ever used...

import os
import sys
import re
import subprocess
import glob
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class Driver:
    name: str
    path: str
    deps: list[str] = field(default_factory=list)

    @classmethod
    def from_file(cls, file_path: Path):
        try:
            # Get dependencies
            result = subprocess.run(
                ['/usr/sbin/modinfo', '-F', 'depends', str(file_path)],
                capture_output=True, text=True, check=False
            )
            deps = result.stdout.strip().split(',') if result.stdout.strip() else []

            # Get name from filename
            name = file_path.name
            # Check for longest extensions first to handle e.g. ".ko.xz" correctly
            for ext in ['.ko.xz', '.ko.zst', '.ko']:
                if name.endswith(ext):
                    name = name[:-len(ext)]
                    break
            
            return cls(name=name, path=str(file_path), deps=deps)
        except FileNotFoundError:
            print("Error: /usr/sbin/modinfo not found. Is kmod package installed?", file=sys.stderr)
            sys.exit(1)

def arch_filter(lines):
    """
    Remove lines for other architectures than the current machine architecture.
    The arch specific lines start with the <$arch> line and end with the </$arch> line.
    """
    filtered_lines = []
    skipping = False
    try:
        arch = subprocess.run(['arch'], capture_output=True, text=True, check=True).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Warning: 'arch' command failed. Cannot filter by architecture.", file=sys.stderr)
        arch = None

    arch_tag = None

    for line in lines:
        open_match = re.match(r'^\s*<\s*(\w+)\s*>\s*$', line)
        if open_match:
            arch_tag = open_match.group(1)
            skipping = (arch_tag != arch)
            continue # Always remove the tag line

        close_match = re.match(r'^\s*</\s*\w+\s*>\s*$', line)
        if close_match:
            skipping = False
            continue # Always remove the tag line

        if skipping:
            if arch_tag:
                print(f"Ignoring {arch_tag} specific line: {line}")
            continue
        
        filtered_lines.append(line)
    
    return filtered_lines

def main():
    do_delete = len(sys.argv) > 1 and sys.argv[1] == "--delete"
    debug = os.environ.get("DEBUG") == "1"

    script_dir = Path(__file__).parent
    
    try:
        # Read config files
        config_lines = (script_dir / "module.list").read_text().splitlines()
        config_lines += (script_dir / "module.list.extra").read_text().splitlines()
    except FileNotFoundError as e:
        print(f"Error: Could not read module list file: {e}", file=sys.stderr)
        sys.exit(1)

    # Filter comments and empty lines
    config_lines = [line.strip() for line in config_lines if line.strip() and not line.strip().startswith('#')]

    # Process architecture-specific lines
    config_lines = arch_filter(config_lines)

    # Split into keep and delete regex patterns
    delete_patterns = []
    keep_patterns = []
    for line in config_lines:
        if line.startswith('-'):
            delete_patterns.append(re.compile(line[1:]))
        else:
            keep_patterns.append(re.compile(line))

    # Find kernel directory
    try:
        kernel_dir = glob.glob("/lib/modules/*")[0]
    except IndexError:
        print("Error: No kernel module directories found in /lib/modules/", file=sys.stderr)
        sys.exit(1)
    
    kernel_dir_path = Path(kernel_dir)

    to_keep = []
    to_delete = []

    print(f"Scanning kernel modules in {kernel_dir}...")
    for path in kernel_dir_path.rglob('*'):
        if path.is_file() and any(path.name.endswith(ext) for ext in ['.ko', '.ko.xz', '.ko.zst']):
            driver = Driver.from_file(path)
            if not driver:
                continue

            kernel_path = str(path.relative_to(kernel_dir_path))

            if any(p.search(kernel_path) for p in delete_patterns):
                to_delete.append(driver)
            elif any(p.search(kernel_path) for p in keep_patterns):
                to_keep.append(driver)
            else:
                # Implicitly delete unknown drivers
                to_delete.append(driver)

    print("Checking driver dependencies...")

    while True:
        # Get all dependency names from drivers currently in to_keep
        all_kept_deps = set(dep for driver in to_keep for dep in driver.deps if dep)

        # Find drivers in to_delete that are dependencies of drivers in to_keep
        referenced = [d for d in to_delete if d.name in all_kept_deps]

        if not referenced:
            break

        for d in referenced:
            print(f"Keep dependant driver {d.path}")

        # Move from to_delete to to_keep
        to_keep.extend(referenced)
        referenced_paths = {d.path for d in referenced}
        to_delete = [d for d in to_delete if d.path not in referenced_paths]

    delete_paths = [d.path for d in to_delete]
    print(f"Found {len(delete_paths)} drivers to delete")
    if debug:
        for path in sorted(delete_paths):
            print(path)

    if do_delete:
        for path in delete_paths:
            try:
                os.remove(path)
            except OSError as e:
                print(f"Error deleting {path}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
