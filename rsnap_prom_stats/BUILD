load("@subpar//:subpar.bzl", "par_binary")
load("@pip_deps//:requirements.bzl", "requirement")

par_binary(
  name = "rsnap_prom_stats",
  main = "__init__.py",
  srcs = ["__init__.py"],
  deps = [
      requirement("prometheus_client"),
  ],
)
