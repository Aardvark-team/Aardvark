{ pkgs }: {
  deps = [
    pkgs.pick
    pkgs.llvmPackages_13.bintools-unwrapped
    pkgs.python39Packages.black
    pkgs.python311
    pkgs.replitPackages.stderred
    pkgs.nodejs-18_x
  ];
  env = {
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      # Needed for pandas / numpy
      pkgs.zlib
      # Needed for pygame
      pkgs.glib
      # Needed for matplotlib
      pkgs.xorg.libX11
    ];
    PYTHONBIN = "${pkgs.python311}/bin/python3.11";
    LANG = "en_US.UTF-8";
    STDERREDBIN = "${pkgs.replitPackages.stderred}/bin/stderred";
  };
}
