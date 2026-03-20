# =============================================================================
# Claude Code Marketplace Installer (Windows PowerShell)
# =============================================================================
#
# Usage:
#   # Install default marketplace (suriyel/longtaskforagent)
#   irm https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.ps1 | iex
#
#   # Install from a different source
#   irm ... | iex -Args "<source> [--name <name>] [--update] [--force]"
#
# Examples:
#   # Default - installs suriyel/longtaskforagent
#   irm https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.ps1 | iex
#
#   # GitHub shorthand
#   irm ... | iex -Args "owner/repo"
#
#   # GitLab
#   irm ... | iex -Args "https://gitlab.com/company/plugins.git --name company-plugins"
#
#   # Self-hosted Git (SSH)
#   irm ... | iex -Args "git@git.example.com:team/plugins.git"
#
#   # Local path (development)
#   irm ... | iex -Args ".\my-marketplace --name test-market"
#
# After installation, use Claude Code to install plugins:
#   /plugin install <plugin-name>@<marketplace-name>
#

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# =============================================================================
# Configuration
# =============================================================================

$ClaudePluginsDir = Join-Path $env:USERPROFILE ".claude\plugins"
$MarketplacesDir = Join-Path $ClaudePluginsDir "marketplaces"
$KnownMarketplacesFile = Join-Path $ClaudePluginsDir "known_marketplaces.json"
$MarketplaceManifest = ".claude-plugin\marketplace.json"

# =============================================================================
# Configurable Marketplace Defaults
# =============================================================================

# The default marketplace to install when no source is specified
# Format: GitHub shorthand (owner/repo)
$DefaultMarketplaceOwner = "suriyel"
$DefaultMarketplaceRepo = "longtaskforagent"
$DefaultSource = "${DefaultMarketplaceOwner}/${DefaultMarketplaceRepo}"

# =============================================================================
# Color Output Functions
# =============================================================================

