# Base teleporter prototype asset pipeline

Requires the hash-verified current buildable-teleport collector output, supplied
matching table mappings, Python 3.12/cityhash, .NET 10 and pinned CUE4Parse.
Game assets and the uploaded mapping are not checked into the repository.

Resolve collected native symbol IDs:

```bash
python pipeline/base-teleporter/prepare_globals.py /path/to/buildable-collection
```

Build the read-only native row inspector, then supply mapping, derived native
symbol JSON, a NEW output directory and the two collected catalog chunk paths:

```bash
dotnet build pipeline/base-teleporter/CatalogInspector.csproj -c Release -p:CUE4PARSE_SKIP_NATIVE=true -m:2
dotnet pipeline/base-teleporter/bin/Release/net10.0/CatalogInspector.dll \
  /path/to/current-compatible.usmap \
  /path/to/buildable-collection/global/script-object-paths.json \
  /path/to/measured-layouts \
  /path/to/buildable-collection/chunks/69a09afefc4abfcd00000001 \
  /path/to/buildable-collection/chunks/cd0419132f02479000000001
```

The inspector rejects incomplete export/row reads and records source hashes and
measured field positions. It supports duplicate export names by including chunk
IDs in output filenames. No runtime AddRow or unsupported native struct copy is
used. Build the raw assets with a version-5 container-header template previously
unpacked by retoc (not the original game archive):

```bash
python pipeline/base-teleporter/build_assets.py \
  /path/to/buildable-collection /path/to/measured-layouts \
  /path/to/unpacked-template /path/to/NEW-base-raw
```

Four generated packages: the two original composite catalogs with one additional
cached row and one additional private parent each, plus one-row private building
and recipe tables. The additive parents retain the row if the engine rebuilds a
composite's cache. All original row bytes are preserved. Name maps, public hashes,
imports, dependency entries, package-store dependencies and export sizes are
relocated, not patched using guessed offsets. Placement booleans are modified at
the measured native field positions and independently read back.

Use pipeline/repackage_iostore.py with retoc 0.1.5 to pack/verify/unpack a new mod
container. Then mount it with the current global pair and mapping in CUE4Parse,
verify private-parent loading and 862/635/1/1 row counts, compare all 861/634 original
rows, and run retoc to-legacy with UE5_7; require 4 extracted / 0 failed assets.
The companion PAK is an empty IoStore companion from an existing verified mod.

Lua checks:

```bash
python pipeline/utility-updates/test_base_teleport.py
python pipeline/utility-updates/test_base_teleport_integration.py
python pipeline/utility-updates/test_teleport_v9_outposts.py
```

These execute production Lua under guarded mocks. Native Windows placement,
streaming, replication, demolition, arrival and save behavior are separate required
acceptance checks, not established by serialization or these mocks.
