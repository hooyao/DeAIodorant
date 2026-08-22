[CmdletBinding()]
param(
    [string]$Reviewer,
    [string]$Workspace = "data/local/translation_v2_review",
    [string]$Output = "data/local/translation_v2_review/review_decisions.csv"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".venv/Scripts/python.exe"
$workspacePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $Workspace))
$outputPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $Output))
$exportArgs = @(
    "translation_benchmark_v2.py",
    "export-review",
    "--workspace", $workspacePath,
    "--output", $outputPath
)
if ($Reviewer) {
    $exportArgs += @("--reviewer", $Reviewer)
}

Push-Location $repoRoot
try {
    & $python @exportArgs
    if ($LASTEXITCODE -ne 0) { throw "Review decision export failed." }
} finally {
    Pop-Location
}

Write-Host "Finalization-compatible decisions: $outputPath"
