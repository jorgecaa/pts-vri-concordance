#!/usr/bin/env python3
"""Compile .tex to PDFs — recompiles stale PDFs (where .tex is newer)."""

import subprocess
import sys
from pathlib import Path

tex_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("rotb_commentary")
force = "--force" in sys.argv
files = sorted(tex_dir.glob("book_*.tex"))
stale = []

for f in files:
    pdf = tex_dir / (f.stem + ".pdf")
    if force or not pdf.exists() or f.stat().st_mtime > pdf.stat().st_mtime:
        stale.append(f)

if not stale:
    print("All PDFs are up to date.")
    sys.exit(0)

print(f"Compiling {len(stale)} of {len(files)} PDFs (stale or missing)...")
ok = 0
for i, f in enumerate(stale):
    name = f.stem
    sys.stdout.write(f"[{i + 1:2d}/{len(stale)}] {name} ... ")
    sys.stdout.flush()
    for _ in range(2):
        subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", f.name],
            cwd=tex_dir,
            capture_output=True,
            text=True,
            timeout=600,
        )
    pdf = tex_dir / (name + ".pdf")
    if pdf.exists():
        print(f"OK {pdf.stat().st_size // 1024} KB")
        ok += 1
    else:
        print("FAILED")
print(f"\n{ok}/{len(stale)} PDFs compiled")
