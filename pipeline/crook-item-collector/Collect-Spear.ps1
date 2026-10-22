param([string]$Retoc="",[string]$Utoc="")
$ErrorActionPreference="Stop"
try {
 Write-Host "GROUNDED 2 - CROOK NATIVE ITEM TABLES" -ForegroundColor Cyan
 Write-Host "Close the game. No mod installation or gameplay sequence is needed."
 Write-Host "This reads original game files only. No server login or character switching."
 Write-Host "Use your existing Windows retoc.exe 0.1.5 and Python 3.11+."
 Add-Type -AssemblyName System.Windows.Forms
 function Select-File([string]$Title,[string]$Filter) {
  $picker=New-Object System.Windows.Forms.OpenFileDialog
  $picker.Title=$Title;$picker.Filter=$Filter
  if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw "Cancelled. Nothing changed." }
  return $picker.FileName
 }
 if (-not $Retoc) { $Retoc=Select-File "Choose the Windows retoc.exe 0.1.5 used for previous character extractions" "retoc executable|retoc.exe" }
 if (-not $Utoc) { $Utoc=Select-File "Choose ORIGINAL Augusta-WinGDK.utoc from the UPDATED game's Content/Paks" "Original game index|Augusta-WinGDK.utoc" }
 if ([IO.Path]::GetFileName($Utoc) -ine "Augusta-WinGDK.utoc") { throw "Select ORIGINAL Augusta-WinGDK.utoc, not a mod UTOC." }
 $python=Get-Command py -ErrorAction SilentlyContinue
 if ($python) { $pyArgs=@("-3") } else { $python=Get-Command python -ErrorAction Stop;$pyArgs=@() }
 & $python.Source @pyArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
 if ($LASTEXITCODE -ne 0) { throw "Python 3.11+ is required." }
 $stamp=Get-Date -Format "yyyyMMdd-HHmmss-fff"
 $out=Join-Path ([Environment]::GetFolderPath("Desktop")) ("Grounded2-CrookItems-"+$stamp)
 Write-Host "Output and upload ZIPs: $out" -ForegroundColor Yellow
 & $python.Source @pyArgs (Join-Path $PSScriptRoot "collect_crook_items.py") --retoc $Retoc --utoc $Utoc --output $out
 $result=$LASTEXITCODE
 if ($result -notin @(0,2)) { throw "Helper could not finish. Keep any output/logs at $out and share the error shown here." }
 Write-Host "";Write-Host "UPLOAD Grounded2-CrookItems-$stamp.zip FROM YOUR DESKTOP." -ForegroundColor Green
 Write-Host "Only Table_AllItems and its actual item-table dependencies (64 MiB maximum). No repeat attack, animation, character, map or .usmap collection. Partial output is useful."
 Write-Host "No game files, saves, mods or UE4SS settings were modified."
} catch {
 Write-Host "";Write-Host $_.Exception.Message -ForegroundColor Red
 Write-Host "No game install/update action was performed. Keep any output ZIPs."
 exit 1
}
