[CmdletBinding()]
param(
    [string]$Workspace = "data/local/translation_v2_review"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$workspacePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $Workspace))
$pidPath = Join-Path $workspacePath "label_studio.pid"

if (-not (Test-Path -LiteralPath $pidPath)) {
    Write-Host "No Label Studio process record was found."
    exit 0
}

$servicePid = [int](Get-Content -Raw $pidPath)
$processRows = @(Get-CimInstance Win32_Process)
$processIds = [System.Collections.Generic.List[int]]::new()
$processIds.Add($servicePid)
for ($index = 0; $index -lt $processIds.Count; $index++) {
    $parentId = $processIds[$index]
    $processRows |
        Where-Object ParentProcessId -eq $parentId |
        ForEach-Object { $processIds.Add([int]$_.ProcessId) }
}
for ($index = $processIds.Count - 1; $index -ge 0; $index--) {
    Stop-Process -Id $processIds[$index] -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath $pidPath
Write-Host "Label Studio stopped. Review data remains in $workspacePath"
