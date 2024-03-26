#!/usr/bin/env bash
# set -euo pipefail

if [[ ${OS:-} = Windows_NT ]]; then
    echo 'error: Please install Aardvark using Windows Subsystem for Linux.'
    echo 'Attempting anyways...'
    powershell.exe -ExecutionPolicy Bypass -Command "& { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Aardvark-team/Aardvark/main/install.ps1' -OutFile 'install.ps1'; .\install.ps1; Remove-Item -Path 'install.ps1' }"
    exit 1
fi
# Reset
Color_Off=''

# Regular Colors
Red=''
Green=''
Dim='' # White

# Bold
Bold_White=''
Bold_Green=''

if [[ -t 1 ]]; then
    # Reset
    Color_Off='\033[0m' # Text Reset

    # Regular Colors
    Red='\033[0;31m'   # Red
    Green='\033[0;32m' # Green
    Dim='\033[0;2m'    # White

    # Bold
    Bold_Green='\033[1;32m' # Bold Green
    Bold_White='\033[1m'    # Bold White
fi

error() {
    printf "${Red}error${Color_Off}: $@\n"
    exit 1
}

info() {
    printf "${Dim}$@ ${Color_Off}\n"
}

info_bold() {
    printf "${Bold_White}$@ ${Color_Off}\n"
}

success() {
    printf "${Green}$@ ${Color_Off}\n"
}


command -v unzip >/dev/null ||
    error 'unzip is required to install Aardvark'



# https://github.com/Aardvark-team/Aardvark/archive/refs/tags/v1.0.0-test.2.zip
version=1.0.0-test.2
GITHUB=${GITHUB-"https://github.com"}

github_repo="$GITHUB/Aardvark-team/Aardvark"

release_url=$github_repo/releases/latest/download/adk.zip
latest_url=$github_repo/archive/main.zip

info_bold "Would you like to install the lastest release or the canary? [release/canary]: "

read -r input
case $input in
    [Rr]elease|[rR]*)
        download_url=$release_url
        ;;
    Canary|[cC]*)
        download_url=$latest_url
        ;;
    *)
        error "Invalid input. Please choose \"release\" or \"canary\"."
        ;;
esac


install_dir=$HOME/.adk
bin_dir=$install_dir/bin
exe=$bin_dir/adk
zip=$install_dir/pack.zip

rm -r "$install_dir" 2>/dev/null

mkdir -p "$install_dir" ||
    error "Failed to create install directory \"$install_dir\""

curl --fail --location --progress-bar --output "$zip" "$download_url" ||
    error "Failed to download Aardvark from \"$download_url\""

unzip -oqd "$install_dir" "$zip" ||
    error 'Failed to extract Aardvark'

mv $install_dir/adk/{.,}* $install_dir/ 2>/dev/null || mv $install_dir/Aardvark-main/{.,}* $install_dir/ 2>/dev/null

rmdir "$install_dir/adk" 2>/dev/null ||
    rmdir "$install_dir/Aardvark-main" || error 'Failed to remove Aardvark'

chmod +x "$exe" ||
    error 'Failed to set permissions on adk executable'

chmod +x $exe"c" ||
    error 'Failed to set permissions on adkc executable'

success "Download Complete!"


# Get the default shell from the SHELL environment variable
default_shell=$(basename "$SHELL")

# The line you want to add to your profile
line_to_add='export PATH="$PATH:$HOME/.adk/bin"\nexport AARDVARK_INSTALL="$HOME/.adk"\n'

# Get the default shell from the SHELL environment variable
default_shell=$(basename "$SHELL")

# Function to check if a command is available
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get the shell version
get_shell_version() {
    case "$1" in
        bash)
            bash --version | head -n 1 | cut -d " " -f 4
            ;;
        zsh)
            zsh --version | cut -d " " -f 2
            ;;
        tcsh)
            tcsh --version | head -n 1 | cut -d " " -f 3
            ;;
        dash)
            dpkg -s dash | grep '^Version:' | cut -d " " -f 2
            ;;
        ksh)
            ksh --version | head -n 1 | cut -d " " -f 3
            ;;
        fish)
            fish --version
            ;;
        *)
            error "Unknown or unsupported shell: $1"
            exit 1
            ;;
    esac
}

