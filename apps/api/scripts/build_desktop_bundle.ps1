$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Split-Path -Parent $scriptDir

Push-Location $apiDir
try {
    uv run masterbrain-build-desktop @args
}
finally {
    Pop-Location
}
