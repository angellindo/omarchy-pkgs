# SPDX-License-Identifier: GPL-2.0-only
"""Fake-sysfs tests: no root, module commands, or real device writes."""

import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
loader = importlib.machinery.SourceFileLoader("t1_driver", str(HERE / "t1-touchbar"))
spec = importlib.util.spec_from_loader(loader.name, loader)
driver = importlib.util.module_from_spec(spec)
loader.exec_module(driver)


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="t1-driver-test-")
        self.addCleanup(self.scratch.cleanup)
        root = Path(self.scratch.name)
        self.sys = root / "sys"
        self.proc = root / "proc"
        self.guard = root / "recovery-guard"
        for name, value in (("SYS", self.sys), ("PROC", self.proc), ("GUARD", self.guard)):
            self.enterContext(patch.object(driver, name, value))
        self.enterContext(patch.object(driver.os, "geteuid", return_value=0))
        self.commands = []
        self.writes = []
        self.fail_binding = None
        self.enterContext(patch.object(driver, "run", side_effect=self.fake_run))
        self.enterContext(patch.object(driver, "write_sysfs", side_effect=self.fake_write))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))
        self.file(self.sys / "class/dmi/id/product_name", driver.MODEL)
        (self.sys / "devices/platform/APP7777:00").mkdir(parents=True)
        self.usb = self.sys / "devices/usb1/1-3"
        for name, value in (("idVendor", "05ac"), ("idProduct", "8600"),
                            ("devnum", "7"), ("removable", "fixed"),
                            ("bConfigurationValue", "1"), ("power/control", "auto"),
                            ("power/wakeup", "enabled")):
            self.file(self.usb / name, value)
        self.link(self.sys / "bus/usb/devices/1-3", self.usb)
        self.drivers = self.sys / "bus/hid/drivers"
        for name in ("hid-generic", "hid-sensor-hub", "apple-ibridge-hid", "apple-touchbar", "custom-panel"):
            for operation in ("bind", "unbind"):
                self.file(self.drivers / name / operation, "")
        self.physical = self.usb / "1-3:1.2/0003:05AC:8600.0001"
        self.virtual = self.physical / "0003:1D6B:0301.0002"
        self.virtual.mkdir(parents=True)
        for node in (self.physical, self.virtual):
            self.link(self.sys / "bus/hid/devices" / node.name, node)
            self.link(node / "driver", self.drivers / "hid-generic")
        for name, value in (("fnmode", "1"), ("idle_timeout", "300"), ("dim_timeout", "-2")):
            self.file(self.virtual / name, value)
        self.file(self.sys / "module/applespi/parameters/fnremap", "0")
        self.file(self.proc / "bus/input/devices",
                  'N: Name="Apple SPI Keyboard"\nH: Handlers=kbd event4 tbkbd\n')

    @staticmethod
    def file(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + "\n")

    @staticmethod
    def link(path, target):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)

    def fake_run(self, *args):
        self.commands.append(args)
        if args[0] == "/usr/bin/modprobe":
            module = args[1]
            self.assertIn(module, driver.PARAMETERS)
            for option in args[2:]:
                key, value = option.split("=", 1)
                self.file(self.sys / "module" / module / "parameters" / key, value)
        else:
            self.assertEqual(args, ("/usr/bin/udevadm", "settle", "--timeout=10"))

    def fake_write(self, path, value, target):
        driver.check_target(target)
        self.writes.append((path, value))
        if self.drivers in path.parents:
            dev = self.sys / "bus/hid/devices" / value
            if path.name == "bind":
                if path.parent.name == self.fail_binding:
                    raise OSError("simulated target bind failure")
                self.assertIsNone(driver.owner(dev))
                (dev / "driver").symlink_to(path.parent)
            else:
                self.assertEqual(driver.owner(dev), path.parent.name)
                (dev / "driver").unlink()
        else:
            path.write_text(value + "\n")

    def assert_no_operations(self):
        self.assertEqual(self.commands, [])
        self.assertEqual(self.writes, [])

    def test_recovery_allows_preflight_but_blocks_condition_and_start(self):
        self.file(self.usb / "idProduct", "1281")
        self.assertEqual(driver.main(["preflight"]), 0)
        self.assertEqual(driver.main(["condition"]), 1)
        self.assertEqual(driver.main(["start"]), 1)
        self.assert_no_operations()

    def test_platform_and_multiple_device_checks(self):
        self.file(self.sys / "class/dmi/id/product_name", "MacBookPro15,1")
        self.assertEqual(driver.main(["condition"]), 1)
        self.file(self.sys / "class/dmi/id/product_name", driver.MODEL)
        self.link(self.sys / "bus/usb/devices/1-4", self.usb)
        self.assertEqual(driver.main(["condition"]), 1)
        self.assert_no_operations()

    def test_condition_needs_neither_modules_nor_released_guard(self):
        self.file(self.guard, "active recovery")
        self.assertEqual(driver.main(["condition"]), 0)
        self.assertEqual(driver.main(["start"]), 1)
        self.assert_no_operations()

    def test_config2_refused_before_module_load_or_write(self):
        self.file(self.usb / "bConfigurationValue", "2")
        self.assertEqual(driver.main(["start"]), 1)
        self.assert_no_operations()

    def test_unknown_owner_is_not_displaced(self):
        (self.physical / "driver").unlink()
        (self.physical / "driver").symlink_to(self.drivers / "custom-panel")
        self.assertEqual(driver.main(["start"]), 1)
        self.assert_no_operations()

    def test_incompatible_module_and_remapped_fn_are_refused(self):
        bad = self.sys / "module/apple_ib_tb"
        bad.mkdir()
        self.assertEqual(driver.main(["start"]), 1)
        bad.rmdir()
        self.file(self.sys / "module/applespi/parameters/fnremap", "1")
        self.assertEqual(driver.main(["start"]), 1)
        self.assert_no_operations()

    def test_loaded_bridge_without_guard_parameter_is_refused(self):
        (self.sys / "module/apple_ibridge").mkdir()
        self.assertEqual(driver.main(["start"]), 1)
        self.assert_no_operations()

    def test_failed_target_binding_restores_original_allowed_owner(self):
        self.fail_binding = "apple-ibridge-hid"
        with self.assertRaisesRegex(driver.Refused, "restored original driver hid-generic"):
            driver.handover(self.physical, "apple-ibridge-hid", driver.healthy_target())
        self.assertEqual(driver.owner(self.physical), "hid-generic")
        self.assertEqual([path.parent.name for path, _ in self.writes],
                         ["hid-generic", "apple-ibridge-hid", "hid-generic"])

    def test_changed_identity_prevents_binding_and_rollback_writes(self):
        target = driver.healthy_target()

        def disappear_after_unbind(path, value, snapshot):
            self.fake_write(path, value, snapshot)
            if path.name == "unbind":
                self.file(self.usb / "idProduct", "1281")

        with patch.object(driver, "write_sysfs", side_effect=disappear_after_unbind):
            with self.assertRaisesRegex(driver.Refused, "ROLLBACK FAILED"):
                driver.handover(self.physical, "apple-ibridge-hid", target)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(driver.read(self.usb / "idProduct"), "1281")

    def test_unrelated_virtual_device_is_not_touched(self):
        unrelated = self.sys / "devices/other/0003:1D6B:0301.0009"
        unrelated.mkdir(parents=True)
        self.link(self.sys / "bus/hid/devices" / unrelated.name, unrelated)
        self.assertEqual([p.name for p in driver.hid_nodes(driver.healthy_target(), True)],
                         [self.virtual.name])

    def test_successful_start_uses_exact_order_and_settings(self):
        self.assertEqual(driver.main(["start"]), 0)
        self.assertEqual(self.commands[:2], [
            ("/usr/bin/modprobe", "apple_touchbar", "fnmode=2", "idle_timeout=-1", "dim_timeout=-1"),
            ("/usr/bin/modprobe", "apple_ibridge", "skip_acpi_power=1"),
        ])
        self.assertEqual(driver.owner(self.physical), "apple-ibridge-hid")
        self.assertEqual(driver.owner(self.virtual), "apple-touchbar")
        self.assertEqual(driver.read(self.virtual / "fnmode"), "2")
        self.assertEqual(driver.read(self.usb / "power/control"), "on")
        self.assertEqual(driver.read(self.usb / "bConfigurationValue"), "1")
        # A repeat is allowed but should not unbind correct owners.
        self.writes.clear()
        self.assertEqual(driver.main(["start"]), 0)
        self.assertFalse(any(path.name == "unbind" for path, _ in self.writes))

    def test_unconfigured_healthy_device_is_configured_without_usb_unbind(self):
        self.file(self.usb / "bConfigurationValue", "")
        self.assertEqual(driver.main(["start"]), 0)
        self.assertIn((self.sys / "bus/usb/devices/1-3/bConfigurationValue", "1"), self.writes)
        self.assertFalse(any("/usb/drivers/" in str(path) for path, _ in self.writes))

    def test_missing_fn_handler_is_reported_as_failure(self):
        self.file(self.proc / "bus/input/devices", 'N: Name="Apple SPI Keyboard"\nH: Handlers=event4\n')
        self.assertEqual(driver.main(["start"]), 1)

    def test_wakeup_policy_is_last_write_after_driver_binding(self):
        self.assertEqual(driver.main(["start"]), 0)
        self.assertEqual(self.writes[-1], (self.sys / "bus/usb/devices/1-3/power/wakeup", "disabled"))
        self.assertEqual(driver.read(self.usb / "power/wakeup"), "disabled")

    def test_failed_wakeup_write_is_not_reported_as_success(self):
        def ignore_wakeup(path, value, target):
            if path.name != "wakeup":
                self.fake_write(path, value, target)
        with patch.object(driver, "write_sysfs", side_effect=ignore_wakeup):
            self.assertEqual(driver.main(["start"]), 1)


class ServiceTests(unittest.TestCase):
    def test_service_syntax_and_ordering_against_system_targets(self):
        source = (HERE / "apple-t1-touchbar.service").read_text()
        self.assertIn("After=multi-user.target", source)
        self.assertIn("WantedBy=graphical.target", source)
        self.assertNotIn("WantedBy=multi-user.target", source)
        self.assertNotIn("ExecStop=", source)
        self.assertIn("t1-touchbar condition", source)
        # The installed executable does not exist yet. Substitute only that
        # path for systemd's executable-existence check; no unit is started.
        with tempfile.TemporaryDirectory(prefix="t1-unit-test-") as root:
            unit = Path(root) / "apple-t1-touchbar.service"
            unit.write_text(source.replace("/usr/lib/apple-t1-touchbar/t1-touchbar", "/usr/bin/true"))
            checked = subprocess.run(["systemd-analyze", "verify", "--man=no", str(unit)],
                                     capture_output=True, text=True, timeout=20)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)


if __name__ == "__main__":
    unittest.main()
