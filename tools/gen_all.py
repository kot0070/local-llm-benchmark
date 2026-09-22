"""Run every gen/gen_home_*.py main(). Supports --missing-only."""
from __future__ import annotations

import argparse
import glob
import importlib.util
import os
import sys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run all fixture generators")
    p.add_argument("--missing-only", action="store_true",
                   help="only run generators whose fixtures are missing")
    p.add_argument("--gen-dir", default=None)
    p.add_argument("--fixtures-root", default=None)
    a = p.parse_args(argv)
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gen_dir = a.gen_dir or os.path.join(root, "gen")
    fx_root = a.fixtures_root or os.path.join(root, "fixtures")
    paths = sorted(glob.glob(os.path.join(gen_dir, "gen_home_*.py")))
    if not paths:
        print("gen_all: no generators found, nothing to do")
        return 0
    ran, skipped = 0, 0
    for path in paths:
        base = os.path.splitext(os.path.basename(path))[0]  # gen_home_20
        home = base.replace("gen_home_", "HOME-")
        fx_dir = os.path.join(fx_root, home)
        manifest = os.path.join(fx_dir, "manifest.json")
        cases = os.path.join(fx_dir, "cases.jsonl")
        if a.missing_only and os.path.exists(manifest) and os.path.exists(cases):
            print(f"gen_all: skip {base} (fixtures present)")
            skipped += 1
            continue
        spec = importlib.util.spec_from_file_location(base, path)
        if spec is None or spec.loader is None:
            print(f"gen_all: cannot load {path}", file=sys.stderr)
            return 1
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "main"):
            print(f"gen_all: {base} has no main()", file=sys.stderr)
            return 1
        print(f"gen_all: running {base}.main()")
        mod.main()
        ran += 1
    print(f"gen_all: ran={ran} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
