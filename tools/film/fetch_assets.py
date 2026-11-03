"""Download the free CC0 models, textures and skies the film's house uses, from Poly Haven, into E:/motion-tools/assets.
Stays out of git; rerun to get them back."""
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path("E:/motion-tools/assets")
MODELS = ["sofa_03", "mid_century_lounge_chair", "modern_coffee_table_02", "side_table_01", "dining_table", "dining_chair_02",
          "bar_chair_round_01", "potted_plant_01", "potted_plant_02", "potted_plant_04", "ceramic_vase_01", "ceramic_vase_03",
          "brass_candleholders", "modern_ceiling_lamp_01"]
TEXTURES = ["herringbone_parquet", "marble_01", "rough_linen", "floor_tiles_06", "concrete_floor"]
HDRIS = ["belfast_sunset"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "motion-tools-film/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(get(url))


def main():
    for m in MODELS:
        f = json.loads(get(f"https://api.polyhaven.com/files/{m}"))["gltf"]["1k"]["gltf"]
        save(f["url"], ROOT / "models" / m / f"{m}.gltf")
        for rel, inc in f.get("include", {}).items():
            save(inc["url"], ROOT / "models" / m / rel)
        print("model", m, flush=True)
    for t in TEXTURES:
        f = json.loads(get(f"https://api.polyhaven.com/files/{t}"))
        for key, name in (("Diffuse", "diff"), ("nor_gl", "nor"), ("Rough", "rough")):
            if key in f:
                save(f[key]["2k"]["jpg"]["url"], ROOT / "textures" / t / f"{name}.jpg")
        print("texture", t, list(f)[:12], flush=True)
    for h in HDRIS:
        f = json.loads(get(f"https://api.polyhaven.com/files/{h}"))["hdri"]["2k"]["hdr"]
        save(f["url"], ROOT / "hdri" / f"{h}.hdr")
        print("hdri", h, flush=True)


if __name__ == "__main__":
    sys.exit(main())
