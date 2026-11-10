
#!/usr/bin/env python3
"""ينزّل ما ينقص أداة build-wheel من متطلبات (host requirements) من مستودع Chaquopy.

build-wheel يتوقف برسالة مثل:
    Couldn't find compatible wheel for chaquopy-libgfortran 4.9. Try downloading it from
    https://chaquo.com/pypi-13.1/chaquopy-libgfortran/ into .../dist/chaquopy-libgfortran.
هذا السكربت يقرأ تلك الرسالة من السجل، وينزّل الـ wheels المناسبة (نفس معمارية الهدف وبايثون)
إلى dist/<اسم الحزمة>/ ثم يُعاد تشغيل build-wheel.

الاستخدام:  fetch_dep.py --log build.log --abi arm64-v8a --python 3.11 --dist dist
الخروج:     0 = نُزّل شيء جديد (أعد المحاولة) ، 3 = لا رسالة نقص في السجل ، 4 = لا wheel مناسب في المستودع.
"""
import argparse
import html.parser
import os
import re
import sys
import urllib.parse
import urllib.request

INDEX = "https://chaquo.com/pypi-13.1/"
MSG = re.compile(r"Couldn't find compatible wheel for (\S+) (\S+?)\.?\s+Try downloading")


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


def canon(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_wheel(fn):
    """name-version[-build]-py-abi-platform.whl → (version, py, abi, platform)."""
    parts = fn[:-4].split("-")
    if len(parts) < 5:
        return None
    return parts[1], parts[-3], parts[-2], parts[-1]


def pick(filenames, abi, pyver, want_version=None):
    """يختار الـ wheels المناسبة: بايثون (cpXY أو py3) + منصة android_<API>_<abi>."""
    cp = "cp" + pyver.replace(".", "")
    abi_tag = abi.replace("-", "_")
    ok = []
    for fn in filenames:
        info = parse_wheel(fn)
        if not info:
            continue
        ver, py, abi_, plat = info
        m = re.fullmatch(r"android_(\d+)_(.+)", plat)
        if not m or m.group(2) != abi_tag:
            continue
        if py == cp and abi_ in (cp, "abi3", "none") or (py in ("py3", "py2.py3") and abi_ == "none"):
            ok.append((fn, ver))
        elif py == cp and abi_ == cp:
            ok.append((fn, ver))
    if want_version:
        exact = [x for x in ok if x[1] == want_version or x[1].startswith(want_version + ".")]
        if exact:
            ok = exact
    return [fn for fn, _ in ok]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--abi", required=True)
    ap.add_argument("--python", default="3.11")
    ap.add_argument("--dist", default="dist")
    a = ap.parse_args()

    with open(a.log, encoding="utf-8", errors="replace") as f:
        m = None
        for m in MSG.finditer(f.read()):
            pass  # آخر رسالة نقص
    if not m:
        print("لا توجد رسالة «Couldn't find compatible wheel» في السجل؛ الفشل لسبب آخر.")
        return 3
    name, version = m.group(1), m.group(2)
    print("ينقص: %s %s" % (name, version))

    url = urllib.parse.urljoin(INDEX, canon(name) + "/")
    try:
        page = urllib.request.urlopen(url, timeout=60).read().decode("utf-8", "replace")
    except Exception as e:
        print("تعذّر فتح %s: %s" % (url, e))
        return 4
    p = Links()
    p.feed(page)
    files = sorted({urllib.parse.unquote(h.rsplit("/", 1)[-1]) for h in p.hrefs if h.endswith(".whl")})
    chosen = pick(files, a.abi, a.python, version)
    if not chosen:
        print("لا يوجد في %s أي wheel مناسب لـ cp%s / %s." % (url, a.python.replace(".", ""), a.abi))
        print("المتاح: " + ", ".join(files))
        return 4

    dest = os.path.join(a.dist, name)
    os.makedirs(dest, exist_ok=True)
    new = False
    for fn in chosen:
        path = os.path.join(dest, fn)
        if os.path.exists(path):
            continue
        print("تنزيل " + fn)
        urllib.request.urlretrieve(urllib.parse.urljoin(url, urllib.parse.quote(fn)), path)
        new = True
    if not new:
        print("الملفات موجودة أصلاً في %s، ولا يزال build-wheel يرفضها — الخطأ ليس في غيابها." % dest)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
