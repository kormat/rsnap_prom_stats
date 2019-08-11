load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",
    commit = "4b84ad270387a7c439ebdccfd530e2339601ef27",
    shallow_since = "1564776078 -0400",
)

load("@rules_python//python:repositories.bzl", "py_repositories")
py_repositories()

load("@rules_python//python:pip.bzl", "pip_repositories", "pip_import")
pip_repositories()

git_repository(
    name = "subpar",
    remote = "https://github.com/google/subpar",
    commit = "35bb9f0092f71ea56b742a520602da9b3638a24f",
    shallow_since = "1557863961 -0400",
)

pip_import(
   name = "pip_deps",
   requirements = "//:requirements.txt",
)

load("@pip_deps//:requirements.bzl", "pip_install")
pip_install()
