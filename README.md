# مستودع wheels لأندرويد (PyIDE)

يبني حزم بايثون المكتوبة بلغة C لأندرويد (cp311) باستخدام أداة `build-wheel` الرسمية من Chaquopy
(`chaquo/chaquopy` → `server/pypi`)، وينشرها كفهرس PEP 503 يقرؤه التطبيق.

## الفكرة
- **GitHub Actions** يبني الـ wheels (arm64-v8a وx86_64) على خوادم GitHub، لأن أداة البناء تعمل على Linux فقط وتحتاج NDK.
- الـ wheels تُرفع إلى **GitHub Releases**، والفهرس (HTML فقط) يُنشر على **GitHub Pages**.
- التطبيق يضيف رابط الفهرس: `pip index add https://USER.github.io/REPO/simple/`.

## الإعداد (مرة واحدة)
1. أنشئ مستودعاً على GitHub وارفع هذا المجلد إليه.
2. Settings → Pages → Source: **GitHub Actions**.
3. عدّل `packages.txt` (ابدأ بحزمة واحدة).
4. Actions → **build-wheels** → Run workflow، وأدخل `release_tag` مثل `wheels-2026-11-09`.
5. في التطبيق (من محرر الكود): `!pip index add https://USER.github.io/REPO/simple/` ثم `pip install opencv-python`.

## قبل الاستثمار في حزم ثقيلة: تحقق من تحميل المكتبات على جهازك
تحميل مكتبات native مثبّتة أثناء التشغيل **لم أختبره على جهاز**. التطبيق يقرأ افتراضياً فهرس Chaquopy
(`https://chaquo.com/pypi-13.1/`)، فجرّب أولاً على جهازك:

    pip install numpy
    import numpy; print(numpy.__version__)

- نجح الاستيراد ← الفكرة تعمل وتستحق بناء بقية الحزم.
- فشل ← ستظهر رسالة الخطأ في سجل `pip`؛ أرسلها لي وأعدّل آلية التحميل.

## ما لم يُحلّ بعد
- **torch / tensorflow:** وصفات Chaquopy لهما قديمة (cp38، إصدارات 2020–2021). بناؤهما لـ cp311 يحتاج ترقية الوصفات
  (وbazel لـ tensorflow)، وساعات بناء طويلة قد تتجاوز حدود GitHub Actions المجانية؛ وحجم الـ wheel يبلغ عشرات الميغابايتات أو أكثر.
- **خطوة `Download Chaquopy target`:** تحمّل بايثون الهدف من Maven؛ إن لم يوجد المجلد الافتراضي `3.11.10-0` جرّب `3.11.14-0` في خانة `target_version` عند التشغيل. أداة البناء تثبّت الـ NDK التي تحتاجها بنفسها.
- **opencv-python:** وصفته موجودة (توجد منه نسخ cp38 وcp310)، لكني لم أتحقق من نجاح بنائها لـ cp311.
- حزمة تعتمد على مكتبات مشتركة (مثل openblas) تُحمَّل عبر `chaquopy/lib/*.so`؛ هذا الافتراض لم أتحقق منه على جهاز.
