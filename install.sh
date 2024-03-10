#!/usr/bin/env bash

# Simplified preconditions check
[[ "${OS:-}" = "Windows_NT" ]] && echo 'Please install Aardvark using WSL' && exit 1

# Color setup
Color_Off='\033[0m'; Red='\033[0;31m'; Green='\033[0;32m'; Dim='\033[0;2m'; Bold_White='\033[1m'; Bold_Green='\033[1;32m'
[[ -t 1 ]] || { Color_Off=''; Red=''; Green=''; Dim=''; Bold_White=''; Bold_Green=''; }

# Utility functions
print_error() { printf "${Red}error${Color_Off}: $@\n" >&2; exit 1; }
print_info() { printf "${Dim}$@ ${Color_Off}\n"; }
print_success() { printf "${Green}$@ ${Color_Off}\n"; }

# Check for required commands
command -v unzip >/dev/null || print_error 'unzip is required to install Aardvark'

# Variables for installation
install_dir="$HOME/.adk"
bin_dir="$install_dir/bin"
zip="$install_dir/pack.zip"
download_url="https://github.com/Aardvark-team/Aardvark/releases/latest/download/adk.zip"

# Download and extract Aardvark
mkdir -p "$bin_dir" || print_error "Failed to create install directory \"$install_dir\""
curl --fail --location --progress-bar --output "$zip" "$download_url" || print_error "Failed to download Aardvark"
unzip -oqd "$install_dir" "$zip" || print_error 'Failed to extract Aardvark'
chmod +x "$bin_dir/adk" || print_error 'Failed to set permissions on adk executable'

print_success "Download Complete!"

# Update profile to include Aardvark in PATH if not already included
update_profile() {
    local path_line='export PATH="$PATH:$HOME/.adk/bin"'
    local install_dir_line='export AARDVARK_INSTALL="$HOME/.adk"'
    
    # Determine which profile file to update
    local profile_files=(.bash_profile .profile .bashrc .zshrc .config/fish/config.fish)
    local profile_path=""
    for profile in "${profile_files[@]}"; do
        if [[ -f "$HOME/$profile" ]]; then
            profile_path="$HOME/$profile"
            break
        fi
    done
    if [[ -z "$profile_path" ]]; then
        profile_path="$HOME/.bash_profile" # Default to .bash_profile if no other profile files exist
    fi

    # Check and update the profile file if needed
    if ! grep -qxF "$path_line" "$profile_path"; then
        echo "$path_line" >> "$profile_path"
        print_info "Updated $profile_path with Aardvark PATH."
    fi
    if ! grep -qxF "$install_dir_line" "$profile_path"; then
        echo "$install_dir_line" >> "$profile_path"
        print_info "Updated $profile_path with Aardvark install directory."
    fi
}

update_profile
print_success "Installation Complete!"
print_info "To get started, run:"
printf "${Bold_White}  adk help${Color_Off}\n"
