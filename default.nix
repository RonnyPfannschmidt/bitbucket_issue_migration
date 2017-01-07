let
  pkgs = import <nixpkgs> {};
in
  with pkgs.python36Packages;
  buildPythonPackage {
    name = "migrate";
    buildInputs = [
        pytest_30
        requests2
        attrs
        parsedatetime
        setuptools_scm
        #d2tod1
        click
        #wait_for
        ] ;
  }