#!/usr/bin/env python

# Copyright 2026 Makora Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

import importlib.util
from pathlib import Path

root_dir = Path(__file__).parent

package_name = "makora"
description = "CLI interface to use MakoraGenerate as a standalone tool or inside your favourite coding agent."
author = "Makora"
author_email = "support@mako-dev.com"
url = "https://github.com/makora-ai/makora"
download_url = "https://github.com/makora-ai/makora/releases"
data_files = {}

version_file = Path(__file__).parent.joinpath(package_name, "version.py")
spec = importlib.util.spec_from_file_location("{}.version".format(package_name), version_file)
package_version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package_version)

long_desc = None
long_desc_type = None
readme_md = Path(__file__).parent.joinpath("README.md")
if readme_md.exists():
    data_files.setdefault("", []).append(readme_md.name)
    with readme_md.open("r") as f:
        long_desc = f.read()
        long_desc_type = "text/markdown"

license = Path(__file__).parent.joinpath("LICENSE")
if license.exists():
    data_files.setdefault("", []).append(license.name)

data_files[package_name] = ["py.typed"]
data_dir = root_dir / package_name / "data"
if data_dir.exists():
    data_files[package_name].extend(
        str(path.relative_to(root_dir / package_name)) for path in data_dir.rglob("*") if path.is_file()
    )


class dist_info_mixin:
    def run(self):
        _dist_file = version_file.parent.joinpath("_dist_info.py")
        _dist_file.write_text(
            "\n".join(
                map(
                    lambda attr_name: attr_name + " = " + repr(getattr(package_version, attr_name)),
                    package_version.__all__,
                )
            )
            + "\n"
        )
        try:
            ret = super().run()
        finally:
            _dist_file.unlink()
        return ret


class custom_sdist(dist_info_mixin, sdist):
    pass


class custom_wheel(dist_info_mixin, build_py):
    pass


setup(
    name=package_name,
    version=package_version.version,
    description=description,
    author=author,
    author_email=author_email,
    url=url,
    download_url=download_url,
    long_description=long_desc or "",
    long_description_content_type=long_desc_type or "",
    python_requires=">=3.10.0",
    install_requires=[
        "pydantic",
        "textual",
        "rich",
        "aiohttp",
        "typer",
        "PyYAML",
        "tabulate",
        "pydantic[email]",
    ],
    extras_require={
        "dev": [
            "GitPython",
            "ruff==0.14.14",
            "datamodel-code-generator",
            "mypy",
            "types-PyYAML",
            "types-tabulate",
            "types-Pygments",
            "types-docutils",
        ],
    },
    packages=find_packages(where=".", include=[package_name, package_name + ".*"]),
    package_dir={"": "."},
    package_data=data_files,
    cmdclass={"sdist": custom_sdist, "build_py": custom_wheel},
    entry_points={
        "console_scripts": [
            "makora = makora.cli:main",
        ]
    },
)
