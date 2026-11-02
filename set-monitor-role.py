#!/usr/bin/env python3
"""Set HG560T34's display override to Computer Monitor. Preview by default."""

import argparse
import datetime
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile


NAME = "HG560T34"
VENDOR = 0x4A8B
PRODUCT = 0x6034
TARGET = Path(
    "/Library/Displays/Contents/Resources/Overrides/"
    "DisplayVendorID-4a8b/DisplayProductID-6034"
)


def find_monitor(report):
    for gpu in report["SPDisplaysDataType"]:
        for display in gpu.get("spdisplays_ndrvs", []):
            if (
                display.get("_name") == NAME
                and display.get("_spdisplays_display-vendor-id") == f"{VENDOR:x}"
                and display.get("_spdisplays_display-product-id") == f"{PRODUCT:x}"
                and display.get("spdisplays_online") == "spdisplays_yes"
            ):
                return display
    raise ValueError("The HG560T34 with vendor 4a8b and product 6034 is not connected.")


def make_override(existing):
    config = plistlib.loads(existing) if existing is not None else {}
    if not isinstance(config, dict):
        raise ValueError("The existing override is not a plist dictionary.")
    for key, expected in (("DisplayVendorID", VENDOR), ("DisplayProductID", PRODUCT)):
        if key in config and config[key] != expected:
            raise ValueError(f"The existing override has a conflicting {key}.")
        config[key] = expected
    config["DisplayIsTV"] = False
    return plistlib.dumps(config, sort_keys=False)


def install_override(target, data):
    if target.is_symlink():
        raise ValueError(f"Refusing to replace a symbolic link: {target}")
    existing = target.read_bytes() if target.exists() else None
    if existing is not None and plistlib.loads(existing) == plistlib.loads(data):
        print(f"The override is already installed: {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if existing is not None:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = target.with_name(f"{target.name}.backup-{stamp}")
        with backup.open("xb") as output:
            output.write(existing)
        print(f"Previous override saved: {backup}")
    fd, temporary = tempfile.mkstemp(prefix=".monitor-role-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            os.fchmod(output.fileno(), 0o644)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    if plistlib.loads(target.read_bytes()) != plistlib.loads(data):
        raise ValueError("The installed override did not match the requested data.")
    print(f"Override installed: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Install with sudo; no restart.")
    mode.add_argument("--check", action="store_true", help="Check active classification.")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("This script requires macOS.")
    report = json.loads(subprocess.check_output(
        ["/usr/sbin/system_profiler", "SPDisplaysDataType", "-json"], text=True
    ))
    display = find_monitor(report)
    projector = display.get("_spdisplays_projector") == "spdisplays_yes"
    television = display.get("_spdisplays_television") == "spdisplays_yes"
    print(f"{NAME}: projector={projector}, television={television}")
    if args.check:
        if projector or television:
            print("macOS still reports a projector or TV.", file=sys.stderr)
            return 1
        print("macOS no longer reports a projector or TV. Check Night Shift on screen.")
        return 0
    if TARGET.is_symlink():
        raise ValueError(f"Refusing to replace a symbolic link: {TARGET}")
    data = make_override(TARGET.read_bytes() if TARGET.exists() else None)
    if not args.apply:
        print(f"Preview only; no changes. Target: {TARGET}")
        print(data.decode(), end="")
        return 0
    if os.geteuid() != 0:
        parser.error("Use sudo python3 set-monitor-role.py --apply.")
    install_override(TARGET, data)
    print("Save your work, then restart the Mac. Run this script with --check afterward.")
    print("Night Shift support is not verified until you check its visible effect.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, plistlib.InvalidFileException, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
