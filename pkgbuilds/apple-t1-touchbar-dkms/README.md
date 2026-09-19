# Apple T1 Touch Bar for MacBookPro14,3

This opt-in DKMS package supports the fixed-function Touch Bar on the Intel 15-inch 2017 MacBook Pro. Only MacBookPro14,3 has been validated; the loader refuses other models. It leaves the in-kernel `applespi` keyboard and trackpad drivers in place. It is not a T2 or Apple Silicon package.

The driver comes from [monomyth/t1-touchbar](https://github.com/monomyth/t1-touchbar/tree/a33c7eb27777339c047b8f532d1e6baebaec46bd/apple-ib-drv), pinned to `a33c7eb27777339c047b8f532d1e6baebaec46bd`, with its GPL-2.0-only license and fixed source checksums. Credit for the driver and its resume/input fixes belongs to the upstream authors; this contribution packages and integrates their work.

## Firmware prerequisite

The internal T1 must already enumerate as `05ac:8600`. A device in recovery mode (`05ac:1281`) is refused. No firmware, personalization tickets or device identifiers are included, downloaded or flashed. This package cannot repair missing T1 firmware; recovery is a separate, device-specific procedure. A running T1 does not by itself prove firmware persistence across power-off.

## Behavior

- Esc and F1–F12 are the default; holding Fn selects media keys.
- The loader verifies model, USB identity and interface ownership before changing bindings. It refuses custom configuration-2 display stacks and incompatible loaded drivers.
- Only generic HID owners on the verified T1 may be handed over; other USB/HID devices are untouched.
- The loader avoids ACPI power calls and applies the remote-wake policy after HID binding. This is a compatibility policy, not a complete system-suspend fix.
- The service is ordered after `multi-user.target` and enabled through `graphical.target`. Installing the package does not enable the service or load modules.
- A gmux udev rule supplies the stable identity missing from the PNP backlight so native `systemd-backlight` saves and restores brightness.
- Omarchy headers remain an explicit dependency for DKMS rebuilds. Kernel updates still require checking the DKMS build result.

## Enable and verify

After installation, run `t1-touchbar` using its full path:

```sh
/usr/lib/apple-t1-touchbar/t1-touchbar preflight
sudo systemctl enable --now apple-t1-touchbar.service
systemctl status apple-t1-touchbar.service
dkms status
```

A skipped service condition is not a successful hardware test. Verify the service is active, physically test press/release of Esc, F1–F12 and Fn/media, and confirm the camera and keyboard remain usable. Stopping or disabling the service does not unload the running kernel modules; reboot to return to a boot without the service.

## Validation and limits

The pinned driver and loader were tested on MacBookPro14,3 with `7.2.5-3-omarchy`, including physical keys, camera, firmware persistence and native brightness restoration after a normal restart. The loader has sixteen fake-sysfs tests, including refusals and rollback. The build checks compilation and module vermagic against installed headers rather than the build host's `uname`.

Complete Wi-Fi/Thunderbolt suspend recovery is outside this package. A separate local experiment recovered those devices in three cycles by protecting Wi-Fi and removing/re-enumerating empty Thunderbolt branches, but USB 3.x transfers, 5 GHz Wi-Fi and attached-peripheral suspend remain unvalidated. That workaround is not installed by this package.

[Subsequent testing](../../docs/macbookpro14-3/suspend-follow-up.md) found high sleep consumption even with the experimental protection and an overnight Wi-Fi/Thunderbolt failure without it. Do not treat working Touch Bar input as proof of reliable or low-power lid suspension.
