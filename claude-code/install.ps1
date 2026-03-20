# =============================================================================
# Claude Code Marketplace Installer (Windows PowerShell)
# =============================================================================
#
# Usage:
#   irm https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.ps1 | iex
#
# After installation, use Claude Code to install plugins:
#   /plugin install long-task@longtaskforagent
#

$ErrorActionPreference = "Stop"

# =============================================================================
# Configuration (modify these for different marketplaces)
# =============================================================================

$MarketplaceGitUrl = "https://github.com/suriyel/longtaskforagent.git"
$MarketplaceName = "longtaskforagent"

# =============================================================================
# Paths
# =============================================================================

$ClaudePluginsDir = Join-Path $env:USERPROFILE ".claude\plugins"
$MarketplacesDir = Join-Path $ClaudePluginsDir "marketplaces"
$TargetDir = Join-Path $MarketplacesDir $MarketplaceName
$KnownMarketplacesFile = Join-Path $ClaudePluginsDir "known_marketplaces.json"

# =============================================================================
# Helper Functions
# =============================================================================

function Write-Info { param($Message) Write-Host "ℹ " -ForegroundColor Blue -NoNewline; Write-Host $Message }
function Write-Success { param($Message) Write-Host "✓ " -ForegroundColor Green -NoNewline; Write-Host $Message }

# =============================================================================
# Pre-flight Check
# =============================================================================

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Error: git is not installed" -ForegroundColor Red
    exit 1
}

# =============================================================================
# Install
# =============================================================================

Write-Info "Installing marketplace: $MarketplaceName"

# Remove existing if present
if (Test-Path $TargetDir) {
    Write-Info "Removing existing installation..."
    Remove-Item $TargetDir -Recurse -Force
}

# Clone repository
Write-Info "Cloning from: $MarketplaceGitUrl"
if (-not (Test-Path $MarketplacesDir)) {
    New-Item -ItemType Directory -Force -Path $MarketplacesDir | Out-Null
}

$gitOutput = git clone --depth 1 $MarketplaceGitUrl $TargetDir 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to clone repository" -ForegroundColor Red
    Write-Host $gitOutput
    exit 1
}

# Update known_marketplaces.json
Write-Info "Registering marketplace..."
if (-not (Test-Path $ClaudePluginsDir)) {
    New-Item -ItemType Directory -Force -Path $ClaudePluginsDir | Out-Null
}

if (-not (Test-Path $KnownMarketplacesFile)) {
    "{}" | Out-File -FilePath $KnownMarketplacesFile -Encoding utf8NoBOM
}

$json = Get-Content $KnownMarketplacesFile -Raw | ConvertFrom-Json
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.000Z")

$json | Add-Member -MemberType NoteProperty -Name $MarketplaceName -Value @{
    source = @{ source = "github"; repo = "suriyel/longtaskforagent" }
    installLocation = $TargetDir
    lastUpdated = $timestamp
} -Force

# Use UTF-8 without BOM and consistent 2-space indentation
$json | ConvertTo-Json -Depth 10 | Out-File -FilePath $KnownMarketplacesFile -Encoding utf8NoBOM

# =============================================================================
# Success
# =============================================================================

Write-Host ""
Write-Host "✓ Marketplace installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Name: $MarketplaceName"
Write-Host "  Path: $TargetDir"
Write-Host ""
Write-Host "To install plugins, use Claude Code:" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "  /plugin install long-task@$MarketplaceName"
Write-Host ""
