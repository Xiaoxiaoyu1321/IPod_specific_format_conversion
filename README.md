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
| MGG → M4A / FLAC / MP3 | QQ 音乐加密格式，经进程解密后分别转 ALAC / FLAC / MP3 |
| MFLAC → M4A / FLAC / MP3 | 同上（MFLAC→FLAC 为整文件复制） |
| 视频 → MP4 | H.264 baseline + AAC，iPod 兼容规格（320x240） |
| 视频 → MPG | mpeg2video + mp3 |
| 封面 | （可选）所有音频转换均支持：源文件提取封面，失败则联网搜索 QQ 音乐封面并嵌入（M4A covr / MP3 APIC / FLAC pictures） |
| 歌词 | （可选）所有音频转换均支持：下载 .lrc 并嵌入标签（M4A ©lyr / MP3 USLT / FLAC LYRICS） |

> 勾选多个目标格式时，一个 QQ 音乐加密文件解密一次，即可同时产出 M4A/FLAC/MP3。

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

## 构建 Windows 版本（GitHub Actions）

仓库内置了手动触发的构建工作流：仓库页面 **Actions → "构建 Windows 版本（手动触发）" → Run workflow**。

工作流会：

1. 自动下载 **最新** gyan.dev ffmpeg 构建（`release-essentials` 稳定版 / `git-essentials` 每日版可选），仅提取 `ffmpeg.exe` 与 `ffprobe.exe`
2. 用 **PyInstaller** 打包为 **单文件 exe**（默认 `onefile`），把 ffmpeg、Frida 解密脚本一并内置——用户拿到单个 exe 即可直接使用，无需单独安装 ffmpeg
3. 上传构建产物（可在 Artifacts 下载），可选创建 GitHub Release 草稿

手动触发参数：

| 参数 | 说明 |
| --- | --- |
| ffmpeg_build | `release-essentials`（推荐，最新稳定版）/ `git-essentials`（每日最新） |
| build_mode | `onefile` 单文件 exe / `onedir` 目录 + zip |
| python_version | **Windows 7 兼容必须选 `3.9`**（3.10 起不再支持 Win7） |
| create_release | 是否同时创建 Release 草稿 |

### 本地打包（Windows 上）

```powershell
powershell -ExecutionPolicy Bypass -File build/package_windows.ps1
```

### Windows 7 兼容性说明

- **Python 3.9**：最后一个官方支持 Windows 7 的 Python（3.10+ 要求 Win8.1+）
- **PyInstaller 6.x**：bootloader 以 Windows 7 feature level（NTDDI 0x0601）编译，产出的 exe 可运行于 Win7
- **内置 ffmpeg**：gyan.dev 最新构建在 Win7/8 下需要 UCRT（KB2999226）。注意 **Python 3.9 在 Win7 上同样要求 UCRT**，二者是同一个前置条件——已安装 UCRT 的 **Windows 7 SP1** 即可直接运行
- **mgg/mflac 解密**：依赖 frida 与正在运行的 QQMusic.exe 进程，该功能的可用性取决于 frida 与 QQ 音乐客户端对 Win7 的支持。**frida 固定为 16.4.8**：frida 17.x 的 Python 源码需要 Python 3.11+，在兼容 Win7 的 Python 3.9 上无法加载（会报"frida 加载失败"），因此版本必须保持 16.x

## Frida 解密原理（bin/decrypt-qm/hook_qq_music.js）

`hook_qq_music.js` 是 **Frida 注入脚本**，是整个 mgg/mflac 解密链的核心，**仍然必须使用**，打包时已内置：

1. 在 `QQMusicCommon.dll` 中定位 `EncAndDesMediaFile` 类的构造/析构/`Open`/`GetSize`/`Read` 五个导出函数（C++ mangled 符号）
2. 通过 Frida 附加到正在运行的 `QQMusic.exe`，向目标进程注入本脚本
3. 脚本以 RPC 形式暴露 `decrypt(srcFileName, tmpFileName)`：在 QQ 音乐**自己的进程内**创建 `EncAndDesMediaFile` 对象、打开加密文件、调用其公开接口读出**已解密**的明文数据并写出

即"借 QQ 音乐进程之手解密"，不需要逆向加密算法本身。调用方为 `core/decrypt.py` 的 `QQMusicDecryptor`（引擎中 `_run_decrypt` 在运行时加载该 JS 文件），构建时必须把 `bin/decrypt-qm/hook_qq_music.js` 一并打包（`--add-data`）。

## 目录说明

```
bin/decrypt-qm/   Frida 解密脚本（hook_qq_music.js 为核心，hook_qq_music.py 为旧独立调用示例）
build/            Windows 打包脚本（package_windows.ps1）
core/             核心逻辑层（引擎/转换/解密/元数据/封面/歌词/ffmpeg 定位/配置/模型）
gui/              客户端层（PyQt5 + qfluentwidgets：转换/任务/设置三页）
legacy/           重构前的旧版脚本归档（classic / scripts / samples / windows_pack），仅供存档
tests/            单元与端到端测试
main.py           GUI 入口
main_cli.py       无 GUI 命令行入口
```

> `Legacy` 分支与 `legacy/` 目录都保留了重构前的旧代码；新功能一律以 `core/` + `gui/` 为准。

## 常见问题

**提示找不到 ffmpeg**：见上文「准备 ffmpeg」，或在设置页点击「检测」。

**提示"frida 加载失败"**：通常是 frida 版本与 Python 不兼容（frida 17.x 需 Python 3.11+，而 Win7 兼容构建使用 Python 3.9）。请使用 `pip install frida==16.4.8`（见 requirements.txt）。

**提示无法附加 QQMusic.exe**：请先启动 QQ 音乐 PC 客户端，且 mgg/mflac 解密仅在 Windows 上可用（依赖 QQMusic.exe 进程）。

## 特别鸣谢

- [decrypt-mflac-frida 项目](https://github.com/yllhwa/decrypt-mflac-frida)

## 商标声明

iPod™、iTunes™、Apple® 是 Apple Inc. 的注册商标。本软件是独立开发项目，与 Apple Inc. 没有隶属关系，也不获得 Apple Inc. 的官方认可或支持。QQ 音乐™ 是腾讯公司的注册商标。

开发者不承担因以下情形导致的任何责任：用户违反版权法造成的法律后果、转换文件的后续使用行为、技术滥用导致的账户封禁/设备损坏、用户未按时删除转换文件的行为。
