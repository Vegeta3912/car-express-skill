#!/usr/bin/env python3
"""用 CDP 设置真移动端视口截图并测量元素边界。

headless Chrome --window-size=390 实际 innerWidth=500（最小宽度限制），
会误报文字截断。用本脚本经 CDP Emulation.setDeviceMetricsOverride 得到真视口。

依赖: pip3 install websocket-client
用法:
  1) 启动 Chrome:
     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
       --disable-gpu --no-sandbox --remote-debugging-port=9333 \
       --user-data-dir=/tmp/cdp_brief about:blank &
  2) python3 cdp_capture.py <报告绝对路径> <输出png> [宽 高]
"""
import sys, json, urllib.request, base64, time, os
import websocket

def main(url_path, out_png, width=390, height=844, port=9333):
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % port))
    tab = [t for t in tabs if t["type"] == "page"][0]
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=15)
    seq = [0]
    def cmd(method, params={}):
        seq[0] += 1; mid = seq[0]
        ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r.get("result", {})
    cmd("Page.enable"); cmd("Runtime.enable")
    cmd("Emulation.setDeviceMetricsOverride", {
        "width": width, "height": height, "deviceScaleFactor": 1, "mobile": True})
    url = url_path if url_path.startswith("http") else "file://" + os.path.abspath(url_path)
    cmd("Page.navigate", {"url": url}); time.sleep(2.5)
    # 边界测量
    expr = """JSON.stringify({iw:innerWidth,sw:document.documentElement.scrollWidth,
      deckRight:Math.round(document.querySelector('.hero .deck').getBoundingClientRect().right),
      tocBtn:getComputedStyle(document.querySelector('.toc-toggle')).display})"""
    r = cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    print("测量:", r["result"]["value"])
    shot = cmd("Page.captureScreenshot", {"format": "png"})
    open(out_png, "wb").write(base64.b64decode(shot["data"]))
    print("截图:", out_png)
    ws.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 390
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 844
    main(sys.argv[1], sys.argv[2], w, h)
