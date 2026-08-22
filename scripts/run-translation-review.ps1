[CmdletBinding()]
param(
    [string]$Reviewer,
    [int]$Port = 8080,
    [string]$Workspace = "data/local/translation_v2_review"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Project virtual environment not found. Run the repository setup first."
}

$workspacePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $Workspace))
$prepareArgs = @(
    "translation_benchmark_v2.py",
    "prepare-review",
    "--workspace", $workspacePath,
    "--port", $Port
)
if ($Reviewer) {
    $prepareArgs += @("--reviewer", $Reviewer)
}

Push-Location $repoRoot
try {
    & $python @prepareArgs
    if ($LASTEXITCODE -ne 0) { throw "Review workspace preparation failed." }

    $runtime = Join-Path $workspacePath "label_studio_venv"
    $runtimePython = Join-Path $runtime "Scripts/python.exe"
    $labelStudio = Join-Path $runtime "Scripts/label-studio.exe"
    if (-not (Test-Path -LiteralPath $labelStudio)) {
        & $python -m venv $runtime
        if ($LASTEXITCODE -ne 0) { throw "Label Studio virtual environment creation failed." }
        & $runtimePython -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) { throw "Label Studio pip bootstrap failed." }
        & $runtimePython -m pip install -r (Join-Path $workspacePath "label_studio_requirements.txt")
        if ($LASTEXITCODE -ne 0) { throw "Label Studio installation failed." }
    }

    & $runtimePython -m pip freeze |
        Set-Content -Encoding utf8 (Join-Path $workspacePath "label_studio_runtime_packages.txt")

    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connection) {
        Get-Content (Join-Path $workspacePath ".env") | ForEach-Object {
            if ($_ -and -not $_.StartsWith("#") -and $_.Contains("=")) {
                $name, $value = $_.Split("=", 2)
                Set-Item -Path "Env:$name" -Value $value
            }
        }
        $env:LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK = "true"
        $env:PYTHONPATH = Join-Path $repoRoot "src"
        $env:DJANGO_SETTINGS_MODULE = "deaiodorant.corpus.label_studio_settings"
        $dataDir = Join-Path $workspacePath "label_studio_data"
        New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
        $stdout = Join-Path $workspacePath "label_studio.stdout.log"
        $stderr = Join-Path $workspacePath "label_studio.stderr.log"
        $process = Start-Process -FilePath $labelStudio -ArgumentList @(
            "start", "--no-browser", "--internal-host", "127.0.0.1",
            "--port", $Port, "--data-dir", $dataDir,
            "--enable-legacy-api-token", "--log-level", "WARNING"
        ) -WindowStyle Hidden -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr -PassThru
        Set-Content -Encoding ascii -Path (Join-Path $workspacePath "label_studio.pid") `
            -Value $process.Id
    }

    & $python translation_benchmark_v2.py bootstrap-review --workspace $workspacePath
    if ($LASTEXITCODE -ne 0) { throw "Label Studio project initialization failed." }
} finally {
    Pop-Location
}

$manifest = Get-Content -Raw (Join-Path $workspacePath "workspace_manifest.json") |
    ConvertFrom-Json
$credentials = Join-Path $workspacePath "OPEN_ME_credentials.txt"

Write-Host "Review workspace is ready."
Write-Host "Login details: $credentials"
Write-Host "Review page: $($manifest.project_url)"
Start-Process $manifest.project_url