# Add a specific line to the configuration file based on shell version
add_line_based_on_version() {
    local shell_version=$1
    local config_file=$2
    local line_to_add=$3

    case "$default_shell" in
        bash|zsh|tcsh|ksh)
            # For Bash, Zsh, Tcsh, Ksh
            printf "$line_to_add" >> "$config_file"
            ;;
        dash)
            # For Dash, only add if the version is at least 0.5.10
            if dpkg --compare-versions "$shell_version" "ge" "0.5.10"; then
                printf "$line_to_add" >> "$config_file"
            fi
            ;;
        fish)
            # For Fish, only add if the version is at least 3.1.0
            if dpkg --compare-versions "$shell_version" "ge" "3.1.0"; then
                printf "$line_to_add" >> "$config_file"
            fi
            ;;
        *)
            error "Unknown or unsupported shell: $default_shell"
            exit 1
            ;;
    esac
}

# Check the default shell and add configuration accordingly
case "$default_shell" in
    bash)
        echo "Default shell is Bash"
        config_file=~/.bash_profile
        ;;
    zsh)
        echo "Default shell is Zsh"
        config_file=~/.zshrc
        ;;
    tcsh)
        echo "Default shell is Tcsh"
        config_file=~/.tcshrc
        ;;
    dash)
        echo "Default shell is Dash"
        config_file=~/.profile
        ;;
    ksh)
        echo "Default shell is Korn Shell (ksh)"
        config_file=~/.kshrc
        ;;
    fish)
        echo "Default shell is Fish"
        config_file=~/.config/fish/config.fish
        ;;
    *)
        error "Unknown or unsupported shell: $default_shell"
        exit 1
        ;;
esac

# Get the shell version
shell_version=$(get_shell_version "$default_shell")




add_to_bash_profile() {
    # List of potential profile files
    profile_files=(.bash_profile .profile .bashrc .inputrc .zshrc .zprofile .zshenv .config/fish/config.fish .config/fish/fish.config .kshrc .cshrc .tcshrc .cshrc)
    if [[ ${XDG_CONFIG_HOME:-} ]]; then
        profile_files+=(
            "$XDG_CONFIG_HOME/.bash_profile"
            "$XDG_CONFIG_HOME/.bashrc"
            "$XDG_CONFIG_HOME/.zprofile"
            "$XDG_CONFIG_HOME/bash_profile"
            "$XDG_CONFIG_HOME/bashrc"
        )
    fi
    # Flag to check if file is found
    file_found=0

    # Loop through the list and append the line to the first file that exists
    for file in "${profile_files[@]}"; do
    profile_path="$HOME/$file"
    if [[ -f "$profile_path" ]]; then
        printf $1 >> "$profile_path"
        info "Added to $profile_path"
        file_found=1
    fi
    done

    # If no file was found, create .bash_profile and append the line
    if [[ $file_found -eq 0 ]]; then
        add_line_based_on_version "$shell_version" "$config_file" "$1"
        profile_path="$HOME/.bash_profile"
        printf $1 >> "$profile_path"
        info "No existing profile file found. Created and added line to $profile_path"
    fi
}

# Check if AARDVARK_INSTALL is set and not empty
if [ -n "$AARDVARK_INSTALL" ]; then
    # Prepare the path we are looking for
    target_path="$AARDVARK_INSTALL/bin"
    
    # Convert PATH into an array of directories
    IFS=':' read -ra path_dirs <<< "$PATH"
    
    # Flag to track if we found the target path
    found=0
    
    # Iterate through directories in PATH
    for dir in "${path_dirs[@]}"; do
        if [ "$dir" == "$target_path" ]; then
            found=1
            break
        fi
    done
    
    # Check if target path was found
    if [ $found -eq 1 ]; then
        info ".adk/bin is already in PATH."
    else
        add_to_bash_profile 'export PATH="$PATH:$HOME/.adk/bin"\n'
    fi
else
    add_to_bash_profile 'export PATH="$PATH:$HOME/.adk/bin"\nexport AARDVARK_INSTALL="$HOME/.adk"\n'
fi



success "Installation Complete!"

echo
info "To get started, run:"
info_bold "  adk help"
