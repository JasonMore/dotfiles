import importlib.util
from pathlib import Path
import plistlib
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    "monitor_role", Path(__file__).resolve().parents[1] / "set-monitor-role.py"
)
monitor_role = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_role)


class MonitorRoleTests(unittest.TestCase):
    def test_matches_real_monitor_identifiers(self):
        display = {
            "_name": "HG560T34",
            "_spdisplays_display-vendor-id": "4a8b",
            "_spdisplays_display-product-id": "6034",
            "spdisplays_online": "spdisplays_yes",
        }
        report = {"SPDisplaysDataType": [{"spdisplays_ndrvs": [display]}]}
        self.assertEqual(monitor_role.find_monitor(report), display)
        display["_spdisplays_display-product-id"] = "6035"
        with self.assertRaises(ValueError):
            monitor_role.find_monitor(report)

    def test_preserves_other_override_settings(self):
        existing = plistlib.dumps({"scale-resolutions": [b"test"], "DisplayIsTV": True})
        config = plistlib.loads(monitor_role.make_override(existing))
        self.assertEqual(config["scale-resolutions"], [b"test"])
        self.assertIs(config["DisplayIsTV"], False)
        self.assertEqual(config["DisplayVendorID"], 19083)
        self.assertEqual(config["DisplayProductID"], 24628)

    def test_rejects_conflicting_or_invalid_overrides(self):
        for config in ([], {"DisplayVendorID": 1}, {"DisplayProductID": 1}):
            with self.assertRaises(ValueError):
                monitor_role.make_override(plistlib.dumps(config))

    def test_install_backup_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "vendor" / "product"
            data = monitor_role.make_override(None)
            monitor_role.install_override(target, data)
            self.assertEqual(target.read_bytes(), data)
            self.assertEqual(target.stat().st_mode & 0o777, 0o644)
            original = plistlib.dumps({"DisplayIsTV": True, "custom": "preserved"})
            target.write_bytes(original)
            data = monitor_role.make_override(original)
            monitor_role.install_override(target, data)
            backups = list(target.parent.glob("product.backup-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)
            monitor_role.install_override(target, data)
            self.assertEqual(len(list(target.parent.iterdir())), 2)

    def test_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "override"
            target.symlink_to(Path(directory) / "missing")
            with self.assertRaises(ValueError):
                monitor_role.install_override(target, monitor_role.make_override(None))


if __name__ == "__main__":
    unittest.main()
