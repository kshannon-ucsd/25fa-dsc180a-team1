#!/usr/bin/env python3

import subprocess
import shutil
from pathlib import Path
import sys


def main():
    here = Path(__file__).resolve()
    r_script = here.with_name("fig_3a_3b.R")

    if not r_script.exists():
        print(f"ERROR: R script not found at {r_script}", file=sys.stderr)
        sys.exit(1)

    rscript_bin = shutil.which("Rscript")
    if rscript_bin is None:
        print("ERROR: 'Rscript' not found on PATH.", file=sys.stderr)
        sys.exit(1)

    subprocess.run([rscript_bin, str(r_script)], check=True)


if __name__ == "__main__":
    main()