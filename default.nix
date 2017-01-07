let
  pkgs = import <nixpkgs> {};
in
  with pkgs.python36Packages;
  buildPythonPackage {
    name = "migrate";
    src = ./.;
    buildInputs = [
        pkgs.git
        pytest_30
        requests2
        attrs
        parsedatetime
        setuptools_scm
        pathlib2
        #d2tod1
        click
        mock
        #wait_for
        ] ;
  }