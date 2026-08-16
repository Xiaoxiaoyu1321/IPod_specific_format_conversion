# Legacy（旧版脚本归档）

本目录存放 **core + GUI 重构之前**（main 分支早期 / `Legacy` 分支）的全部旧版脚本，
仅作存档与参考，**不再维护**。新功能请使用仓库根目录的 `core/` + `gui/`（入口 `main.py`）。

```
legacy/
├── classic/         旧版单文件转换脚本（Classic 目录原样迁移）
│   ├── flac2m4a.py / wav2m4a.py / ogg2m4a.py / ogg2m4a_2.0.py
│   ├── ogg2mp3.py / ogg2mp3_2.0.py
│   ├── m4a_lrc.py
│   └── video_mp4_ipod.py / video_mp42mpg_ipod.py
├── scripts/         旧版"整合型"脚本（原仓库根目录，需手改路径）
│   ├── flac2m4a_2.0.py / mflac2m4a.py / mflac2m4a_2.0.py / mflac2m4a_3.0.py
│   ├── mgg2m4a.py / mgg2m4a_2.0.py / mgg2mp3_2.0_Online.py
├── samples/         旧脚本的元数据样例（ffprobe 输出 / ffmetadata）
│   ├── metadata.json / metadata.txt
└── windows_pack/    旧版 Windows 打包产物（含 flac2m4a_d102a18.exe 与 logo.ico）
```

## 旧版与新版差异（简述）

- 旧版：每个功能一个独立 `.py`，顶部硬编码 `input_dir`/`output_dir`，路径分隔符写死 `\`
- 新版：`core/` 纯逻辑层 + `gui/`（PyQt5 + qfluentwidgets）客户端 + `main_cli.py` CLI，
  配置经 `config.json` 读写，转换/解密/封面/歌词/ffmpeg 定位全部模块化

> 提示：`logo.ico` 仍被 `build/package_windows.ps1` 用作 Windows 打包图标，请勿删除。
