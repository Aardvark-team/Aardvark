#!/usr/bin/env bash
# set -euo pipefail

if [[ ${OS:-} = Windows_NT ]]; then
    echo 'error: Please install Aardvark using Windows Subsystem for Linux'
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
    echo -e "${Red}error${Color_Off}:" "$@" >&2
    exit 1
}

info() {
    echo -e "${Dim}$@ ${Color_Off}"
}

info_bold() {
    echo -e "${Bold_White}$@ ${Color_Off}"
}

success() {
    echo -e "${Green}$@ ${Color_Off}"
}


command -v unzip >/dev/null ||
    error 'unzip is required to install Aardvark'



# https://github.com/Aardvark-team/Aardvark/archive/refs/tags/v1.0.0-test.2.zip
version=1.0.0-test.2
GITHUB=${GITHUB-"https://github.com"}

github_repo="$GITHUB/Aardvark-team/Aardvark"

download_url=$github_repo/releases/latest/download/adk.zip

install_dir=$HOME/.adk
bin_dir=$install_dir/bin
exe=$bin_dir/adk
zip=$install_dir/pack.zip

rm -r "$install_dir" || true

mkdir -p "$install_dir" ||
    error "Failed to create install directory \"$install_dir\""

curl --fail --location --progress-bar --output "$zip" "$download_url" ||
    error "Failed to download Aardvark from \"$download_url\""

unzip -oqd "$install_dir" "$zip" ||
    error 'Failed to extract Aardvark'

mv $install_dir/adk/{.,}* $install_dir/ 2>/dev/null

rmdir "$install_dir/adk" ||
    error 'Failed to remove Aardvark'

chmod +x "$exe" ||
    error 'Failed to set permissions on adk executable'

chmod +x $exe"c" ||
    error 'Failed to set permissions on adkc executable'

success "Download Complete!"




# The line you want to add to your profile
line_to_add='export PATH="$PATH:$HOME/.adk/bin"\nexport AARDVARK_INSTALL="$HOME/.adk"'
add_to_bash_profile() {
    # List of potential profile files
    profile_files=(.bash_profile .profile .bashrc)
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
        echo -e $1 >> "$profile_path"
        info "Added to $profile_path"
        file_found=1
        break
    fi
    done

    # If no file was found, create .bash_profile and append the line
    if [[ $file_found -eq 0 ]]; then
    profile_path="$HOME/.bash_profile"
    echo -e $1 >> "$profile_path"
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
        add_to_bash_profile 'export PATH="$PATH:$HOME/.adk/bin"'
    fi
else
    add_to_bash_profile 'export PATH="$PATH:$HOME/.adk/bin"\nexport AARDVARK_INSTALL="$HOME/.adk'
fi



success "Installation Complete!"

echo
info "To get started, run:"
info_bold "  adk help"