function Write-Info { param($Message) Write-Host "ℹ " -ForegroundColor Blue -NoNewline; Write-Host $Message }
function Write-Success { param($Message) Write-Host "✓ " -ForegroundColor Green -NoNewline; Write-Host $Message }
function Write-Warning { param($Message) Write-Host "! " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
function Write-Error { param($Message) Write-Host "✗ " -ForegroundColor Red -NoNewline; Write-Host $Message }
function Write-Fatal { param($Message) Write-Error $Message; exit 1 }

# =============================================================================
# Argument Parsing
# =============================================================================

param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Source = "",

    [Parameter(Mandatory = $false)]
    [string]$Name = "",

    [Parameter(Mandatory = $false)]
    [switch]$Update,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

# If no source provided and args exist, parse them
if ([string]::IsNullOrEmpty($Source) -and $args.Count -gt 0) {
    $Source = $args[0]
    for ($i = 1; $i -lt $args.Count; $i++) {
        switch ($args[$i]) {
            { $_ -in "--name", "-n" } { $Name = $args[++$i]; break }
            { $_ -in "--update", "-u" } { $Update = $true; break }
            { $_ -in "--force", "-f" } { $Force = $true; break }
            { $_ -in "--help", "-h" } {
                Write-Host @"

Claude Code Marketplace Installer

Usage:
  .\install.ps1 <source> [--name <name>] [--update] [--force]

Examples:
  .\install.ps1 suriyel/longtaskforagent
  .\install.ps1 https://gitlab.com/company/plugins.git --name company-plugins
  .\install.ps1 .\local-marketplace --name test-market

Options:
  --name, -n     Marketplace name (defaults to manifest name)
  --update, -u   Update existing marketplace
  --force, -f    Remove and reinstall if marketplace exists
  --help, -h     Show this help message

"@
                exit 0
            }
        }
    }
}

if ([string]::IsNullOrEmpty($Source)) {
    Write-Info "No source specified, using default: $DefaultSource"
    $Source = $DefaultSource
}

# =============================================================================
# Helper Functions
# =============================================================================

function Test-Command {
    param($Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

function Parse-Source {
    param($Src)

    # Local path: .\path, ..\path, C:\path, ~\path
    if ($Src -match '^(\.\\|\.\.\\|~\\|[A-Za-z]:\\|/)') {
        $absPath = $Src
        if ($Src -match '^~\\') {
            $absPath = Join-Path $env:USERPROFILE ($Src.Substring(2))
        } elseif ($Src -match '^(\.\\|\.\.\\)') {
            $absPath = (Resolve-Path $Src -ErrorAction SilentlyContinue).Path
            if (-not $absPath) {
                $absPath = Join-Path $PWD $Src
            }
        }
        return @{
            Type = "local"
            Value = $absPath
            Url = $Src
        }
    }

    # GitHub shorthand: owner/repo
    if ($Src -match '^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$') {
        $owner = $Matches[1]
        $repo = $Matches[2] -replace '\.git$', ''
        return @{
            Type = "github"
            Value = "$owner/$repo"
            Url = "https://github.com/$owner/$repo.git"
        }
    }

    # GitHub URL: https://github.com/owner/repo[.git]
    if ($Src -match '^https?://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+?)(\.git)?/?$') {
        $owner = $Matches[1]
        $repo = $Matches[2]
        return @{
            Type = "github"
            Value = "$owner/$repo"
            Url = "https://github.com/$owner/$repo.git"
        }
    }

    # Git URL (http, https, ssh, git@)
    if ($Src -match '^(https?|git|ssh)://' -or $Src -match '^git@') {
        return @{
            Type = "url"
            Value = $Src
            Url = $Src
        }
    }

    # Try as local path (relative without .\)
    if (Test-Path $Src -PathType Container) {
        $absPath = (Resolve-Path $Src).Path
        return @{
            Type = "local"
            Value = $absPath
            Url = $Src
        }
    }

    Write-Fatal "Cannot determine source type: $Src`n`nSupported formats:`n  - GitHub shorthand: owner/repo`n  - GitHub URL: https://github.com/owner/repo[.git]`n  - Git URL: https://..., git@..., ssh://...`n  - Local path: .\path, C:\path, ~\path"
}

function Get-JsonField {
    param($File, $Field)
    if (-not (Test-Path $File)) { return $null }
    $content = Get-Content $File -Raw
    if ($content -match "\"$Field\"`\s*:\s*`"([^`"]*)`"") {
        return $Matches[1]
    }
    return $null
}

function Update-KnownMarketplaces {
    param($Name, $SourceType, $SourceValue, $InstallLocation)

    # Ensure directory exists
    if (-not (Test-Path $ClaudePluginsDir)) {
        New-Item -ItemType Directory -Force -Path $ClaudePluginsDir | Out-Null
    }

    # Initialize file if not exists
    if (-not (Test-Path $KnownMarketplacesFile)) {
        "{}" | Out-File -FilePath $KnownMarketplacesFile -Encoding utf8
    }

    # Read existing data
    $json = Get-Content $KnownMarketplacesFile -Raw | ConvertFrom-Json

    # Build source object
    $sourceObj = switch ($SourceType) {
        "github" { @{ source = "github"; repo = $SourceValue } }
        "url" { @{ source = "url"; url = $SourceValue } }
        "local" { @{ source = "local"; path = $SourceValue } }
    }

    # Add or update entry
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.000Z")

    $json | Add-Member -MemberType NoteProperty -Name $Name -Value @{
        source = $sourceObj
        installLocation = $InstallLocation
        lastUpdated = $timestamp
    } -Force

    # Write back
    $json | ConvertTo-Json -Depth 10 | Out-File -FilePath $KnownMarketplacesFile -Encoding utf8
}

function Get-PluginList {
    param($ManifestPath)

    if (-not (Test-Path $ManifestPath)) { return @() }

    $manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
    return $manifest.plugins
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

Write-Info "Pre-flight checks..."

# Check git
if (-not (Test-Command "git")) {
    Write-Fatal "Git is not installed.`n`nInstall git from: https://git-scm.com/download/win`nOr use: winget install Git.Git"
}

# =============================================================================
# Parse Source
# =============================================================================

Write-Info "Parsing source: $Source"

$sourceInfo = Parse-Source $Source

Write-Info "Source type: $($sourceInfo.Type)"
switch ($sourceInfo.Type) {
    "github" { Write-Info "  Repository: $($sourceInfo.Value)" }
    "url" { Write-Info "  URL: $($sourceInfo.Value)" }
    "local" { Write-Info "  Path: $($sourceInfo.Value)" }
}

# =============================================================================
# Clone or Copy Marketplace
# =============================================================================

$tempDir = $null
$sourceDir = $null

try {
    if ($sourceInfo.Type -eq "local") {
        $localPath = $sourceInfo.Value

        if (-not (Test-Path $localPath)) {
            Write-Fatal "Local path does not exist: $localPath"
        }

        $manifestPath = Join-Path $localPath $MarketplaceManifest
        if (-not (Test-Path $manifestPath)) {
            Write-Fatal "Marketplace manifest not found: $manifestPath`n`nA valid marketplace must contain .claude-plugin/marketplace.json`nSee: https://code.claude.com/docs/en/plugin-marketplaces"
        }

        $marketplaceName = Get-JsonField $manifestPath "name"
        if ([string]::IsNullOrEmpty($marketplaceName)) {
            Write-Fatal "Missing required field 'name' in marketplace.json`nFile: $manifestPath"
        }

        if (-not [string]::IsNullOrEmpty($Name)) {
            $marketplaceName = $Name
        }

        $sourceDir = $localPath

    } else {
        # Git source - clone to temp
        $tempDir = Join-Path $env:TEMP "claude-marketplace-$(Get-Random)"
        Write-Info "Cloning: $($sourceInfo.Url)"

        $gitOutput = git clone --depth 1 $sourceInfo.Url $tempDir 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Fatal "Failed to clone repository: $($sourceInfo.Url)`n`nGit output:`n$gitOutput`n`nTroubleshooting:`n  - Check your network connection`n  - Verify the repository URL is correct`n  - For private repos, ensure git credentials are configured:`n    GitHub:    gh auth login`n    GitLab:    Configure SSH keys or GITLAB_TOKEN`n    Self-hosted: Configure SSH keys or credential helper"
        }

        $manifestPath = Join-Path $tempDir $MarketplaceManifest
        if (-not (Test-Path $manifestPath)) {
            Write-Fatal "Marketplace manifest not found: $manifestPath`n`nA valid marketplace must contain .claude-plugin/marketplace.json`nSee: https://code.claude.com/docs/en/plugin-marketplaces"
        }

        $marketplaceName = Get-JsonField $manifestPath "name"
        if ([string]::IsNullOrEmpty($marketplaceName)) {
            Write-Fatal "Missing required field 'name' in marketplace.json`nFile: $manifestPath"
        }

        if (-not [string]::IsNullOrEmpty($Name)) {
            $marketplaceName = $Name
        }

        $sourceDir = $tempDir
    }

    # Sanitize name for filesystem
    $safeName = $marketplaceName -replace '[<>:"/\\|?*]', '_'
    $targetDir = Join-Path $MarketplacesDir $safeName

    # =========================================================================
    # Handle Existing Marketplace
    # =========================================================================

    if (Test-Path $targetDir) {
        if ($Force) {
            Write-Warning "Removing existing marketplace: $targetDir"
            Remove-Item $targetDir -Recurse -Force
        } elseif ($Update) {
            Write-Info "Updating existing marketplace: $targetDir"
            Remove-Item $targetDir -Recurse -Force
        } else {
            Write-Fatal "Marketplace already exists: $marketplaceName`n`nLocation: $targetDir`n`nUse --update to update or --force to reinstall."
        }
    }

    # =========================================================================
    # Install Marketplace
    # =========================================================================

    if (-not (Test-Path $MarketplacesDir)) {
        New-Item -ItemType Directory -Force -Path $MarketplacesDir | Out-Null
    }

    if ($sourceInfo.Type -eq "local") {
        Write-Info "Copying from: $sourceDir"
        Write-Info "          to: $targetDir"
        Copy-Item $sourceDir $targetDir -Recurse
    } else {
        Write-Info "Installing to: $targetDir"
        Move-Item $sourceDir $targetDir
        $tempDir = $null  # Prevent cleanup
    }

    # =========================================================================
    # Register Marketplace
    # =========================================================================

    Write-Info "Registering marketplace: $marketplaceName"
    Update-KnownMarketplaces $marketplaceName $sourceInfo.Type $sourceInfo.Value $targetDir

    # =========================================================================
    # Success Output
    # =========================================================================

    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "✓ Marketplace installed successfully!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Name: $marketplaceName"
    Write-Host "  Path: $targetDir"
    Write-Host ""

    # List plugins
    $finalManifest = Join-Path $targetDir $MarketplaceManifest
    $plugins = Get-PluginList $finalManifest

    if ($plugins -and $plugins.Count -gt 0) {
        Write-Host "Available plugins ($($plugins.Count)):"
        foreach ($plugin in $plugins) {
            $pluginName = $plugin.name
            $pluginVersion = if ($plugin.version) { $plugin.version } else { "unknown" }
            $pluginDesc = $plugin.description
            Write-Host "  - $pluginName (v$pluginVersion)"
            if ($pluginDesc) {
                Write-Host "    $pluginDesc"
            }
        }
        Write-Host ""
    }

    Write-Host "To install plugins, use Claude Code:" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host "  /plugin install <plugin-name>@$marketplaceName"
    Write-Host ""

} finally {
    # Cleanup temp directory
    if ($tempDir -and (Test-Path $tempDir)) {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
