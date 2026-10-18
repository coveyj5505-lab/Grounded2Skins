param(
 [Parameter(Mandatory=$true)][string]$Retoc,
 [Parameter(Mandatory=$true)][string]$Utoc,
 [Parameter(Mandatory=$true)][string]$Output,
 [string]$LegacyContext = ""
)
$ErrorActionPreference = "Stop"
$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) { $pythonArgs = @("-3") } else {
 $python = Get-Command python -ErrorAction Stop
 $pythonArgs = @()
}
$pythonArgs += @((Join-Path $PSScriptRoot "extract_selected.py"), "--retoc", $Retoc, "--utoc", $Utoc, "--output", $Output)
if ($LegacyContext) { $pythonArgs += @("--legacy-context", $LegacyContext) }
& $python.Source @pythonArgs
exit $LASTEXITCODE
