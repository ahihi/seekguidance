# based on https://github.com/nix-community/dream2nix/blob/main/examples/packages/languages/python-local-development/default.nix
{ config, dream2nix, lib, ... }:
let
  pyproject = lib.importTOML (config.mkDerivation.src + /pyproject.toml);
in {
  imports = [
    dream2nix.modules.dream2nix.pip
  ];

  inherit (pyproject.project) name version;

  deps = { nixpkgs, ... }: {
    python = nixpkgs.python3;
  };

  mkDerivation = {
    src = lib.cleanSourceWith {
      src = lib.cleanSource ./.;
      filter = name: type:
        !(builtins.any (x: x) [
          (lib.hasSuffix ".nix" name)
          (lib.hasPrefix "." (builtins.baseNameOf name))
          (lib.hasSuffix "flake.lock" name)
        ]);
    };
  };

  buildPythonPackage = {
    pyproject = true;
    pythonImportsCheck = [
      config.name
    ];
  };

  paths.lockFile = "lock.${config.deps.stdenv.system}.json";
  pip = {
    requirementsList =
      pyproject.build-system.requires or []
      ++ pyproject.project.dependencies;
    flattenDependencies = true;
  };
}
