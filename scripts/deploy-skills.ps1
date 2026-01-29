<#
.SYNOPSIS
    Infects a target project with the Antigravity Skill Ecosystem.
.DESCRIPTION
    Copies the .agent directory (Skills & Workflows) to a target path.
    Enforces the creation of ACTIVITY_LOG.md.
    Delivers a sarcastic confirmation message.
.PARAMETER TargetPath
    The absolute path to the victim (I mean, target) project.
.EXAMPLE
    .\deploy-skills.ps1 -TargetPath "C:\Projects\MyNewApp"
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$TargetPath
)

$SourcePath = "$PSScriptRoot\..\.agent"
$TargetAgentPath = Join-Path -Path $TargetPath -ChildPath ".agent"
$TargetLogPath = Join-Path -Path $TargetPath -ChildPath "ACTIVITY_LOG.md"

Write-Host "💀 Initiating Skill Injection Protocol..." -ForegroundColor Cyan
Write-Host "   Source: $SourcePath" -ForegroundColor Gray
Write-Host "   Target: $TargetAgentPath" -ForegroundColor Gray

# 1. Validate Source
if (-not (Test-Path $SourcePath)) {
    Write-Error "CRITICAL: The source .agent folder is missing. Did you delete your own brain?"
    exit 1
}

# 2. Validate Target
if (-not (Test-Path $TargetPath)) {
    Write-Host "   Target does not exist. Creating it..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $TargetPath | Out-Null
}

# 3. Copy .agent (Skills & Workflows)
Write-Host "   Copying neural pathways..." -ForegroundColor Green
Copy-Item -Path $SourcePath -Destination $TargetAgentPath -Recurse -Force

# 4. Enforce Activity Log
if (-not (Test-Path $TargetLogPath)) {
    Write-Host "   Enforcing Audit Protocols (Creating ACTIVITY_LOG.md)..." -ForegroundColor Yellow
    $InitialLog = "# Activity Log`n`n## [$(Get-Date -Format 'yyyy-MM-dd HH:mm')] SYSTEM INITIALIZATION`n- Action: Deployment via deploy-skills.ps1.`n- Status: Skills injected. Agent is now watching.`n"
    Set-Content -Path $TargetLogPath -Value $InitialLog
} else {
    Write-Host "   ACTIVITY_LOG.md detected. Appending entry..." -ForegroundColor Gray
    Add-Content -Path $TargetLogPath -Value "`n## [$(Get-Date -Format 'yyyy-MM-dd HH:mm')] SYSTEM UPDATE`n- Action: Skills refreshed via deployment script.`n- Status: Capabilities upgraded.`n"
}

Write-Host "`n🎉 INJECTION COMPLETE." -ForegroundColor Magenta
Write-Host "   The target project is now smarter than it was 5 seconds ago." -ForegroundColor Cyan
Write-Host "   REMEMBER: Open the project and check .agent/memory.md to start." -ForegroundColor Cyan
