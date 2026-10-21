param([string]$Retoc="",[string]$Utoc="")
$ErrorActionPreference="Stop"
try {
 Write-Host "GROUNDED 2 - FOUR TEXTURE TEMPLATES" -ForegroundColor Cyan
 Write-Host "Close the game. Leave UE4SS disabled and the removed mods outside Paks."
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
 $out=Join-Path ([Environment]::GetFolderPath("Desktop")) ("Grounded2-TextureTemplates-"+$stamp)
 Write-Host "Output and upload ZIPs: $out" -ForegroundColor Yellow
 & $python.Source @pyArgs (Join-Path $PSScriptRoot "collect_textures.py") --retoc $Retoc --utoc $Utoc --output $out
 $result=$LASTEXITCODE
 if ($result -notin @(0,2)) { throw "Helper could not finish. Keep any output/logs at $out and share the error shown here." }
 Write-Host "";Write-Host "UPLOAD Grounded2-TextureTemplates-$stamp.zip FROM YOUR DESKTOP." -ForegroundColor Green
 Write-Host "Only four texture assets; do not redo the four character collections. Partial output is useful too."
 Write-Host "No game files, saves, mods or UE4SS settings were modified."
} catch {
 Write-Host "";Write-Host $_.Exception.Message -ForegroundColor Red
 Write-Host "No game install/update action was performed. Keep any output ZIPs."
 exit 1
}
