import json
from pathlib import Path

catalog_path = Path(__file__).resolve().parents[1] / "assets" / "resource_catalog.json"
with open(catalog_path, "r", encoding="utf-8") as fp:
    catalog = json.load(fp)

def build_mapping(catalog):
    mapping = {}
    for char_id, info in catalog.items():
        uid = (info.get("sketchfab") or {}).get("uid")
        if uid:
            mapping[char_id] = uid
    return mapping

mapping = build_mapping(catalog)
print("Total characters:", len(mapping))
for key, value in list(mapping.items())[:5]:
    print(key, value)

js_entries = ",\n".join([f"  ['{char}','{uid}']" for char, uid in mapping.items()])
js_code = "const entries = [\n" + js_entries + "\n];\nconsole.log(entries.length);"
output_path = Path(__file__).with_name("sketchfab_uid_entries.js")
output_path.write_text(js_code, encoding="utf-8")
print("Wrote", output_path)
