ToyStoryDiscovery: read-only UE4SS v3.0.1 Beta probe
Uses your already working UE4SS installation. Do not replace its DLL/settings or FreeBuild.
Close game. Copy ToyStoryDiscovery folder into the same Mods directory as your working FreeBuild mod. enabled.txt is included; if your loader uses mods.txt, append ToyStoryDiscovery : 1 without replacing other lines.
Load a copied test save. Press Ctrl+F8 once per state: unarmed idle, walking, equipped spear idle, spear attacking, another weapon, shield, sitting, and gliding. Also capture first-person unarmed and third-person unarmed. Keep a note of this order. Return UE4SS.log with the notes.
This probe only logs metadata and reads properties. It never spawns, attaches, equips, attacks, plays montages or calls game-specific discovered functions. Function names are discovery evidence, not proof they can be used safely.
Disable by removing this mod folder or its enable entry. No skin packages need changing.
Cloud checks: Lua 5.4 execution with mocked menu/local/remote controller states and game-thread dispatch passed. Actual UE4SS reflection behavior still requires Windows test.
