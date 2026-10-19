$ErrorActionPreference = 'Stop'
try {
    if (Get-Process -Name 'Grounded2*' -ErrorAction SilentlyContinue) { throw 'Close Grounded 2 first.' }
    $receipt = Get-Content (Join-Path $PSScriptRoot 'installed-files.json') -Raw | ConvertFrom-Json
    foreach ($entry in $receipt) {
        if (Test-Path -LiteralPath $entry.path) {
            if ((Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash -ne $entry.sha256) { throw "Changed file preserved: $($entry.path). Remove it manually if intended." }
        }
    }
    foreach ($entry in $receipt) { if (Test-Path -LiteralPath $entry.path) { Remove-Item -LiteralPath $entry.path } }
    $dirs = $receipt | ForEach-Object { Split-Path $_.path -Parent } | Where-Object { $_ -match '[\\/]BoPeepCrook([\\/]|$)' } | Sort-Object Length -Descending -Unique
    foreach ($dir in $dirs) {
        if ((Test-Path -LiteralPath $dir) -and @(Get-ChildItem -LiteralPath $dir -Force).Count -eq 0) { Remove-Item -LiteralPath $dir }
        $parent = Split-Path $dir -Parent
        if ((Split-Path $parent -Leaf) -eq 'BoPeepCrook' -and (Test-Path -LiteralPath $parent) -and @(Get-ChildItem -LiteralPath $parent -Force).Count -eq 0) { Remove-Item -LiteralPath $parent }
    }
    Write-Host 'Crook test files removed. Working skins and FreeBuild unchanged.' -ForegroundColor Green
} catch { Write-Host $_ -ForegroundColor Red; exit 1 }
