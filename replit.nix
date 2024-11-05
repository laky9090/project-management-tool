{pkgs}: {
  deps = [
    pkgs.file
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.glibcLocales
    pkgs.postgresql
  ];
}
