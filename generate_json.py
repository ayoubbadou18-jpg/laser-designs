import json
import re
from datetime import datetime, timezone
import requests

OWNER = "ayoubbadou18-jpg"
REPO = "laser-designs"
BRANCH = "main"

FILES_PATH = "assets/files"
IMAGES_PATH = "assets/images"

INPUT_JSON = "laser-files.json"
OUTPUT_JSON = "laser-files.generated.json"

# ✅ اختَر أين تريد إضافة الملفات الجديدة:
TARGET_CATEGORY_ID = "curtains"  # غيّرها مثلاً إلى "decor" أو اكتب "repo_designs" لإنشاء تصنيف جديد

# لو أنشأنا تصنيف جديد:
NEW_CATEGORY_TEMPLATE = {
    "id": "repo_designs",
    "name": "📁 مكتبة التصاميم (GitHub)",
    "type": "designs",
    "order": 12,
    "description": "تصاميم تمت إضافتها تلقائياً من مستودع GitHub.",
    "files": []
}

SUPPORTED_FILE_EXT = {"dxf", "svg", "pdf", "ai", "cdr"}
SUPPORTED_IMG_EXT = {"jpg", "jpeg", "png", "webp"}

def gh_contents(path: str):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response for {path}")
    return data

def stem(name: str):
    # إزالة الامتداد + توحيد المسافات والشرطة
    base = re.sub(r"\.[^.]+$", "", name.strip())
    base = base.replace("_", " ").replace("-", " ")
    base = re.sub(r"\s+", " ", base).strip().lower()
    return base

def ext(name: str):
    m = re.search(r"\.([^.]+)$", name.lower().strip())
    return m.group(1) if m else ""

def nice_title(filename: str):
    base = re.sub(r"\.[^.]+$", "", filename.strip())
    base = base.replace("_", " ").replace("-", " ")
    base = re.sub(r"\s+", " ", base).strip()
    return base

def make_id(prefix: str, filename: str):
    s = stem(filename)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return f"{prefix}_{s}"[:60]

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        app = json.load(f)

    categories = app.get("categories", [])
    if not isinstance(categories, list):
        raise RuntimeError("Invalid input json: categories must be a list")

    files_list = gh_contents(FILES_PATH)
    imgs_list = gh_contents(IMAGES_PATH)

    # خريطة الصور حسب stem
    img_map = {}
    for it in imgs_list:
        name = it.get("name", "")
        if it.get("type") != "file":
            continue
        e = ext(name)
        if e in SUPPORTED_IMG_EXT:
            img_map[stem(name)] = it.get("download_url") or it.get("html_url")

    generated_items = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for it in files_list:
        name = it.get("name", "")
        if it.get("type") != "file":
            continue
        e = ext(name)
        if e not in SUPPORTED_FILE_EXT:
            continue

        file_stem = stem(name)
        image_url = img_map.get(file_stem, "https://i.imgur.com/8Q2Q2Qp.png")  # placeholder

        generated_items.append({
            "id": make_id("gh", name),
            "title": nice_title(name),
            "description": "ملف جاهز للقص/الحفر بالليزر.",
            "format": e.upper(),
            "imageUrl": image_url,
            "downloadUrl": it.get("download_url") or it.get("html_url"),
            "createdAt": now,
            "downloadsCount": 0,
            "viewsCount": 0,
            "rating": 0.0,
            "ratingCount": 0,
            "isFeatured": False,
            "isEditable": True,
            "isReadyToCut": True,
            "usageType": "cut",
            "materialType": "",
            "productType": "",
            "tags": ["GitHub", e.upper()]
        })

    # رتّب العناصر أبجديًا
    generated_items.sort(key=lambda x: x["title"])

    # ضعها داخل التصنيف المطلوب
    target = None
    for c in categories:
        if c.get("id") == TARGET_CATEGORY_ID:
            target = c
            break

    if target is None:
        # أنشئ تصنيف جديد
        new_cat = dict(NEW_CATEGORY_TEMPLATE)
        new_cat["files"] = generated_items
        categories.append(new_cat)
    else:
        existing = target.get("files", [])
        if not isinstance(existing, list):
            existing = []
        # دمج بدون تكرار بالـ id
        existing_ids = {x.get("id") for x in existing if isinstance(x, dict)}
        for item in generated_items:
            if item["id"] not in existing_ids:
                existing.append(item)
        target["files"] = existing

    app["categories"] = categories

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(app, f, ensure_ascii=False, indent=2)

    print(f"✅ Done. Added {len(generated_items)} items.")
    print(f"📄 Output: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
