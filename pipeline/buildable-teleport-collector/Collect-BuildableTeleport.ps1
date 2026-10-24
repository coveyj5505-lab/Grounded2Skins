param([string]$Retoc="", [string]$Source="")
$ErrorActionPreference="Stop"
try {
 Write-Host "GROUNDED 2 - BUILDABLE TELEPORT / CONSTRUCTION FOLLOW-UP" -ForegroundColor Cyan
 Write-Host "Close the game. This reads original files; it installs nothing and does not touch saves."
 Add-Type -AssemblyName System.Windows.Forms
 function Select-File([string]$Title, [string]$Filter) {
  $picker=New-Object System.Windows.Forms.OpenFileDialog
  $picker.Title=$Title; $picker.Filter=$Filter
  if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw "Cancelled. Nothing changed." }
  return $picker.FileName
 }
 if (-not $Retoc) { $Retoc=Select-File "Choose your existing Windows retoc.exe 0.1.5" "retoc executable|retoc.exe" }
 if (-not $Source) { $Source=Select-File "Choose ORIGINAL Augusta-WinGDK.pak or Augusta-WinGDK.utoc" "Original game container|Augusta-WinGDK.pak;Augusta-WinGDK.utoc" }
 $python=Get-Command py -ErrorAction SilentlyContinue
 if ($python) { $pyArgs=@("-3") } else { $python=Get-Command python -ErrorAction Stop; $pyArgs=@() }
 & $python.Source @pyArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
 if ($LASTEXITCODE -ne 0) { throw "Python 3.11+ is required." }
 $stamp=Get-Date -Format "yyyyMMdd-HHmmss-fff"
 $out=Join-Path ([Environment]::GetFolderPath("Desktop")) ("Grounded2-BuildableTeleport-"+$stamp)
 & $python.Source @pyArgs (Join-Path $PSScriptRoot "collect_buildable_teleport.py") --retoc $Retoc --source $Source --output $out
 if ($LASTEXITCODE -notin @(0,2)) { throw "Collector failed. Keep any logs at $out and share the error." }
 Write-Host "Upload ONE Grounded2-BuildableTeleport-$stamp.zip from your Desktop. Partial output is useful." -ForegroundColor Green
 Write-Host "Maximum 32 logic/table packages / 64 MiB decoded, plus global metadata pair up to 16 MiB. No models or textures."
} catch {
 Write-Host $_.Exception.Message -ForegroundColor Red
 exit 1
}
