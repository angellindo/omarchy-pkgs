# Suspend follow-up — 2026-09-19

These are additional observations on the same MacBookPro14,3 with kernel
`7.2.5-3-omarchy`. The T1 package is not a complete laptop suspend fix.
No new driver or permanent power-management workaround is included here.

## Overnight lid-close failure

The user reported Wi-Fi unavailable after reopening the lid. The previous boot's
journal records s2idle entry at 03:27:09 and exit at 06:46:57 (local UTC-05:00),
about 3 h 20 min including entry/resume overhead. Relevant kernel messages:

```text
brcmfmac 0000:03:00.0: Unable to change power state from D3hot to D0, device inaccessible
brcmfmac 0000:03:00.0: Unable to change power state from D3cold to D0, device inaccessible
brcmfmac: brcmf_chip_recognition: MMIO read failed: 0xffffffff
brcmfmac: brcmf_pcie_pm_leave_D3: probe after resume failed, err=-19
```

Both Thunderbolt xHCI controllers (`07:00.0`, `7d:00.0`) also exhausted the
65535 ms resume wait; Thunderbolt resume emitted warnings. This is a PCI device
resume failure, not merely failure to reconnect to an access point. The exact
platform/firmware cause remains unresolved.

The one-shot Wi-Fi/Thunderbolt protection had been removed after the controlled
trials. This overnight interval has no protected PRE/POST execution in the service
journal. It therefore does not establish failure of that workaround when active;
it establishes that ordinary lid suspension is still broken. That boot still
used the experimental `pcie_aspm=force pcie_aspm.policy=default` command line.
ASPM forcing did not prevent this failure; it is not recommended as a fix.
After a subsequent reboot, the usual command line has no ASPM override and
NetworkManager reports Wi-Fi connected.

## Device recovery does not establish low-power sleep

Earlier lid tests discharged the battery from 78% to 54% in about 80 minutes
without protection, and from 47% to 28% in about 64 minutes with protection.
Both correspond to roughly 18 battery percentage points per hour on this battery.
The protected test recovered the PCI devices but did not resolve high consumption.
These observations are not a calibrated whole-system power measurement.

In a separate protected AC-powered trial, package C3 residency accounted for
about 99.55% of the roughly 629-second sample interval; package C6–C10 counters
remained zero. The CPU package-state limit register was read as unlimited;
no MSR writes were made. Forcing ASPM and testing powersupersave did not produce
deeper package residency in the tested windows. An isolated function trace
confirmed execution of `amdgpu_device_suspend` and `amdgpu_device_resume`;
it did not prove physical GPU power removal or D3cold. PCI power-state tracing
was attempted but rejected before another sleep test, so it yielded no result.

No temperature samples were available inside suspended userspace. The user's
previous report of a hot laptop in a bag remains a serious unresolved symptom;
the exact temperature and cause during that incident were not captured.

## Scope of the contribution

The earlier Touch Bar/input/camera and brightness observations remain the scope
of the package contribution. Overnight system stability, safe closed-lid transport,
low-power sleep, SuperSpeed transfers, 5 GHz and attached-peripheral suspend are
not validated. The experimental protection is not installed by the package.
Raw journals, network identifiers, firmware and recovery material remain private.
