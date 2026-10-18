param([string]$Retoc="", [string]$Utoc="")
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
function Select-File([string]$Title,[string]$Filter) {
 $picker=New-Object System.Windows.Forms.OpenFileDialog
 $picker.Title=$Title; $picker.Filter=$Filter
 if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw "Cancelled; no game files changed." }
 return $picker.FileName
}
if (-not $Retoc) { $Retoc=Select-File "Choose Windows retoc.exe (version 0.1.5)" "retoc executable|retoc.exe" }
if (-not $Utoc) { $Utoc=Select-File "Choose ORIGINAL Augusta-WinGDK.utoc in the game's Paks folder" "Original game index|Augusta-WinGDK.utoc" }
if ([IO.Path]::GetFileName($Utoc) -ine "Augusta-WinGDK.utoc") { throw "Select the ORIGINAL Augusta-WinGDK.utoc, not a mod index." }
$python=Get-Command py -ErrorAction SilentlyContinue
if ($python) { $pythonArgs=@("-3") } else {
 $python=Get-Command python -ErrorAction SilentlyContinue
 if (-not $python) { throw "Python 3.11+ is required. Install it from python.org, then run this helper again." }
 $pythonArgs=@()
}
& $python.Source @pythonArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
if ($LASTEXITCODE -ne 0) { throw "Python 3.11+ is required. Install/update Python, then retry." }
$stamp=Get-Date -Format "yyyyMMdd-HHmmss-fff"
$out=Join-Path ([Environment]::GetFolderPath("Desktop")) ("Grounded2-StockMax-"+$stamp)
$pythonArgs+=@((Join-Path $PSScriptRoot "extract_selected.py"),"--retoc",$Retoc,"--utoc",$Utoc,"--output",$out,"--targets",(Join-Path $PSScriptRoot "targets.json"))
# Exact original UTOC only. No Paks-directory context/override lookup is used.
& $python.Source @pythonArgs
if ($LASTEXITCODE -ne 0) { throw "Extraction incomplete. Keep output/logs at $out. No game files were changed." }
$zip=$out+".zip"
Compress-Archive -LiteralPath @((Join-Path $out "chunks"),(Join-Path $out "extraction-report.json")) -DestinationPath $zip
Write-Host "Finished. Share this ZIP for comparison: $zip"
Write-Host "Original game files and installed mods were not modified."
