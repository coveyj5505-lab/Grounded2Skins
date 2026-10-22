using System.Text.Json;
using CUE4Parse.Compression;
using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Versions;
using CUE4Parse.UE4.Assets.Exports.Animation;
using Newtonsoft.Json;
var output=args[2];Directory.CreateDirectory(output);
var mappings=new FileUsmapTypeMappingsProvider(args[1]);
var wanted=new[]{"AnimSequence","AnimSequenceBase","AnimMontage","AnimNotifyEvent","AttackData","DamageData","BaseItemData","SurvivalPlayerCharacter","SurvivalGameModeSettings","Item"};
var types=mappings.MappingsForGame!.Types.Where(x=>wanted.Contains(x.Key)).ToDictionary(x=>x.Key,x=>new{ x.Value.Name,x.Value.SuperType,x.Value.PropertyCount,Properties=x.Value.Properties.Select(p=>new{Index=p.Key,Name=p.Value.Name,Type=p.Value.MappingType.Type,StructType=p.Value.MappingType.StructType})});
File.WriteAllText(Path.Combine(output,"mapping-summary.json"),System.Text.Json.JsonSerializer.Serialize(new{Types=mappings.MappingsForGame.Types.Count,Enums=mappings.MappingsForGame.Enums.Count,Selected=types},new JsonSerializerOptions{WriteIndented=true}));
OodleHelper.Initialize("/workspace/mod-work/bin/liboo2corelinux64.so.9");
using var provider=new DefaultFileProvider(args[0],SearchOption.TopDirectoryOnly,new VersionContainer(EGame.GAME_UE5_7),StringComparer.OrdinalIgnoreCase);
provider.ReadScriptData=args.Contains("--bytecode");provider.MappingsContainer=mappings;provider.Initialize();await provider.MountAsync();provider.PostMount();
var results=new List<object>();
foreach(var file in provider.Files.Values.Where(f=>f.Path.EndsWith(".uasset",StringComparison.OrdinalIgnoreCase)).OrderBy(f=>f.Path)){
 try{
  var package=provider.LoadPackage(file);var exports=package.GetExports().ToArray();
  foreach(var export in exports){
   File.WriteAllText(Path.Combine(output,export.Name+".json"),JsonConvert.SerializeObject(export,Formatting.Indented));
  }
  results.Add(new{Path=file.Path,Success=true,Exports=exports.Select(x=>new{x.Name,Type=x.GetType().Name})});
 }catch(Exception e){results.Add(new{Path=file.Path,Success=false,Error=e.ToString()});Console.WriteLine(file.Path+": "+e.Message);}
}
File.WriteAllText(Path.Combine(output,"results.json"),System.Text.Json.JsonSerializer.Serialize(results,new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine($"Mappings loaded: {mappings.MappingsForGame.Types.Count}; packages: {results.Count}");
