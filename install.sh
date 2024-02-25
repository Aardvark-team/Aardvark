
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

download_url=$github_repo/archive/refs/tags/v$version.zip

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

mv $install_dir/Aardvark-$version/{.,}* $install_dir/ 2>/dev/null

rmdir "$install_dir/Aardvark-$version" ||
    error 'Failed to remove Aardvark'

chmod +x "$exe" ||
    error 'Failed to set permissions on adk executable'

success "Download Complete!"


# The line you want to add to your profile
line_to_add='export PATH="$PATH:$HOME/.adk/bin"\nexport AARDVARK_INSTALL="$HOME/.adk"'

# List of potential profile files
profile_files=(.bash_profile .profile .bashrc)

# Flag to check if file is found
file_found=0

# Loop through the list and append the line to the first file that exists
for file in "${profile_files[@]}"; do
  profile_path="$HOME/$file"
  if [[ -f "$profile_path" ]]; then
    echo "$line_to_add" >> "$profile_path"
    info "Added to $profile_path"
    file_found=1
    break
  fi
done

# If no file was found, create .bash_profile and append the line
if [[ $file_found -eq 0 ]]; then
  profile_path="$HOME/.bash_profile"
  echo "$line_to_add" >> "$profile_path"
  info "No existing profile file found. Created and added line to $profile_path"
fi

success "Installation Complete!"
