[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Reviewer
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".venv/Scripts/python.exe"

Push-Location $repoRoot
try {
    & $python translation_benchmark_v2.py export-value-review --reviewer $Reviewer
    if ($LASTEXITCODE -ne 0) { throw "Research-value review export failed." }
} finally {
    Pop-Location
}
