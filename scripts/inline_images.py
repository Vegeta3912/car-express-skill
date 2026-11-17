#!/usr/bin/env python3
"""图片压缩转 base64 并注入 HTML 占位符。

用法:
  python3 inline_images.py <模板html> <图片清单json> <输出html>

图片清单 json 格式:
  {"cover": "path/to/cover.jpg", "dims": "path/to/dims.jpg", ...}
模板中用 __IMG_cover__ 这样的占位符。
"""
import sys, json, re, io, base64
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

# 每类图片的最大宽度（按 key 前缀匹配，default 兜底）
MAXW = {"cover": 1400, "underpan": 1400, "body": 1200}

def main(tpl_path, manifest_path, out_path):
    tpl = open(tpl_path, encoding="utf-8").read()
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    for key, path in manifest.items():
        im = Image.open(path).convert("RGB")
        maxw = next((v for k, v in MAXW.items() if key.startswith(k)), 1200)
        if im.width > maxw:
            im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        tpl = tpl.replace("__IMG_%s__" % key, "data:image/jpeg;base64," + b64)
        print(f"{key:12s} {im.width}x{im.height} {len(b64)//1024}KB")
    left = re.findall(r"__IMG_\w+__", tpl)
    if left:
        print("!! 未替换占位符:", left)
        sys.exit(1)
    open(out_path, "w", encoding="utf-8").write(tpl)
    print(f"已生成 {out_path}  ({len(tpl)//1024} KB)")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__); sys.exit(1)
    main(*sys.argv[1:4])
