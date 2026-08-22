[CmdletBinding()]
param(
    [string]$DgxHost = "gx10",
    [string]$Endpoint = "http://192.168.1.200:8000/v1",
    [int]$BatchSize = 16
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".venv/Scripts/python.exe"
$model = "qwen3.8-27b"
$modelDigest = "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab"
$triageDir = "data/local/translation_v2_review/triage_qwen38"

ssh $DgxHost "docker start qwen38-vllm-instanttensor" | Out-Null
$ready = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        Invoke-RestMethod -Uri "$Endpoint/models" -TimeoutSec 3 | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds 3
    }
}
if (-not $ready) { throw "Qwen3.8-27B did not become ready on DGX Spark." }

Push-Location $repoRoot
try {
    & $python translation_benchmark_v2.py triage-review `
        --decisions data/local/translation_v2_review/human_review_decisions_merged.csv `
        --output-dir $triageDir `
        --model $model --model-digest $modelDigest `
        --backend openai --endpoint $Endpoint --concurrency $BatchSize --routing-only
    if ($LASTEXITCODE -ne 0) { throw "Qwen3.8 provenance triage failed." }

    & $python translation_benchmark_v2.py triage-value `
        --provenance-results "$triageDir/triage_results.jsonl" `
        --output-dir "$triageDir/value" `
        --model $model --model-digest $modelDigest `
        --backend openai --endpoint $Endpoint --concurrency $BatchSize
    if ($LASTEXITCODE -ne 0) { throw "Qwen3.8 research-value triage failed." }

    & $python translation_benchmark_v2.py publish-value-review
    if ($LASTEXITCODE -ne 0) { throw "Research-value review publication failed." }
} finally {
    Pop-Location
}
