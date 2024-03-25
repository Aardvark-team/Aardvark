# Check if running on Windows
if ($env:OS -ne "Windows_NT") {
  Write-Error "error: Please install Aardvark using the bash script"
  exit 1
}

# Reset
$Color_Off = ""

# Regular Colors
$Red = ""
$Green = ""
$Dim = "" # White

# Bold
$Bold_White = ""
$Bold_Green = ""

# Check if running in a terminal
if ($Host.UI.RawUI.BufferSize.Width -gt 0) {
  # Reset
  $Color_Off = "`e[0m" # Text Reset

  # Regular Colors
  $Red = "`e[0;31m"   # Red
  $Green = "`e[0;32m" # Green
  $Dim = "`e[0;2m"    # White

  # Bold
  $Bold_Green = "`e[1;32m" # Bold Green
  $Bold_White = "`e[1m"    # Bold White
}

function error {
  param([string]$message)
  Write-Host "${Red}error${Color_Off}: $message"
  exit 1
}

function info {
  param([string]$message)
  Write-Host "$Dim$message $Color_Off"
}

function info_bold {
  param([string]$message)
  Write-Host "$Bold_White$message $Color_Off"
}

function success {
  param([string]$message)
  Write-Host "$Green$message $Color_Off"
}


### Taken from bun install.ps1
# These three environment functions are roughly copied from https://github.com/prefix-dev/pixi/pull/692
# They are used instead of `SetEnvironmentVariable` because of unwanted variable expansions.
function Publish-Env {
  if (-not ("Win32.NativeMethods" -as [Type])) {
    Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition @"
[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(
    IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
    uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
  }
  $HWND_BROADCAST = [IntPtr] 0xffff
  $WM_SETTINGCHANGE = 0x1a
  $result = [UIntPtr]::Zero
  [Win32.NativeMethods]::SendMessageTimeout($HWND_BROADCAST,
    $WM_SETTINGCHANGE,
    [UIntPtr]::Zero,
    "Environment",
    2,
    5000,
    [ref] $result
  ) | Out-Null
}
  
function Write-Env {
  param([String]$Key, [String]$Value)

  $RegisterKey = Get-Item -Path 'HKCU:'

  $EnvRegisterKey = $RegisterKey.OpenSubKey('Environment', $true)
  if ($null -eq $Value) {
    $EnvRegisterKey.DeleteValue($Key)
  }
  else {
    $RegistryValueKind = if ($Value.Contains('%')) {
      [Microsoft.Win32.RegistryValueKind]::ExpandString
    }
    elseif ($EnvRegisterKey.GetValue($Key)) {
      $EnvRegisterKey.GetValueKind($Key)
    }
    else {
      [Microsoft.Win32.RegistryValueKind]::String
    }
    $EnvRegisterKey.SetValue($Key, $Value, $RegistryValueKind)
  }

  Publish-Env
}
  
function Get-Env {
  param([String] $Key)

  $RegisterKey = Get-Item -Path 'HKCU:'
  $EnvRegisterKey = $RegisterKey.OpenSubKey('Environment')
  $EnvRegisterKey.GetValue($Key, $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
}

# Define URLs and directories
$version = "1.0.0-test.2"
$GITHUB = "https://github.com"
$github_repo = "$GITHUB/Aardvark-team/Aardvark"
$download_url = "$github_repo/releases/latest/download/adk.zip"
$install_dir = "$Home\.adk"
$bin_dir = "$install_dir\bin"
$exe = "$bin_dir\adk"
$zip = "$install_dir\pack.zip"

# Clean previous installation
Remove-Item -Path $install_dir -Recurse -ErrorAction SilentlyContinue

# Create install directory
New-Item -Path $install_dir -ItemType Directory -ErrorAction Stop | Out-Null

# Download Aardvark
Invoke-WebRequest -Uri $download_url -OutFile $zip -ErrorAction Stop

# Extract Aardvark
Expand-Archive -Path $zip -DestinationPath $install_dir -Force

# Move files from subdirectory
Move-Item -Path "$install_dir\adk\*" -Destination $install_dir -Force

# Remove empty subdirectory
Remove-Item -Path "$install_dir\adk" -Force

# Set permissions
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
Set-ItemProperty -Path $exe -Name IsReadOnly -Value $false -ErrorAction Stop
Set-ItemProperty -Path ($exe + "c") -Name IsReadOnly -Value $false -ErrorAction Stop

success "Download Complete!"

Write-Env -Key "AARDVARK_INSTALL" -Value $install_dir

$adkbin = "%AARDVARK_INSTALL%\bin"
$Path = (Get-Env -Key "Path") -split ";"

if ($Path -notcontains $adkbin) {
  $Path += $adkbin
  $env:Path = ($Path -join ";")
  Write-Env -Key "Path" -Value ($Path -join ";")
  success "Added to PATH!"
}

# if (([Environment]::GetEnvironmentVariable("Path").Contains($adkbin)) -eq "False") {
#     [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$adkbin", "User")
#     success "Added to PATH!"
# }

success "Installation Complete!"

Write-Host ""
info "To get started, run:"
info_bold "  adk help"
