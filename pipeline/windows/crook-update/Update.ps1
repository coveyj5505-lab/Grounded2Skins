$ErrorActionPreference = 'Stop'
try {
    if (Get-Process -Name 'Grounded2*' -ErrorAction SilentlyContinue) { throw 'Close Grounded 2 first.' }
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = 'Select your existing UE4SS Mods folder (contains BoPeepCrook and FreeBuild)'
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'Cancelled; nothing changed.' }
    $target = Join-Path $dialog.SelectedPath 'BoPeepCrook\Scripts\main.lua'
    if (-not (Test-Path -LiteralPath $target)) { throw 'BoPeepCrook\Scripts\main.lua not found in that folder. Nothing changed.' }
    $backup = $target + '.before-v0.1.1-' + (Get-Date -Format 'yyyyMMdd-HHmmssfff')
    Copy-Item -LiteralPath $target -Destination $backup
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'BoPeepCrook\Scripts\main.lua') -Destination $target
    Write-Host 'UPDATED. Skins, Paks, mods.txt and FreeBuild were not changed.' -ForegroundColor Green
    Write-Host 'Load as Bo Peep, stand upright with both hands empty, F9 ONCE. Wait 5 seconds.'
    Write-Host 'If crook appears, test views and equipment. If not, send UE4SS.log; no repeated F9 toggles needed.'
    Write-Host "Previous script backed up at: $backup"
} catch { Write-Host $_ -ForegroundColor Red; exit 1 }
