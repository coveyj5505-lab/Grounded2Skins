using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Assets;
using CUE4Parse.UE4.Assets.Exports;
using CUE4Parse.UE4.Assets.Exports.Engine;
using CUE4Parse.UE4.Assets.Objects;
using CUE4Parse.UE4.Assets.Readers;
using CUE4Parse.UE4.IO.Objects;
using CUE4Parse.UE4.Objects.UObject;
using CUE4Parse.UE4.Readers;
using CUE4Parse.UE4.Versions;
using Newtonsoft.Json;
Directory.CreateDirectory(args[2]);
var mappings=new FileUsmapTypeMappingsProvider(args[0]);
Console.WriteLine("Mapping structs: "+mappings.MappingsForGame.Types.Count);
var wanted=new[]{"Building","MarkerBuilding","BP_BaseBuilding_C","BP_BaseTeleport_C","BP_SurvivalTeleport_C","MapWidget","MapMarkerWidget","MapPlayerWaypointWidget","HUDMarkerData","SurvivalGameState","UI_Map_C","UI_BottomButton_C","BuildingData","BuildingRecipeData","PersistenceComponent"};
File.WriteAllText(Path.Combine(args[2],"relevant-schemas.json"),JsonConvert.SerializeObject(mappings.MappingsForGame.Types.Where(k=>wanted.Contains(k.Key)).ToDictionary(k=>k.Key,k=>new{k.Value.SuperType,k.Value.PropertyCount,Properties=k.Value.Properties.Select(p=>new{Index=p.Key,Name=p.Value.Name,Type=p.Value.MappingType.Type,Struct=p.Value.MappingType.StructType})}),Formatting.Indented));
File.WriteAllText(Path.Combine(args[2],"relevant-enums.json"),JsonConvert.SerializeObject(mappings.MappingsForGame.Enums.Where(k=>new[]{"EBuildingState","ERecipeVisibility"}.Contains(k.Key)).ToDictionary(k=>k.Key,k=>k.Value),Formatting.Indented));
var globals=JsonConvert.DeserializeObject<Dictionary<string,string>>(File.ReadAllText(args[1]));
var ver=new VersionContainer(EGame.GAME_Grounded2);
var provider=new DefaultFileProvider(Path.GetDirectoryName(Path.GetFullPath(args[0])),SearchOption.TopDirectoryOnly,ver,StringComparer.OrdinalIgnoreCase){MappingsContainer=mappings};
Directory.CreateDirectory(args[2]);
foreach(var path in args.Skip(3)){
 try {
 var data=File.ReadAllBytes(path);using var h=new FByteArchive(path,data,ver);var s=new FZenPackageSummary(h);
 if(s.bHasVersioningInfo!=0)throw new Exception("Versioned package needs explicit handling");
 h.Position+=8;var names=FNameEntrySerialized.LoadNameBatch(h);h.Position=s.ImportMapOffset;
 var imports=h.ReadArray<ulong>((s.ExportMapOffset-s.ImportMapOffset)/8);h.Position=s.ExportMapOffset;
 var exports=Enumerable.Range(0,(s.ExportBundleEntriesOffset-s.ExportMapOffset)/72).Select(_=>new FExportMapEntry(h)).ToArray();
 h.Position=s.ImportedPackageNamesOffset;var packages=FNameEntrySerialized.LoadNameBatch(h).Select(n=>n.Name).ToArray();
 h.Position=s.ImportedPublicExportHashesOffset;var hashes=h.ReadArray<ulong>((s.ImportMapOffset-s.ImportedPublicExportHashesOffset)/8);
 var ctx=new Context(names,imports,exports,packages,hashes,globals,s.PackageFlags,provider);
 foreach(var e in exports){
 var cls=ctx.ResolveObject(e.ClassIndex.TypeAndId);
 if(cls.Name.Text is not ("DataTable" or "CompositeDataTable"))continue;
 var name=names[e.ObjectName.NameIndex].Name;var table=cls.Name.Text=="CompositeDataTable"?new UCompositeDataTable():new UDataTable();table.Name=name;table.Class=cls;table.Outer=new ResolvedPackageObject(ctx);
 var offset=(int)s.HeaderSize+(int)e.CookedSerialOffset;var end=offset+(int)e.CookedSerialSize;
 using var ar=new FAssetArchive(new FByteArchive(name,data,ver),ctx);ar.Position=offset;
 table.Deserialize(ar,end);
 if(ar.Position!=end)throw new Exception($"Unconsumed bytes {end-ar.Position}");
 if(table.RowMap==null)throw new Exception("Rows were not decoded");
 var rowType=table.Get<FPackageIndex>("RowStruct").Name;
 var schema=mappings.MappingsForGame.Types[rowType];
 var schemaOutput=new {row_struct=rowType,schema.PropertyCount,Properties=schema.Properties.Select(p=>new{Index=p.Key,Name=p.Value.Name,Type=p.Value.MappingType.Type,Struct=p.Value.MappingType.StructType})};
 File.WriteAllText(Path.Combine(args[2],Path.GetFileName(path)+"-"+name+".schema.json"),JsonConvert.SerializeObject(schemaOutput,Formatting.Indented));
 using var rowAr=new FAssetArchive(new FByteArchive(name,data,ver),ctx);rowAr.Position=offset;
 var objectHeader=new UObject{Name=name,Class=cls,Outer=new ResolvedPackageObject(ctx)};objectHeader.Deserialize(rowAr,end);
 var countPosition=rowAr.Position;var count=rowAr.Read<int>();var layouts=new List<object>();
 for(int row=0;row<count;row++){
  var rowStart=rowAr.Position;var rowName=rowAr.ReadFName();var valueStart=rowAr.Position;
  var uh=new CUE4Parse.UE4.Assets.Objects.Unversioned.FUnversionedHeader(rowAr);var bodyStart=rowAr.Position;
  var indices=new List<(int index,bool nonzero)>();if(uh.HasValues){using var it=new CUE4Parse.UE4.Assets.Objects.Unversioned.FIterator(uh);do{indices.Add(it.Current);}while(it.MoveNext());}
  rowAr.Position=valueStart;var value=new FStructFallback(rowAr,rowType);var rowEnd=rowAr.Position;long cursor=bodyStart;var props=new List<object>();
  if(indices.Count!=value.Properties.Count)throw new Exception("Row schema/property count mismatch");
  for(int v=0;v<indices.Count;v++){
   var prop=value.Properties[v];var children=new List<object>();
   if(prop.Size>0 && prop.Tag?.GenericValue is FScriptStruct script && script.StructType is FStructFallback nested){
    using var nestedAr=new FAssetArchive(new FByteArchive(name,data,ver),ctx);nestedAr.Position=cursor;
    _=new CUE4Parse.UE4.Assets.Objects.Unversioned.FUnversionedHeader(nestedAr);var nestedCursor=nestedAr.Position;
    foreach(var child in nested.Properties){children.Add(new{Name=child.Name.Text,Position=nestedCursor,child.Size});nestedCursor+=child.Size;}
    if(nestedCursor!=cursor+prop.Size)throw new Exception("Nested property size mismatch");
   }
   props.Add(new{Name=prop.Name.Text,Index=indices[v].index,NonZero=indices[v].nonzero,Position=cursor,prop.Size,Children=children});cursor+=prop.Size;
  }
  if(cursor!=rowEnd)throw new Exception("Property size mismatch");
  layouts.Add(new{Name=rowName.Text,Start=rowStart,End=rowEnd,ValueStart=valueStart,BodyStart=bodyStart,Properties=props});
 }
 if(rowAr.Position!=end)throw new Exception("Layout parse did not consume export");
 File.WriteAllText(Path.Combine(args[2],Path.GetFileName(path)+"-"+name+".layout.json"),JsonConvert.SerializeObject(new{SourceSHA256=Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(data)).ToLowerInvariant(),CountPosition=countPosition,Rows=layouts},Formatting.Indented));
 var output=Path.Combine(args[2],Path.GetFileName(path)+"-"+name+".json");
 File.WriteAllText(output,JsonConvert.SerializeObject(table,Formatting.Indented));
 Console.WriteLine($"PASS {name}: {table.RowMap.Count} rows; consumed {ar.Position-offset}/{end-offset} bytes");
 }
 }catch(Exception ex){Console.WriteLine("FAIL "+Path.GetFileName(path)+": "+ex);}
}
sealed class Context(FNameEntrySerialized[] names,ulong[] imports,FExportMapEntry[] exports,string[] packages,ulong[] hashes,Dictionary<string,string> globals,EPackageFlags flags,DefaultFileProvider provider):AbstractUePackage("CatalogReview",provider){
 public override FPackageFileSummary Summary=>new(){PackageFlags=flags};public override FNameEntrySerialized[] NameMap=>names;public override int ImportMapLength=>imports.Length;public override int ExportMapLength=>exports.Length;
 public override int GetExportIndex(string n,StringComparison t=StringComparison.Ordinal)=>throw new NotSupportedException();
 public ResolvedObject ResolveObject(ulong id){
  if(id==ulong.MaxValue)return null;
  if((id>>62)==0)return new Named(this,names[exports[(int)id].ObjectName.NameIndex].Name);
  if((id>>62)==1){var path=globals[id.ToString("x16")];var leaf=path.Split('/').Last();return new Named(this,leaf,path);}
  var package=packages[(int)((id&0x3fffffffffffffffUL)>>32)];return new Named(this,package.Split('/').Last(),package+" [hash "+hashes[(uint)id].ToString("x16")+"]");
 }
 public override ResolvedObject ResolvePackageIndex(FPackageIndex? i)=>i==null||i.IsNull?null:ResolveObject(i.Index>0?(ulong)(i.Index-1):imports[-i.Index-1]);
}
sealed class Named(IPackage p,string n,string full=null):ResolvedObject(p){public override FName Name=>new FName(n);public override Lazy<UObject> Object=>new(()=>new UScriptClass(n));}
