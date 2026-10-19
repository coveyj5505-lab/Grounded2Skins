using System.Text.Json;
using System.Security.Cryptography;
using CUE4Parse.UE4.Assets.Exports.SkeletalMesh;
using CUE4Parse.UE4.Assets.Readers;
using CUE4Parse.UE4.Readers;
using CUE4Parse.UE4.Versions;
using CUE4Parse.UE4.Objects.UObject;
using CUE4Parse.UE4.Objects.Core.Math;
var input=Path.GetFullPath(args[0]);var bytes=File.ReadAllBytes(input);var hash=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
using var skeletons=JsonDocument.Parse(File.ReadAllText(args[1]));var skeleton=skeletons.RootElement.GetProperty("meshes").EnumerateArray().Single(x=>x.GetProperty("chunk_sha256").GetString()==hash);var boneCount=skeleton.GetProperty("bone_count").GetInt32();
using var headers=JsonDocument.Parse(File.ReadAllText(args[2]));var header=headers.RootElement.EnumerateArray().Single(x=>x.GetProperty("chunk_id").GetString()==Path.GetFileName(input));var names=header.GetProperty("name_map").EnumerateArray().Select(x=>x.GetString()!).ToArray();
var outDir=Path.GetFullPath(args[3]);if(Directory.Exists(outDir))throw new Exception("output must be new");Directory.CreateDirectory(outDir);
var hasColors=!args.Contains("--no-colors");
var versions=new VersionContainer(EGame.GAME_Grounded2);using var raw=new TraceArchive("CommanderNative",bytes,versions);using var ar=new NamedArchive(raw,names);
ar.Position=skeleton.GetProperty("end").GetInt64();if(!ar.ReadBoolean())throw new Exception("not cooked");if(versions["SkeletalMesh.KeepMobileMinLODSettingOnDesktop"])ar.Read<int>();var count=ar.Read<int>();if(count<1||count>16)throw new Exception($"Invalid LOD count {count}");
raw.Tracing=true;var lodStart=ar.Position;var lod=new FStaticLODModel();lod.SerializeRenderItem(ar,hasColors);if(lod.Sections is null || lod.Indices is null || lod.VertexBufferGPUSkin is null)throw new Exception("Missing native LOD buffers");var lodEnd=ar.Position;var lods=new List<object>{new{level=0,start=lodStart,end=lodEnd,vertices=lod.NumVertices,triangles=lod.Indices?.Buffer?.Length/3,sections=lod.Sections?.Length,has_cloth=lod.HasClothData(),has_morph=lod.MorphTargetVertexInfoBuffers!=null,vertex_attributes=lod.VertexAttributeBuffers?.Count}};for(int level=1;level<count;level++){var start=ar.Position;var other=new FStaticLODModel();other.SerializeRenderItem(ar,hasColors);lods.Add(new{level,start,end=ar.Position,vertices=other.NumVertices,triangles=other.Indices?.Buffer?.Length/3,sections=other.Sections?.Length,has_cloth=other.HasClothData(),has_morph=other.MorphTargetVertexInfoBuffers!=null,vertex_attributes=other.VertexAttributeBuffers?.Count});}var allLodsEnd=ar.Position;raw.Tracing=false;File.WriteAllText(Path.Combine(outDir,"native-read-layout.json"),JsonSerializer.Serialize(raw.Events,new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine($"LOD parsed {lodStart}..{lodEnd}: {lod.NumVertices} vertices, {lod.Indices?.Buffer?.Length} indices, {lod.Sections.Length} sections");
var verts=lod.VertexBufferGPUSkin.VertsFloat ?? throw new Exception("Missing vertex data");var indices=lod.Indices!.Buffer ?? throw new Exception("Missing index data");if(verts.Length!=lod.NumVertices||indices.Length%3!=0||lod.NumTexCoords!=1)throw new Exception("count/UV mismatch");
var owner=Enumerable.Repeat(-1,verts.Length).ToArray();var triSlots=new int[indices.Length/3];var triCovered=new bool[triSlots.Length];
for(var si=0;si<lod.Sections.Length;si++) {
 var sec=lod.Sections[si];if(sec.BaseIndex%3!=0||sec.BaseIndex<0||sec.NumTriangles<0)throw new Exception("invalid section");
 if(sec.BoneMap.Any(x=>x>=boneCount))throw new Exception("palette bone outside skeleton");
 for(var v=(int)sec.BaseVertexIndex;v<sec.BaseVertexIndex+sec.NumVertices;v++){if(v<0||v>=verts.Length||owner[v]!=-1)throw new Exception("vertex coverage overlap/range");owner[v]=si;}
 for(var t=sec.BaseIndex/3;t<sec.BaseIndex/3+sec.NumTriangles;t++){
  if(t>=triSlots.Length||triCovered[t])throw new Exception("triangle coverage overlap/range");triCovered[t]=true;triSlots[t]=sec.MaterialIndex;
  for(var j=0;j<3;j++){var v=indices[t*3+j];if(v<sec.BaseVertexIndex||v>=sec.BaseVertexIndex+sec.NumVertices)throw new Exception("triangle outside section vertex range");}
 }
}
if(owner.Any(x=>x<0)||triCovered.Any(x=>!x))throw new Exception("incomplete coverage");
// Recover native material records using their documented reader and require a unique
// count-prefixed array ending exactly at the independently validated skeleton.
var matEnd=skeleton.GetProperty("offset").GetInt64();var materialCandidates=new List<(long start,FSkeletalMaterial[] data)>();
for(long p=Math.Max(0,matEnd-8192);p<matEnd-4;p++){
 ar.Position=p;var n=ar.Read<int>();if(n<triSlots.Max()+1||n>64)continue;
 try{var a=new FSkeletalMaterial[n];for(var k=0;k<n;k++)a[k]=new FSkeletalMaterial(ar);if(ar.Position==matEnd)materialCandidates.Add((p,a));}catch(Exception){}
}
if(materialCandidates.Count!=1)throw new Exception($"Material array candidates: {materialCandidates.Count}");var materials=materialCandidates[0];Console.WriteLine($"Material array {materials.start}..{matEnd}: {materials.data.Length} slots");
var maxInf=verts.Max(x=>x.Infs!.BoneIndex.Length);if(maxInf>12)throw new Exception("unexpected influence count");var rawSums=new List<int>();var usedBones=new HashSet<ushort>();var nonzeroHist=new Dictionary<int,int>();var precisions=new HashSet<bool>();
BinaryWriter Open(string name)=>new(File.Open(Path.Combine(outDir,name),FileMode.CreateNew));
using(var pos=Open("positions.f32"))using(var uv=Open("uv0.f32"))using(var normals=Open("normals.f32"))using(var joints=Open("joints.u16"))using(var weights=Open("weights.f32"))using(var rawWeights=Open("weights.u16")) {
 for(var vi=0;vi<verts.Length;vi++){
  var v=verts[vi];if(!float.IsFinite(v.Pos.X)||!float.IsFinite(v.Pos.Y)||!float.IsFinite(v.Pos.Z))throw new Exception("nonfinite position");pos.Write(v.Pos.X);pos.Write(v.Pos.Y);pos.Write(v.Pos.Z);
  if(v.UVs.Length!=1||!float.IsFinite(v.UVs[0].U)||!float.IsFinite(v.UVs[0].V))throw new Exception("invalid UV");uv.Write(v.UVs[0].U);uv.Write(v.UVs[0].V);
  var normal=v.Normal[2];normals.Write(normal.X);normals.Write(normal.Y);normals.Write(normal.Z);
  var inf=v.Infs!;precisions.Add(inf.bUse16BitBoneWeight);var sum=inf.BoneWeight.Sum(x=>(int)x);if(sum==0)throw new Exception("unweighted vertex");rawSums.Add(sum);var sec=lod.Sections[owner[vi]];var nz=0;var seen=new HashSet<ushort>();
  for(var j=0;j<maxInf;j++){
   var w=j<inf.BoneWeight.Length?inf.BoneWeight[j]:(ushort)0;ushort global=0;
   if(w>0){var local=inf.BoneIndex[j];if(local>=sec.BoneMap.Length)throw new Exception("palette index out of range");global=sec.BoneMap[local];if(!seen.Add(global))throw new Exception("duplicate nonzero joint");usedBones.Add(global);nz++;}
   joints.Write(global);rawWeights.Write(w);weights.Write((float)w/sum);
  }
  if(nz>sec.MaxBoneInfluences)throw new Exception("section influence limit exceeded");nonzeroHist[nz]=nonzeroHist.GetValueOrDefault(nz)+1;
 }
}
using(var b=Open("indices.u32"))foreach(var i in indices)b.Write(i);
using(var b=Open("triangle-materials.u16"))foreach(var m in triSlots)b.Write((ushort)m);
using(var b=Open("colors.rgba8"))foreach(var c in lod.ColorVertexBuffer.Data){b.Write(c.R);b.Write(c.G);b.Write(c.B);b.Write(c.A);}
if(hasColors&&lod.ColorVertexBuffer.Data.Length!=verts.Length)throw new Exception("color count mismatch");
if(precisions.Count!=1)throw new Exception("mixed weight precision");var expectedSum=precisions.Single()?65535:255;if(rawSums.Any(x=>Math.Abs(x-expectedSum)>maxInf))throw new Exception("bad raw weight totals");
ar.Position=materials.start-56;var importedBounds=new FBoxSphereBounds(ar);if(ar.Position!=materials.start)throw new Exception("Invalid imported bounds extent");
var sections=lod.Sections.Select((x,i)=>new {section=i,material=x.MaterialIndex,index_start=x.BaseIndex,triangles=x.NumTriangles,vertex_start=x.BaseVertexIndex,vertices=x.NumVertices,palette=x.BoneMap,max_influences=x.MaxBoneInfluences}).ToArray();
var result=new {source=input,source_sha256=hash,has_vertex_colors=hasColors,lod_count=count,lods,all_lods_end=allLodsEnd,skeleton_bones=boneCount,vertices=verts.Length,triangles=indices.Length/3,uv_channels=lod.NumTexCoords,influence_stride=maxInf,used_bones=usedBones.Order().ToArray(),nonzero_influence_histogram=nonzeroHist,weight_precision_bits=precisions.Single()?16:8,raw_weight_sum_min=rawSums.Min(),raw_weight_sum_max=rawSums.Max(),expected_raw_weight_sum=expectedSum,weights_normalization="preserved integer weights plus export float weights divided by measured vertex sum",lod_start=lodStart,lod_end=lodEnd,material_start=materials.start,material_end=matEnd,materials=materials.data.Select((x,i)=>new {slot=i,name=x.MaterialSlotName.Text,package_index=x.MaterialInterface?.Index}).ToArray(),sections,required_bones=lod.RequiredBones,active_bones=lod.ActiveBoneIndices,imported_bounds=new {origin=new[]{importedBounds.Origin.X,importedBounds.Origin.Y,importedBounds.Origin.Z},extent=new[]{importedBounds.BoxExtent.X,importedBounds.BoxExtent.Y,importedBounds.BoxExtent.Z},radius=importedBounds.SphereRadius},remaining_native_tail_bytes=bytes.Length-lodEnd,vertex_colors=hasColors,validation=new {all_triangles_in_section_vertex_ranges=true,all_vertices_covered_once=true,all_triangles_covered_once=true,all_nonzero_joint_indices_mapped_through_section_palette=true,no_unweighted_vertices=true,all_positions_uvs_finite=true},bounds_cm=new {min=new[]{verts.Min(x=>x.Pos.X),verts.Min(x=>x.Pos.Y),verts.Min(x=>x.Pos.Z)},max=new[]{verts.Max(x=>x.Pos.X),verts.Max(x=>x.Pos.Y),verts.Max(x=>x.Pos.Z)}}};
File.WriteAllText(Path.Combine(outDir,"mesh.json"),JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine(JsonSerializer.Serialize(result));
class NamedArchive(FArchive source,string[] names):FAssetArchive(source,null){public override FName ReadFName(){var index=Read<int>();var number=Read<int>();if(index<0||index>=names.Length||number<0)throw new Exception("FName out of range");return new FName(names[index],index,number);}}

class TraceArchive(string name,byte[] data,VersionContainer versions):FByteArchive(name,data,versions) {
 public bool Tracing;
 public List<object> Events=new();
 public override long Position {get=>base.Position;set {var old=base.Position;if(Tracing && old>Length-256 && value!=old)Events.Add(new {kind="position",start=old,end=value,delta=value-old});base.Position=value;}}
 public override T[] ReadArray<T>(int length){var start=Position;var a=base.ReadArray<T>(length);if(Tracing && (Position-start>100000 || start>Length-256))Events.Add(new {kind="array",type=typeof(T).Name,start,end=Position,count=length});return a;}
 public override T Read<T>(){var start=Position;var a=base.Read<T>();if(Tracing && start>Length-256)Events.Add(new {kind="scalar",type=typeof(T).Name,start,end=Position,value=a});return a;}
}
