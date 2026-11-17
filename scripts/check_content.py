#!/usr/bin/env python3
"""新车快报内容专项检查：车型名一致性、关键数字、图注编号、AI腔、标签闭合。

用法: python3 check_content.py <报告.html> [关键数字逗号分隔]
"""
import sys, re, html

def main(path, keys=""):
    s = open(path, encoding="utf-8").read()
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    body = re.sub(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", "[IMG]", body)
    txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))

    print("=== 关键数字 ===")
    for k in [x for x in keys.split(",") if x.strip()]:
        c = txt.count(k.strip())
        print(f"  {k.strip()}: {c}" + ("  ⚠缺失" if c == 0 else ""))

    print("\n=== 图注编号 ===")
    nums = re.findall(r"图\s*([\d.]+)\s*·", txt)
    print("  ", nums)

    print("\n=== AI腔套话（应为0，除原话引用）===")
    for p in ["赋能", "抓手", "闭环", "打造", "助力", "不仅仅是", "更是", "值得一提的是", "总而言之"]:
        c = txt.count(p)
        if c: print(f"  ⚠ {p}: {c}")

    print("\n=== 标签闭合 ===")
    for tag in ["section", "div", "table", "figure"]:
        o = len(re.findall(r"<%s[\s>]" % tag, s))
        c = s.count("</%s>" % tag)
        print(f"  {tag}: {o}/{c}" + ("  ✅" if o == c else "  ⚠不匹配"))

    print("\n=== 图片内联检查 ===")
    print("  base64图片数:", len(re.findall(r"data:image/jpeg;base64,", s)))
    print("  未替换占位符:", re.findall(r"__IMG_\w+__", s) or "无")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
