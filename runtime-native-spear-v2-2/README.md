# Crook native-item V2 — blocked on current source item tables

Windows log2026-10-22 reports `Virtual UScriptStruct::ICppStructOps::Copy is unavailable` at V1 UDataTable.AddRow, before F10. ConsoleEnabler also lists F10 as a console key. V1 is withdrawn as a functional candidate; retain it unchanged for diagnosis.

V2 removes runtime AddRow/CopyScriptStruct entirely and requires a pre-cooked private item row. Its development test key is F7. The old empty V1 item-table asset is explicitly rejected. Native attack-cache validation, deferred cosmetic binding and rollback remain.

The original native item-row package is not among the previously received eight baselines. The targeted Crook-Item-Tables-Collector obtains Table_AllItems and actual imported item-table dependencies, read-only, without another animation/probe/gameplay test. Once received, clone/cook the native Spear row offline, rebind the three private damage8/range275/no-charge attack handles and disable throwing. Do not ship this draft with the empty V1 table or claim that a key change fixes the copy failure.

Accepted skins and published packages remain unchanged. Current Windows Teleport V3 testing is independent.

Four actual-Lua V2 row tests pass, including a fixture whose AddRow always raises the exact Windows unsupported-Copy failure; the V2 reader never calls it. The cooked item source remains required.
