# iPod_Specific_Format_Conversion

一个可以将各种文件格式转换为适用于 **iPod** 播放格式（ALAC 无损 M4A / H.264 MP4 等）的脚本集。

> 本分支（`Next`）对项目进行了重构：将原有脚本逻辑封装为 **core（核心）+ GUI 客户端（PyQt5 / qfluentwidgets）** 两层架构，并附带无 GUI 的命令行入口，结构上类似 Clash（core 独立运行，客户端负责展示与控制）。

## 重要声明

- 本工具仅用于技术研究和**已合法获得**音频文件的格式转换
- 不得用于盗版或商业用途；所有转换操作均发生在**用户本地设备**
- 仅允许转换用户**合法拥有版权**的本地文件
- mgg/mflac 是腾讯 QQ 音乐的专有加密音频格式，相关解密技术基于社区逆向工程成果
- 本软件集成的 mgg/mflac 解密工具来自第三方开源项目 [decrypt-mflac-frida](https://github.com/yllhwa/decrypt-mflac-frida)，版权归其原始开发者所有，**仅为学习交流使用**
- 使用本软件进行的任何操作均属**用户自主行为**，用户应自行审查操作内容的合法性并承担全部责任；开发者不承担任何形式的责任
- 软件以及相关文件必须在 24 小时内删除

## 支持的功能

| 转换类型 | 说明 |
| --- | --- |
| FLAC → M4A | 转为 ALAC 无损（高于 1411Kbps 的压缩为 1411Kbps），自动提取/下载封面 |
| OGG → M4A | 同上 |
| WAV → M4A | 同上 |
| OGG → MP3 | libmp3lame 编码 |
| MGG → M4A | QQ 音乐加密格式，经进程解密后转 ALAC，联网补封面 |
| MFLAC → M4A | 同上 |
| 视频 → MP4 | H.264 baseline + AAC，iPod 兼容规格（320x240） |
| 视频 → MPG | mpeg2video + mp3 |
| 歌词 | （可选）自动下载 .lrc 歌词 |

## 架构

```
┌─────────────────────────────────────────────────────────┐
│  core/   核心层（纯 Python，无 GUI 依赖）                  │
│    engine.py    转换引擎：任务发现 / 调度 / 进度回调        │
│    converter.py ffmpeg 封装（进度解析、可中断）            │
│    decrypt.py   QQ 音乐 Frida 解密                        │
│    metadata.py  ffprobe 元数据、封面提取/嵌入              │
│    albumart.py  QQ 音乐封面搜索下载                       │
│    lyrics.py    歌词下载                                  │
│    ffmpeg.py    ffmpeg 定位与自动下载                     │
│    config.py    配置读写（config.json）                   │
│    models.py    数据模型（任务/状态/格式规格）              │
├─────────────────────────────────────────────────────────┤
│  gui/    客户端层（PyQt5 + qfluentwidgets）               │
│    main_window.py 主窗口（导航：转换/任务/设置）            │
│    worker.py      QThread 桥接 core 引擎与 Qt 信号        │
│    pages/         首页 / 任务列表 / 设置                  │
├─────────────────────────────────────────────────────────┤
│  main.py       GUI 入口                                   │
│  main_cli.py   CLI 入口（无 GUI 运行 core）               │
└─────────────────────────────────────────────────────────┘
```

核心层与界面完全解耦：`ConversionEngine` 通过 `log_cb` / `task_cb` 回调对外汇报进度，GUI 用 Qt 信号订阅，CLI 直接 `print`。

## 快速开始

### 1. 创建虚拟环境并安装依赖（清华镜像）

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> Windows 下将 `.venv/bin/pip` 换成 `.venv\Scripts\pip`。

### 2. 准备 ffmpeg

程序会按以下顺序查找 ffmpeg/ffprobe：

1. 设置页中指定的 `ffmpeg_dir`
2. 仓库内 `bin/ffmpeg` 目录
3. 系统 PATH

Linux/macOS 建议 `brew install ffmpeg` 或 `apt install ffmpeg`；Windows 可让程序自动下载（设置页/启动时提示），或手动下载后放入 `bin/ffmpeg`。

### 3. 运行

**GUI（推荐）**

```bash
.venv/bin/python main.py
```

- 「转换」页：选择输入/输出目录、勾选转换类型、开始/停止，实时查看日志与进度
- 「任务」页：每个文件的独立状态与进度表格
- 「设置」页：ffmpeg 目录、线程数、缓存保留、封面/歌词开关

**CLI（core 独立运行）**

```bash
.venv/bin/python main_cli.py -i ~/Music/in -o ~/Music/out -f flac2m4a -f ogg2mp3
.venv/bin/python main_cli.py -i ~/QQMusic -o ~/Music/out -f mgg2m4a --qq-music-dir ~/QQMusic
```

### 4. 配置

配置文件为仓库根目录 `config.json`（GUI 保存设置或 CLI 运行时自动生成），内容示例：

```json
{
  "input_dir": "",
  "output_dir": "",
  "qq_music_dir": "",
  "ffmpeg_dir": "",
  "kinds": ["flac2m4a", "ogg2m4a"],
  "keep_temp": false,
  "keep_temp_pic": false,
  "download_cover": true,
  "download_lyrics": false,
  "threads": 4,
  "process_name": "QQMusic.exe"
}
```

### 5. 运行测试

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## 目录说明

- `Classic/` 旧版单文件脚本（无 GUI，需手改路径），保留供参考
- `bin/decrypt-qm/` Frida 解密脚本（hook_qq_music.js / hook_qq_music.py）
- `Windows_Pack_Version/` 旧版 Windows 打包产物
- 仓库根目录下的旧脚本（`mgg2m4a.py`、`flac2m4a_2.0.py` 等）为重构前的整合脚本，新功能以 `core/` + `gui/` 为准

## 常见问题

**提示找不到 ffmpeg**：见上文「准备 ffmpeg」，或在设置页点击「检测」。

**提示缺少 frida / 无法附加 QQMusic.exe**：请先启动 QQ 音乐 PC 客户端，且 mgg/mflac 解密仅在 Windows 上可用（依赖 QQMusic.exe 进程）。

## 特别鸣谢

- [decrypt-mflac-frida 项目](https://github.com/yllhwa/decrypt-mflac-frida)

## 商标声明

iPod™、iTunes™、Apple® 是 Apple Inc. 的注册商标。本软件是独立开发项目，与 Apple Inc. 没有隶属关系，也不获得 Apple Inc. 的官方认可或支持。QQ 音乐™ 是腾讯公司的注册商标。

开发者不承担因以下情形导致的任何责任：用户违反版权法造成的法律后果、转换文件的后续使用行为、技术滥用导致的账户封禁/设备损坏、用户未按时删除转换文件的行为。
