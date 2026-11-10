#!/usr/bin/env python3
"""يولّد فهرساً بصيغة PEP 503 من مجلد wheels.

الاستخدام:
    make_index.py --wheels dist --out site/simple --base-url https://github.com/USER/REPO/releases/download/TAG

الناتج:  <out>/index.html  +  <out>/<package>/index.html  (روابط مطلقة نحو ملفات الـ wheels مع #sha256=).
تبقى ملفات الـ wheel نفسها في GitHub Releases (حدّ الملف الواحد 2GB)، وتستضيف GitHub Pages الفهرس فقط.
"""
import argparse
import hashlib
import html
import os
import re
import sys
from collections import defaultdict


def canon(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wheels", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-url", required=True)
    a = ap.parse_args()

    groups = defaultdict(list)
    for fn in sorted(os.listdir(a.wheels)):
        if fn.endswith(".whl"):
            groups[canon(fn.split("-")[0])].append(fn)
    if not groups:
        sys.exit("لا توجد ملفات .whl في " + a.wheels)

    base = a.base_url.rstrip("/")
    os.makedirs(a.out, exist_ok=True)
    root = ["<!DOCTYPE html><html><body>"]
    for pkg, files in sorted(groups.items()):
        root.append('<a href="%s/">%s</a><br>' % (pkg, html.escape(pkg)))
        d = os.path.join(a.out, pkg)
        os.makedirs(d, exist_ok=True)
        rows = ["<!DOCTYPE html><html><body>"]
        for fn in files:
            with open(os.path.join(a.wheels, fn), "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            rows.append('<a href="%s/%s#sha256=%s">%s</a><br>' % (base, fn, sha, html.escape(fn)))
        rows.append("</body></html>")
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write("\n".join(rows))
    root.append("</body></html>")
    with open(os.path.join(a.out, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(root))
    print("فهرس: %d حزمة، %d ملف" % (len(groups), sum(len(v) for v in groups.values())))


if __name__ == "__main__":
    main()
