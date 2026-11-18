#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工信部《道路机动车辆生产企业及产品公告》参数查询
================================================================
用途：取「前悬/后悬、轴荷、轮距、整备质量、总质量、接近/离去角、额定载客」
等公告原值（媒体转引常缺轴荷，官网不公布）。

用法:
  python3 miit_gonggao.py search 腾势            # 列该品牌全部公告型号（自动翻页）
  python3 miit_gonggao.py model SKE6522          # 按型号前缀逐条取参数
  python3 miit_gonggao.py param Z AC282252 410   # 取单个产品参数（Z=整车，gid，批次）

原理与坑（详见 references/工信部公告查询.md）:
  1) 参数页 queryCpData 带滑块验证，但校验完全在前端：x/y 由 JS 随机、token 只判非空，
     直接 POST NECaptchaValidate=<任意 65 位串> 即可拿到参数页。
  2) 有频控：连续抓取约 8 次会被封（"访问频率过高"），单次间隔建议 ≥25 秒，
     被封后等待约 3 分钟。脚本内置间隔与重试。
  3) 列表接口 doCpQueryByeOne 返回 JSON、不受频控影响，先用它拿 gid + 批次。
"""
import sys
import time
import random
import string
import html
import re

import requests

BASE = "https://service.miit-eidc.org.cn/miitxxgk/gonggao/xxgk"
HDRS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Accept-Language": "zh-CN,zh;q=0.9",
}
FIELDS = ["产品号", "产品ID", "批次", "发布日期", "企业名称", "产品商标", "车辆型号", "车辆名称",
          "外形尺寸长", "外形尺寸宽", "外形尺寸高", "总质量", "整备质量", "额定载客",
          "接近角/离去角", "最高车速", "轴荷", "前悬后悬", "轴数", "轴距", "前轮距", "后轮距",
          "轮胎规格", "燃料种类", "发动机型号", "发动机功率", "储能装置种类"]
SEP = "\u0001"
S = requests.Session()
S.headers.update(HDRS)


def _token():
    al = string.ascii_letters + string.digits
    return "".join(random.choice(al) for _ in range(65))


def _clean(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"<[^>]+>", SEP, h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\r\n]+", " ", h)
    return re.sub(r"(%s\s*)+" % SEP, SEP, h)


def list_models(brand, page_size=10, max_page=30):
    """按品牌/关键词列全部公告型号（JSON 接口，自动翻页）。"""
    rows = []
    for p in range(1, max_page + 1):
        r = S.post(BASE + "/doCpQueryByeOne",
                   data={"querylb": "cp", "querydata": brand,
                         "pageSize": str(page_size), "pageNum": str(p)},
                   headers={"X-Requested-With": "XMLHttpRequest"}, timeout=40)
        d = r.json()
        for it in d.get("cpList", []):
            rows.append({"gid": it["gid"], "pc": it["pc"], "tag": it.get("dataTag", "Z"),
                         "model": it["clxh"], "name": it["clmc"], "brand": it.get("cpsb", ""),
                         "oem": it.get("qymc", "")})
        if p >= d.get("countResult", {}).get("totalPage", 1):
            break
    return rows


def param(tag, gid, pc, wait=25, retries=4):
    """取单个产品参数页。返回 dict；失败返回 {'_error': ...}。"""
    url = BASE + "/queryCpData"
    q = {"dataTag": tag, "gid": gid, "pc": pc}
    for attempt in range(retries):
        r = S.get(url, params=q, timeout=40)
        r.encoding = "utf-8"
        if "访问行为验证" in r.text:
            r = S.post(url, data=dict(q, NECaptchaValidate=_token()),
                       headers={"Referer": url}, timeout=40)
            r.encoding = "utf-8"
        if "禁止" in r.text and "频率" in r.text:
            if attempt == retries - 1:
                return {"_error": "访问频率过高，等待后重试"}
            time.sleep(180)
            continue
        t = _clean(r.text)
        if "前悬后悬" not in t:
            if attempt == retries - 1:
                return {"_error": "未取到参数页"}
            time.sleep(wait)
            continue
        parts = [p.strip() for p in t.split(SEP)]
        out = {}
        for i, p in enumerate(parts):
            if p in FIELDS and p not in out and i + 1 < len(parts) and parts[i + 1]:
                out[p] = parts[i + 1]
        m = re.search(r"备注[:：]?\s*(.{0,800})", t)
        if m:
            out["备注"] = m.group(1)
        return out
    return {"_error": "未知失败"}


def _line(m, f):
    def g(k):
        return f.get(k, "-") or "-"
    dim = "%s×%s×%s" % (g("外形尺寸长"), g("外形尺寸宽"), g("外形尺寸高"))
    tail = ""
    fz, hz = f.get("前悬后悬", ""), f.get("轴荷", "")
    if "/" in fz and "/" in hz:
        try:
            a, b = [int(x) for x in fz.split("/")]
            wb = int(g("外形尺寸长"))
            ok = (a + int(g("轴距")) + b == wb)
            tail = " 自洽:%s" % ("OK" if ok else "不一致(前悬+轴距+后悬≠车长)")
        except Exception:
            pass
    return ("%s 批%s | %s | 轴距 %s | 前悬/后悬 %s | 轴荷 %s | 整备 %s | 总质量 %s | "
            "轮距 %s/%s | 接近/离去 %s | 胎 %s%s") % (
        m["model"], m["pc"], dim, g("轴距"), g("前悬后悬"), g("轴荷"), g("整备质量"),
        g("总质量"), g("前轮距"), g("后轮距"), g("接近角/离去角"), g("轮胎规格"), tail)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "search":
        for r in list_models(sys.argv[2]):
            print(r["pc"], r["model"], r["name"], r["brand"], r["gid"])
    elif cmd == "model":
        key = sys.argv[2].upper()
        rows = [r for r in list_models(sys.argv[2][:6]) if key in r["model"].upper()]
        for i, r in enumerate(rows):
            f = param(r["tag"], r["gid"], r["pc"])
            if "_error" in f:
                print(r["model"], r["pc"], "ERROR", f["_error"])
            else:
                print(_line(r, f))
            if i < len(rows) - 1:
                time.sleep(25)
    elif cmd == "param":
        for k, v in param(sys.argv[2], sys.argv[3], sys.argv[4]).items():
            print("%s: %s" % (k, v))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
