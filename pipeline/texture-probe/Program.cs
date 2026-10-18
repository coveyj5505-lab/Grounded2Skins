using System.Security.Cryptography;
using System.Text.Json;
using System.Text;
using System.Reflection;
using System.Runtime.InteropServices;
using CUE4Parse.UE4.Objects.UObject;
using CUE4Parse.UE4.IO.Objects;
using CUE4Parse.UE4.Assets;
using CUE4Parse.UE4.Assets.Readers;
using CUE4Parse.UE4.Assets.Utils;
using CUE4Parse.UE4.Assets.Exports.Texture;
using CUE4Parse.UE4.Readers;
using CUE4Parse.UE4.Versions;
var path=Path.GetFullPath(args[0]);var output=Path.GetFullPath(args[1]);if(Directory.Exists(output))throw new Exception("New output required");Directory.CreateDirectory(output);
var version=new VersionContainer(EGame.GAME_Grounded2);
var head=File.ReadAllBytes(path+".uasset");var exp=File.ReadAllBytes(path+".uexp");var bulk=File.ReadAllBytes(path+".ubulk");
using var ha=new FByteArchive("TextureHeader",head,version);using var ea=new FByteArchive("TextureExport",exp,version);using var ba=new FByteArchive("TextureBulk",bulk,version);
// Read only real serialized header metadata. Package's full-export constructor
// requests mappings even when exports are never used; avoid that unrelated path.
var summary=new FPackageFileSummary(ha);var package=new HeaderContext(summary);
using var hctx=new FAssetArchive(ha,package);hctx.Position=summary.DataResourceOffset;
var resourceVersion=(EObjectDataResourceVersion)hctx.Read<uint>();if(resourceVersion is <= EObjectDataResourceVersion.Invalid or > EObjectDataResourceVersion.Latest)throw new Exception("Resource version");
var resources=hctx.ReadArray(()=>new FObjectDataResource(hctx,resourceVersion));
using var mapBytes=new MemoryStream();using(var writer=new BinaryWriter(mapBytes,Encoding.UTF8,true))foreach(var r in resources){if(r.RawSize!=r.SerialSize)throw new Exception("Compressed resource metadata unsupported");writer.Write(r.SerialOffset);writer.Write(r.DuplicateSerialOffset);writer.Write(r.SerialSize);writer.Write(r.LegacyBulkDataFlags);writer.Write(r.CookedIndex.Value);writer.Write(new byte[3]);}
var nativeMap=MemoryMarshal.Cast<byte,FBulkDataMapEntry>(mapBytes.ToArray()).ToArray();
using var ar=new FAssetArchive(ea,package,head.Length);ar.AddPayload(PayloadType.UBULK,new FAssetArchive(ba,package));
// Supply the measured resource table through the reader's realm-context slot.
typeof(FAssetArchive).GetField("BulkDataMap",BindingFlags.Instance|BindingFlags.NonPublic)!.SetValue(ar,nativeMap);
if(!ar.IsFilterEditorOnly)throw new Exception("Expected actual cooked/filter-editor package flags");
var candidates=new List<int>();foreach(var format in new[]{"PF_DXT5","PF_DXT1","PF_BC5"}){var needle=Encoding.ASCII.GetBytes(format+"\0");for(int i=32;i<=exp.Length-needle.Length;i++)if(exp.AsSpan(i,needle.Length).SequenceEqual(needle)&&BitConverter.ToInt32(exp,i-4)==needle.Length)candidates.Add(i-32);}
if(candidates.Count!=1)throw new Exception("Native platform candidate must be unique");ar.Position=candidates[0];var start=ar.Position;var data=new FTexturePlatformData(ar,new UTexture2D());var end=ar.Position;
if(data.VTData!=null||data.Mips.Length<1)throw new Exception("Only conventional cooked 2D textures supported");var records=new List<object>();
for(int i=0;i<data.Mips.Length;i++){var mip=data.Mips[i];var payload=mip.BulkData?.Data??throw new Exception("Unreadable mip");var bytesPerBlock=data.PixelFormat=="PF_DXT1"?8:16;var count=Math.Max(1,(mip.SizeX+3)/4)*Math.Max(1,(mip.SizeY+3)/4)*bytesPerBlock;if(payload.Length!=count||mip.SizeZ!=1)throw new Exception("Invalid block size/depth");File.WriteAllBytes(Path.Combine(output,$"mip-{i:D2}.bin"),payload);records.Add(new{level=i,width=mip.SizeX,height=mip.SizeY,bytes=payload.Length,sha256=Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant(),flags=(uint)mip.BulkData!.Header.BulkDataFlags,offset=mip.BulkData.Header.OffsetInFile});}
var report=new{pixel_format=data.PixelFormat,width=data.SizeX,height=data.SizeY,mip_count=data.Mips.Length,first_mip=data.FirstMipToSerialize,platform_start=start,platform_end=end,actual_package_flags=(uint)package.Summary.PackageFlags,mips=records,reader="Unmodified CUE4Parse FTexturePlatformData/FTexture2DMipMap/FByteBulkData, actual retoc legacy header and bulk context; no UObject property deserialization"};File.WriteAllText(Path.Combine(output,"texture.json"),JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine(JsonSerializer.Serialize(report));

sealed class HeaderContext(FPackageFileSummary summary):AbstractUePackage("MeasuredTextureHeader",null){
 public override FPackageFileSummary Summary=>summary;
 public override FNameEntrySerialized[] NameMap=>[];
 public override int ImportMapLength=>0;public override int ExportMapLength=>0;
 public override int GetExportIndex(string name,StringComparison comparisonType=StringComparison.Ordinal)=>throw new NotSupportedException();
 public override ResolvedObject? ResolvePackageIndex(FPackageIndex? index)=>throw new NotSupportedException();
}
