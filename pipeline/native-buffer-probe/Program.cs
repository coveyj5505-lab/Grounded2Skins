using System.Security.Cryptography;
using System.Text.Json;
using CUE4Parse.UE4.Readers;
using CUE4Parse.UE4.Versions;
using CUE4Parse.UE4.Objects.Meshes;
using CUE4Parse.UE4.Assets.Exports.StaticMesh;
using CUE4Parse.UE4.Assets.Exports.SkeletalMesh;
using CUE4Parse.UE4.Assets.Readers;
using CUE4Parse.UE4.Objects.Core.Math;

// Uses unmodified CUE4Parse buffer constructors, independently of the Python encoder.
var extract = args[0] == "extract-reference";
var input = Path.GetFullPath(args[1]);
var output = Path.GetFullPath(args[2]);
if (Directory.Exists(output)) throw new Exception("Output must be new");
Directory.CreateDirectory(output);
var versions = new VersionContainer(EGame.GAME_Grounded2);
var records = new List<object>();
byte[]? reference = null;
FByteArchive? source = null;
if (extract)
{
    reference = File.ReadAllBytes(input);
    if (Convert.ToHexString(SHA256.HashData(reference)).ToLowerInvariant() !=
        "7c4f26505028ebce27c7dc02aabfc61a719aa2e4ee4204a08b73884890664901")
        throw new Exception("Unexpected Commander101 reference body chunk");
    source = new FByteArchive("ReferenceBody", reference, versions) { Position = 34361 };
}
T Read<T>(string file, Func<FByteArchive, T> getter)
{
    using var own = extract ? null : new FByteArchive(file, File.ReadAllBytes(Path.Combine(input, file)), versions);
    var ar = extract ? source! : own!;
    var start = ar.Position;
    var value = getter(ar);
    if (!extract && ar.Position != ar.Length) throw new Exception($"Unread or over-read {file}: {ar.Position}/{ar.Length}");
    if (extract) File.WriteAllBytes(Path.Combine(output, file), reference!.AsSpan((int)start, (int)(ar.Position - start)).ToArray());
    records.Add(new { file, start, end = ar.Position, bytes = ar.Position - start });
    return value;
}
var indices = Read("indices.bin", ar => new FMultisizeIndexContainer(ar));
var positions = Read("positions.bin", ar => new FPositionVertexBuffer(ar));
var vertices = Read("static-vertices.bin", ar => new FStaticMeshVertexBuffer(ar));
var weights = Read("skin-weights.bin", ar => new FSkinWeightVertexBuffer(ar, true));
var colors = Read("colors.bin", ar => new FColorVertexBuffer(ar));
var n = positions.NumVertices;
if (positions.Verts.Length != n || vertices.NumVertices != n || vertices.UV.Length != n ||
    weights.Weights.Length != n || colors.Data.Length != n || vertices.NumTexCoords != 1)
    throw new Exception("Buffer count mismatch");
if (indices.Buffer.Any(i => i >= n) || indices.Buffer.Length % 3 != 0)
    throw new Exception("Invalid triangle indices");
if (weights.Weights.Any(w => w.BoneWeight.Length != 8 || w.bUse16BitBoneWeight || w.BoneWeight.Sum(x => (int)x) != 255))
    throw new Exception("Expected eight influence slots, UNORM8 weights summing255");
BinaryWriter Open(string file) => new(File.Open(Path.Combine(output, file), FileMode.CreateNew));
using (var b = Open("positions.f32")) foreach (var p in positions.Verts) { b.Write(p.X); b.Write(p.Y); b.Write(p.Z); }
using (var b = Open("indices.u32")) foreach (var i in indices.Buffer) b.Write(i);
using (var b = Open("uv0.f32")) foreach (var v in vertices.UV) { b.Write(v.UV[0].U); b.Write(v.UV[0].V); }
using (var b = Open("normals.f32")) foreach (var v in vertices.UV) { b.Write(v.Normal[2].X); b.Write(v.Normal[2].Y); b.Write(v.Normal[2].Z); }
using (var b = Open("tangents.f32")) foreach (var v in vertices.UV) { b.Write(v.Normal[0].X); b.Write(v.Normal[0].Y); b.Write(v.Normal[0].Z); }
using (var b = Open("signs.f32")) foreach (var v in vertices.UV) b.Write(v.Normal[2].W);
using (var b = Open("tangent-x-w.f32")) foreach (var v in vertices.UV) b.Write(v.Normal[0].W);
using (var b = Open("joints-local.u16")) foreach (var w in weights.Weights) foreach (var j in w.BoneIndex) b.Write(j);
using (var b = Open("weights.u16")) foreach (var w in weights.Weights) foreach (var q in w.BoneWeight) b.Write(q);
using (var b = Open("colors.rgba8")) foreach (var c in colors.Data) { b.Write(c.R); b.Write(c.G); b.Write(c.B); b.Write(c.A); }
var report = new { mode = args[0], vertices = n, triangles = indices.Buffer.Length / 3,
    uv_channels = vertices.NumTexCoords, full_precision_uv = vertices.UseFullPrecisionUVs,
    high_precision_tangents = vertices.UseHighPrecisionTangentBasis,
    exact_count_checks_passed = true, weights_eight_slots_sum255 = true,
    record_ranges = records, cooked_package_test = "NOT RUN", in_game_test = "NOT RUN" };
File.WriteAllText(Path.Combine(output, "reader-validation.json"), JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
if (extract)
{
    using var body = new FByteArchive("MeasuredReferenceLayout", reference!, versions);
    using var ar = new FAssetArchive(body, null);
    ar.Position = 8502;
    var bounds = new FBoxSphereBounds(ar);
    if (ar.Position != 8558) throw new Exception("Unexpected native bounds layout");
    ar.Position = 32898;
    var lod = new FStaticLODModel();
    lod.SerializeRenderItem(ar, true);
    if (ar.Position != 15761184) throw new Exception("Unexpected full native LOD layout");
    var layout = new { source_sha256 = Convert.ToHexString(SHA256.HashData(reference!)).ToLowerInvariant(),
        imported_bounds = new { offset = 8502, bytes = 56, encoding = "7 little-endian float64 values",
            origin = new[] { bounds.Origin.X, bounds.Origin.Y, bounds.Origin.Z },
            extent = new[] { bounds.BoxExtent.X, bounds.BoxExtent.Y, bounds.BoxExtent.Z }, radius = bounds.SphereRadius },
        materials_start = 8558, skeleton_start = 8958, skeleton_end = 32890,
        lod_start = 32898, lod_end = ar.Position, remaining_package_bytes = ar.Length - ar.Position,
        required_bones = lod.RequiredBones, active_bones = lod.ActiveBoneIndices,
        sections = lod.Sections.Select((s, i) => new { section = i, material = s.MaterialIndex,
            vertex_start = s.BaseVertexIndex, vertices = s.NumVertices, index_start = s.BaseIndex,
            triangles = s.NumTriangles, palette = s.BoneMap, max_influences = s.MaxBoneInfluences,
            cloth = s.HasClothData, cast_shadow = s.bCastShadow, visible_in_ray_tracing = s.bVisibleInRayTracing }),
        status = "Reader-validated layout only; resizing the complete asset is NOT IMPLEMENTED" };
    File.WriteAllText(Path.Combine(output, "package-layout.json"), JsonSerializer.Serialize(layout, new JsonSerializerOptions { WriteIndented = true }));
}
Console.WriteLine(JsonSerializer.Serialize(report));
