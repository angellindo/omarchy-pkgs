# MacBookPro14,3 T1 loader reference

This branch shares a guarded late-loader implementation and independent hardware observations for discussion on [omarchy-pkgs #298](https://github.com/omacom/omarchy-pkgs/pull/298). It is a reference for extracting improvements into the existing proposal, not a request to ship two competing iBridge packages. Do not install this package alongside `apple-ib-drv-dkms`.

The source is in [pkgbuilds/apple-t1-touchbar-dkms](../../pkgbuilds/apple-t1-touchbar-dkms). The driver remains attributed to its upstream authors and pinned to a full commit with checksums. The loader adds strict model and USB identity checks, limited generic-HID ownership handover, refusal of recovery/configuration-2 devices, rollback and sixteen synthetic-sysfs tests.

[Hardware observations](validation-report.md) distinguish the implementation tested on MacBookPro14,3 from pending upstream PRs. [Verification results](TESTS.md) include the successful source build, the clean-chroot rebuild still needed, and the failures in the separate Omarchy installer suite. Installer and NVMe references mentioned in that report remain local and are not part of this package branch.

Only MacBookPro14,3 was physically tested. This is not general MacBook support or a production Wi-Fi/Thunderbolt suspend fix. The three experimental resume cycles do not establish USB 3.x transfers, 5 GHz Wi-Fi, attached-peripheral suspend or overnight stability. Firmware, recovery material, private logs and workstation-built binaries are excluded.

Latest: [2026-09-19 suspend follow-up](suspend-follow-up.md) documents an overnight Wi-Fi/Thunderbolt resume failure and high consumption even in a protected test. Ordinary lid suspension remains unresolved.
