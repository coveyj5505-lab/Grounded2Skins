# Crook jab V1 Windows feedback and isolated V2 draft

User reports rotation/return works but no visible forward lunge. The screenshots show native punching arm far inward from the camera-relative crook. User proposes a real spear carry/jab screenshot reference. Assistant requested standing and mid-jab screenshots at the same FOV; no reference spear screenshot has arrived yet.

Windows log confirms GameplayStatics.GetTimeSeconds is supported, jab/recover/carry transitions run, and screen anchor calibration targets92% at2560x1440, producing right101.97cm. Median observed native attack flag duration is0.9215s. V1 reaches its12cm thrust by170ms and holds extension until that flag clears. These findings explain a weak visible pulse but do not establish a native hand/weapon grip match.

Isolated UNPUBLISHED V2 draft changes only the cosmetic stroke:100ms lowering,200ms forward stroke,220ms withdrawal, then forward-ready until actual attack ends,160ms upright return. FP thrust increases12->30cm. No new engine calls, native animations, gameplay writes, Paks or model changes.11 actual Lua curve and35 mocked adapter/carry/camera groups pass. Existing accepted skins and released V1 remain unchanged.

FP position is intentionally NOT retuned yet. The next carry/attack position should use the proposed native spear reference rather than another arbitrary margin. Aligning the staff alone cannot replace the native punch pose. Full native spear-arm animation remains incomplete; existing current-build clip inventory contains gameplay hit-frame notifies and still needs safe pose-only adaptation without native combat effects/timing changes. This draft is not represented as that full solution and is not a new Windows package.
