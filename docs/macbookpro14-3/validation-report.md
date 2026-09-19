# MacBookPro14,3: independent T1, brightness and suspend observations

Test platform: Intel 15-inch 2017 MacBook Pro (MacBookPro14,3, Apple T1), Omarchy, kernel `7.2.5-3-omarchy`, Radeon Pro 560, BCM43602 (`14e4:43ba`), dual Alpine Ridge NHI (`8086:15d2`) and xHCI (`8086:15d4`). Only this model was physically tested.

These observations concern a local implementation. They are not a claim that PR #298, #9910, #11570 or any other pending PR was installed or validated verbatim.

## Touch Bar

The driver was pinned to `monomyth/t1-touchbar@a33c7eb27777339c047b8f532d1e6baebaec46bd`, including the resume/input changes related to AJ-dev-i60/t1-touchbar#1. The local loader checks model and healthy USB `05ac:8600`, validates identity before changes, only hands over permitted generic HID owners, refuses recovery mode and configuration-2 display stacks, and verifies the virtual control and SPI Fn handler after binding. It loads late, avoids SOCW calls and disables remote wake after HID binding.

Physical Esc/F1–F12/Fn-media operation, camera and subsequent boots were verified. Touch Bar resume was observed; physical Esc/F keys were confirmed after an earlier suspend. Sixteen synthetic-sysfs loader tests cover refusals and rollback. The cleaned source package compiled and passed all sixteen tests against the installed Omarchy headers, with module vermagic checked. DKMS remains responsible for installing modules on the user's kernel.

The public reference package contains no firmware recovery mechanism. Missing T1 firmware is a separate prerequisite: a recovery-mode T1 must not be reported as fixed merely because the DKMS package installed.

## Native panel brightness persistence

`gmux_backlight` is under PNP; the stock udev `path_id` import prevented the native systemd-backlight service from being requested. A local rule supplied `ID_PATH=platform-apple-gmux`, added the systemd tag and requested the native backlight unit. A save/change/load test restored the exact value, and a subsequent normal restart preserved it. This independently supports the diagnosis in omarchy#9910; that PR's rule omits the explicit identity, so our result is not a verbatim test of its implementation.

Volume also survived a normal restart under existing WirePlumber route/profile restoration. No additional volume daemon or fixed startup level is proposed.

## Suspend comparison

| Variant | Observed result |
|---|---|
| Disable D3cold on Wi-Fi, Thunderbolt and upstream bridges | Wi-Fi recovered in one cycle, but Thunderbolt produced inaccessible-device errors and both xHCI controllers disappeared |
| Keep only both xHCI controllers runtime-active | Thunderbolt errors persisted; Wi-Fi failed MMIO reads with `0xffffffff` and resume error `-19`; user restarted to regain Wi-Fi |
| Protect Wi-Fi and its bridge from D3cold, remove healthy empty Thunderbolt trees before s2idle, rescan afterwards | Three completed cycles in the same boot, both NHI/xHCI pairs restored, connected 2.4 GHz Wi-Fi with HTTPS verification, brightness and volume preserved |

In the second successful cycle one HTTPS attempt timed out after five seconds; subsequent requests to two independent sites returned HTTP 200, and three gateway pings had no loss. The third cycle returned HTTP 200 from both sites on the first attempt. No previous inaccessible-device/MMIO/resume/Thunderbolt warning patterns appeared during these protected resume intervals.

Wi-Fi firmware reinitialized after resume; this did not preserve the firmware instance. No claim is made for 5 GHz. The USB memory physically checked was later observed on the chipset USB 2.0 controller at 480 Mbit/s. NHI/xHCI re-enumeration therefore does not prove a real SuperSpeed transfer. Suspend with attached storage, displays or other peripherals and prolonged/overnight sleep remain unvalidated.

The experiment used `ExecStartPre` and `ExecStopPost` on `systemd-suspend.service`, rather than a sleep hook that cannot stop suspend on failure. Preflight refuses model/topology mismatch, external PCI/USB devices, attached block devices, external displays and overlapping trials. It saves policies before modification and restores them after failure as well as after wake. Nine offline tests cover the guard and recovery paths. The one-shot override was removed after each test series. It is not a production fix.

## NVMe targeting

On this machine, `01:00.0` is the Radeon GPU and `02:00.0` is Samsung NVMe (`144d:a804`). The installed Omarchy service named as an NVMe workaround wrote to the GPU. This confirms the mismatch described in #11624/#10877. The existing GPU policy was not changed during the suspend trials; correcting the installer target must not be represented as independently resolving these resume failures.

## Packaging review limits

The source package, loader tests, udev syntax and unit verification passed. The build emitted a fakeroot payload warning; the build completed and archive ownership/modes were inspected, but official packaging CI should rebuild it in a clean chroot. No binary built on this workstation is proposed for distribution. Repository-wide test results are recorded in [TESTS.md](TESTS.md).

## Follow-up, 2026-09-19

The short-cycle results above do not establish overnight reliability or low sleep consumption. [Additional measurements and the overnight failure](suspend-follow-up.md) document both limitations; the overnight failure occurred without the one-shot protection active.
