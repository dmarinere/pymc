# BSD 3-Clause License

# Copyright (c) 2008-2011, AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team
# All rights reserved.

# Copyright (c) 2011-2020, Open source contributors.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Check requirements-dev.txt has been generated from conda-envs/environment-dev-py3*.yml

This is intended to be used as a pre-commit hook, see `.pre-commit-config.yaml`.
You can run it manually with `pre-commit run pip-from-conda --all`.
"""
import argparse
import re

import yaml

EXCLUDE = {
    "pip",
    "python",
    "libblas",
    "libblas=*=*mkl",
    "libpython",
    "m2w64-toolchain",
    "mkl-service",
    "numba",
    "python-graphviz",
    "blas",
}
RENAME = {}


def conda_package_to_pip(package):
    """
    Convert a conda package to its pip equivalent.

    In most cases they are the same, those are the exceptions:
    - Packages that should be excluded (in `EXCLUDE`)
    - Packages that should be renamed (in `RENAME`)
    - A package requiring a specific version, in conda is defined with a single
      equal (e.g. ``pandas=1.0``) and in pip with two (e.g. ``pandas==1.0``)
    """
    package = re.sub("(?<=[^<>])=", "==", package).strip()

    for compare in ("<=", ">=", "=="):
        if compare not in package:
            continue
        pkg, version = package.split(compare, maxsplit=1)
        if pkg in EXCLUDE:
            return

        if pkg in RENAME:
            return "".join((RENAME[pkg], compare, version))

        break

    if package in EXCLUDE:
        return

    if package in RENAME:
        return RENAME[package]

    return package


def main(conda_fname, pip_fname):
    """
    Generate the pip dependencies file from the conda file, or compare that
    they are synchronized (``compare=True``).

    Parameters
    ----------
    conda_fname : str
        Path to the conda file with dependencies (e.g. `environment.yml`).
    pip_fname : str
        Path to the pip file with dependencies (e.g. `requirements-dev.txt`).
    compare : bool, default False
        Whether to generate the pip file (``False``) or to compare if the
        pip file has been generated with this script and the last version
        of the conda file (``True``).

    Returns
    -------
    bool
        True if the comparison fails, False otherwise
    """
    with open(conda_fname) as conda_fd:
        deps = yaml.safe_load(conda_fd)["dependencies"]

    pip_deps = []
    for dep in deps:
        if isinstance(dep, str):
            conda_dep = conda_package_to_pip(dep)
            if conda_dep:
                pip_deps.append(conda_dep)
        elif isinstance(dep, dict) and len(dep) == 1 and "pip" in dep:
            pip_deps += dep["pip"]
        else:
            raise ValueError(f"Unexpected dependency {dep}")

    header = (
        f"# This file is auto-generated by scripts/generate_pip_deps_from_conda.py, "
        "do not modify.\n# See that file for comments about the need/usage of each dependency.\n\n"
    )
    pip_content = header + "\n".join(sorted(pip_deps)) + "\n"

    with open(pip_fname, "w") as pip_fd:
        pip_fd.write(pip_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    for file in args.files:
        main(file, "requirements-dev.txt")
