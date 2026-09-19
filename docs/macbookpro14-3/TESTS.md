# Verification performed

## Focused checks

- Cleaned T1 source package: `makepkg --nodeps --log` completed using the already installed build dependencies and kernel headers. Source checksums, module compilation, vermagic checks and all 16 loader tests passed. No package was installed.
- `udevadm verify` accepted the gmux rule. `systemd-analyze verify` accepted the T1 service, while reporting the pre-existing escaped-PCI-path warning in the machine's installed NVMe service.
- Installer tests passed: MacBookPro14,3 selects the T1 package, other SPI models retain their current package, T2 is untouched, and a package failure prevents service enablement. The test stubs package/system actions; it does not install anything.
- NVMe reference tests passed: actual NVMe selected, GPU unchanged, multiple controllers and no-controller case handled. This reference is not recommended as another competing PR; #11624 has a more conservative controller scope.
- All 9 experimental suspend guard/restore tests passed. Actual protected suspend observations are in `validation-report.md`.
- `git diff --check` passed in all three worktrees. Installer/NVMe patches passed `git apply --check` against the unchanged Omarchy base checkout.
- The submission directory was scanned for the local username/home path, recorded boot IDs, private firmware artifact names and local-network address patterns; no matches were found. Only explicit source files and reviewed summaries were copied.

## Full Omarchy suite

`./test/all` completed. The CLI suite passed. The shell suite reported 5 failures out of 245 test files:

| Test | Follow-up |
|---|---|
| `launch-about-test.sh` | Same failure reproduced in an unchanged checkout: roomy-window animation assertion |
| `omarchy-kernel-migration-test.sh` | Same failure reproduced in an unchanged checkout: superseded PTL migration assertion |
| `snapper-test.sh` | Same failure reproduced in an unchanged checkout: required sibling `omarchy-iso` checkout absent |
| `update-pacman-test.sh` | Same failure reproduced in an unchanged checkout: guarded invocation assertion |
| `locate-test.sh` | Failed decoding Python bytecode created under `bin/__pycache__` by earlier tests; passed in the clean checkout and in the changed checkout after removing only those generated cache files |

The full suite is therefore not green in this environment. These results must accompany any submission; do not claim all repository tests passed. No unrelated production code was changed to silence the failures.

The package build also emitted a fakeroot payload warning despite completing successfully. Archive ownership and modes were inspected. An official clean-chroot rebuild remains necessary before publishing the package; the workstation-built binary is excluded from this submission.

## Documentation update, 2026-09-19

See [suspend follow-up](suspend-follow-up.md) for subsequent hardware observations. This update changes documentation only; the historical build/test results above were not rerun and are not new validation of system sleep.
