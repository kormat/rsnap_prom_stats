git_repository(
    name = "io_bazel_rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",
    commit = "f3a6a8d00a51a1f0e6d61bc7065c19fea2b3dd7a",
)

git_repository(
    name = "subpar",
    remote = "https://github.com/google/subpar",
    tag = "1.3.0",
)

load("@io_bazel_rules_python//python:pip.bzl", "pip_repositories", "pip_import")

pip_repositories()

pip_import(
   name = "pip_deps",
   requirements = "//:requirements.txt",
)

load("@pip_deps//:requirements.bzl", "pip_install")
pip_install()
