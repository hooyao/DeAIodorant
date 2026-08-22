[CmdletBinding()]
param(
    [ValidateRange(1, 100)]
    [int]$TargetPerCell = 2,

    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$RunName = ("run-" + (Get-Date -Format "yyyyMMdd-HHmmss")),

    [string]$TranslationModel = "qwen3.5:9b",

    [switch]$WithoutTranslationModel,
    [switch]$SkipModelPull,
    [switch]$SkipInstall,
    [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$VirtualPython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
$OutputDirectory = Join-Path $RepositoryRoot ("data\local\" + $RunName)

Push-Location $RepositoryRoot
try {
    if (-not (Test-Path -LiteralPath $VirtualPython -PathType Leaf)) {
        Write-Host "Creating .venv with the available Python launcher..."
        $PythonLauncher = Get-Command python -ErrorAction SilentlyContinue
        if ($PythonLauncher) {
            & $PythonLauncher.Source -m venv .venv
        }
        elseif (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3 -m venv .venv
        }
        else {
            throw "Python 3.10 or newer is required."
        }
        if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
    }

    if (-not $SkipInstall) {
        Write-Host "Installing DeAIodorant and development dependencies into .venv..."
        & $VirtualPython -m pip install -e ".[dev]"
        if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    }

    if (-not $SkipChecks) {
        Write-Host "Running offline tests and bytecode compilation..."
        & $VirtualPython -m pytest
        if ($LASTEXITCODE -ne 0) { throw "The offline test suite failed." }
        & $VirtualPython -m compileall -q src pilot_collect.py translation_eval.py translation_holdout.py translation_final_test.py
        if ($LASTEXITCODE -ne 0) { throw "Python compilation checks failed." }
    }

    if (-not $WithoutTranslationModel) {
        if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
            throw "Ollama is required unless -WithoutTranslationModel is specified."
        }
        if (-not $SkipModelPull) {
            $InstalledModels = & ollama list
            if ($LASTEXITCODE -ne 0) { throw "Ollama is not reachable." }
            if (-not ($InstalledModels -match [regex]::Escape($TranslationModel))) {
                Write-Host "Downloading optional local translation model $TranslationModel..."
                & ollama pull $TranslationModel
                if ($LASTEXITCODE -ne 0) { throw "Ollama model download failed." }
            }
        }
    }

    $PipelineArguments = @(
        "-m", "deaiodorant.corpus.pipeline",
        "--output-dir", $OutputDirectory,
        "--target-per-cell", $TargetPerCell
    )
    if ($WithoutTranslationModel) {
        $PipelineArguments += "--without-translation-model"
    }
    else {
        $PipelineArguments += @("--translation-model", $TranslationModel)
    }

    Write-Host "Starting diagnostic corpus run: $RunName"
    & $VirtualPython @PipelineArguments
    if ($LASTEXITCODE -ne 0) { throw "Corpus pipeline failed." }
    Write-Host "Corpus pipeline completed: $OutputDirectory"
}
finally {
    Pop-Location
}
