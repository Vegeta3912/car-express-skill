# car-express-skill · 新车快报生成器

给一款新车名，产出一份**整车架构视角**的 HTML 快报——像资深整车工程师写的技术解剖，而不是几篇媒体报道的拼接。

产出的报告与 [问界新 M8 快报](examples/问界新M8_新车快报.html) 版式完全一致：单文件、样式/脚本/图片全内联、离线可开、一页上下通读。

## 它做什么

- **一手取证**：下载并转录官方发布会视频，逐帧核对技术画面；抓官网车型页原图；查汽车之家、工信部公告等权威参数。
- **架构主线**：围绕下车体布置、平台三电、底盘、智能安全展开，不是配置表罗列。
- **参数推算**：L113/H30 等车内硬点按 SAE J1100 定义做区间估算，轮胎直径/离地角/迎风面积做可复现几何推算，推算值明确标注、不伪造精确值。
- **可溯源**：全文 `[n]` 信源上标，附录列信源清单与口径处理说明。
- **版式固定**：复用同一套 CSS/JS 模板，谁生成都是同样的样式。

## 怎么用

### 在你的 AI Agent 里（WorkBuddy / Claude Code 等）

安装（见下）后，直接说：

```
使用这个 skill，分析 问界新M8
```

或更具体：

```
使用 car-express-skill，生成 小米YU7 的新车快报，
发布会视频 https://www.bilibili.com/video/xxx，图片只用官网原图。
```

Agent 会自动按标准流程取证、推算、套模板、自检，最后产出 `XXX_新车快报.html`。

开工前它通常只问你四件事：是否出视觉样张、发布会视频来源、图片口径、水印文字/logo。

### 安装到不同 Agent

| Agent | 安装方式 |
|---|---|
| **WorkBuddy** | 把本仓库放到 `~/.workbuddy/skills/car-express-skill/`，重启会话即生效 |
| **Claude Code** | 放到 `~/.claude/skills/car-express-skill/`（项目级则放 `<项目>/.claude/skills/`） |
| **其他支持 SKILL.md 的 Agent** | 把整个目录放到该 Agent 的 skills 目录即可；核心是让 Agent 能读到 `SKILL.md` |

无论哪种，都是**复制整个目录**（含 `assets/`、`references/`、`scripts/`），不要只拿 `SKILL.md`——样式模板和脚本都在里面。

## 目录结构

```
car-express-skill/
├── SKILL.md                          # Agent 读的主指令，定义触发与工作流
├── README.md                         # 本文件
├── assets/
│   └── report-template.html          # 骨架模板：完整 CSS/JS + {{占位符}} + __IMG_xxx__
├── references/
│   ├── 样式规范.md                    # 版式设计系统（配色/层次/留白），填内容前必读
│   └── 参数推算法.md                  # 硬点定义与 A/B 类推算公式
├── scripts/
│   ├── inline_images.py              # 图片压缩转 base64 注入占位符
│   ├── check_content.py              # 内容专项检查（数字/图注/AI腔/标签闭合）
│   └── cdp_capture.py                # 真移动端视口截图与边界测量
└── examples/
    └── 问界新M8_新车快报.html         # 完整成品范例（对照版式与内容深度）
```

## 环境依赖

```bash
pip3 install pillow websocket-client yt-dlp imageio-ffmpeg
```

- **Pillow**：图片压缩与拼核对墙
- **websocket-client**：CDP 真移动端截图
- **yt-dlp / imageio-ffmpeg**：下载与合并发布会视频
- 音频转录用宿主 Agent 提供的工具（WorkBuddy 的 AudioTranscribe）
- 需要本机有 Chrome（用于视觉自检截图）

不联网取证也能用：把参数与图片素材准备好，Agent 可直接套模板生成。

## 自检清单（Agent 产出后会跑）

- 车型名一致、关键数字齐全、图注编号连续、无 AI 腔套话
- 图片画面与所在章节匹配
- 1440 桌面 + 390 移动无溢出/重叠/乱码
- HTML 标签开闭平衡、11 张图全内联、占位符全部替换

## 许可

MIT License.
