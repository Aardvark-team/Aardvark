{ pkgs }: {
  deps = [
    pkgs.python311
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
  };
}