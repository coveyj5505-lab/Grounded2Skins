$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
function Pick-Folder($message) {
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $message
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'Cancelled. No installation performed.' }
    return $dialog.SelectedPath
}
try {
    if (Get-Process -Name 'Grounded2*' -ErrorAction SilentlyContinue) { throw 'Close Grounded 2 before installing.' }
    Write-Host 'Keep your working Bo Peep skin installed. Disable the old ToyStory accessory/discovery F9 probes first.'
    $paks = Pick-Folder 'Select Grounded 2 Augusta\Content\Paks (where your working skins are installed)'
    $mods = Pick-Folder 'Select your existing UE4SS Mods folder (the one containing your FreeBuild mod)'
    if ((Split-Path $paks -Leaf) -ne 'Paks') { throw 'The first folder must be Paks.' }
    if ((Split-Path $mods -Leaf) -ne 'Mods') { throw 'The second folder must be UE4SS Mods.' }
    $dest = Join-Path $mods 'BoPeepCrook'
    $files = @('zBoCrookAsset_P.pak','zBoCrookAsset_P.utoc','zBoCrookAsset_P.ucas')
    if (Test-Path $dest) { throw 'BoPeepCrook already exists. Remove the earlier crook test before installing. Nothing overwritten.' }
    foreach ($file in $files) { if (Test-Path (Join-Path $paks $file)) { throw "Already exists: $file. Nothing overwritten." } }
    $receipt = @()
    foreach ($file in $files) {
        $src = Join-Path (Join-Path $PSScriptRoot 'Paks') $file
        $receipt += @{ path=(Join-Path $paks $file); sha256=(Get-FileHash $src -Algorithm SHA256).Hash }
    }
    foreach ($file in Get-ChildItem (Join-Path $PSScriptRoot 'UE4SS\Mods\BoPeepCrook') -File -Recurse) {
        $relative = $file.FullName.Substring((Join-Path $PSScriptRoot 'UE4SS\Mods\BoPeepCrook').Length).TrimStart('\')
        $receipt += @{ path=(Join-Path $dest $relative); sha256=(Get-FileHash $file.FullName -Algorithm SHA256).Hash }
    }
    $receipt | ConvertTo-Json | Set-Content (Join-Path $PSScriptRoot 'installed-files.json')
    foreach ($file in $files) { Copy-Item (Join-Path (Join-Path $PSScriptRoot 'Paks') $file) (Join-Path $paks $file) }
    Copy-Item (Join-Path $PSScriptRoot 'UE4SS\Mods\BoPeepCrook') $dest -Recurse
    Write-Host 'INSTALLED. Load as Bo Peep. Stand upright with both hands empty; press F9 once.' -ForegroundColor Green
    Write-Host 'Check third person and first person, then equip spear, shield only, and empty hands again.'
    Write-Host 'F9 again removes the crook. Attack animation replacement is NOT included yet.'
    Write-Host 'Send UE4SS.log plus front/side/first-person screenshots. No gliding test needed.'
} catch { Write-Host $_ -ForegroundColor Red; exit 1 }
