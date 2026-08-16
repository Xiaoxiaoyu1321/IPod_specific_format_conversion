<#
.SYNOPSIS
    构建 Windows 单文件版本（PyInstaller + 内置最新 ffmpeg）。

.DESCRIPTION
    1. 下载最新 gyan.dev ffmpeg 构建（release-essentials 稳定版 / git-essentials 每日版）
    2. 只提取 ffmpeg.exe 与 ffprobe.exe
    3. 用 PyInstaller 打包为单文件 exe：
        - 内置 ffmpeg/ffprobe（运行时自动解压，无需用户单独安装）
        - 内置 Frida 解密脚本 bin/decrypt-qm/hook_qq_music.js
        - 图标使用 legacy/windows_pack/logo.ico

    本地 Windows 上运行（PowerShell）：
        powershell -ExecutionPolicy Bypass -File build/package_windows.ps1
    或 GitHub Actions：见 .github/workflows/build-windows.yml

    说明（Windows 7 兼容）：
        - 打包使用 Python 3.9（最后一个官方支持 Windows 7 的 Python）
        - PyInstaller 6.x 的 bootloader 以 Windows 7 feature level 编译
        - gyan.dev 最新 ffmpeg 构建在 Windows 7/8 下需要 UCRT
          （KB2999226）。注意 Python 3.9 在 Windows 7 上同样要求 UCRT，
          二者是同一个前置条件，已安装 UCRT 的 Win7 SP1 即可直接运行。
#>
param(
    [ValidateSet("release-essentials", "git-essentials")]
    [string]$FfmpegSource = "release-essentials",

    [ValidateSet("onefile", "onedir")]
    [string]$BuildMode = "onefile",

    [string]$Py = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot   # 仓库根目录
Set-Location $root

# ---------- 1. 下载最新 ffmpeg ----------
if ($FfmpegSource -eq "git-essentials") {
    $url     = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z"
    $archive = Join-Path $root "ffmpeg-git-essentials.7z"
} else {
    $url     = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $archive = Join-Path $root "ffmpeg-release-essentials.zip"
}
Write-Host "[1/4] 下载 ffmpeg ($FfmpegSource)"
Write-Host "      $url"
Invoke-WebRequest -Uri $url -OutFile $archive

$staging = Join-Path $root "build\ffmpeg_staging"
$binDir  = Join-Path $root "build\ffmpeg\bin"
New-Item -ItemType Directory -Force $staging, $binDir | Out-Null

Write-Host "[2/4] 解压并提取 ffmpeg.exe / ffprobe.exe"
if (Get-Command 7z -ErrorAction SilentlyContinue) {
    $sevenZip = "7z"
} elseif (Test-Path "C:\Program Files\7-Zip\7z.exe") {
    $sevenZip = "C:\Program Files\7-Zip\7z.exe"
} else {
    throw "未找到 7-Zip，请安装 7-Zip 或将 7z.exe 加入 PATH"
}
& $sevenZip x $archive "-o$staging" -y | Out-Null
if ($LASTEXITCODE -ne 0) { throw "解压 ffmpeg 失败" }

$src = Get-ChildItem $staging -Directory | Select-Object -First 1
Copy-Item "$($src.FullName)\bin\ffmpeg.exe"  (Join-Path $binDir "ffmpeg.exe")  -Force
Copy-Item "$($src.FullName)\bin\ffprobe.exe" (Join-Path $binDir "ffprobe.exe") -Force
& (Join-Path $binDir "ffmpeg.exe") -version | Select-Object -First 1

# ---------- 2. PyInstaller 打包 ----------
Write-Host "[3/4] PyInstaller 打包 ($BuildMode)"
$modeArg = if ($BuildMode -eq "onedir") { "--onedir" } else { "--onefile" }
& $Py -m PyInstaller --noconfirm --clean $modeArg --windowed --name IPodConverter `
    --icon "legacy\windows_pack\logo.ico" `
    --collect-all frida --collect-all qfluentwidgets --collect-all qframelesswindow `
    --hidden-import frida --hidden-import mutagen --hidden-import py7zr `
    --add-data "bin/decrypt-qm/hook_qq_music.js;bin/decrypt-qm" `
    --add-data "$binDir\ffmpeg.exe;bin\ffmpeg" `
    --add-data "$binDir\ffprobe.exe;bin\ffmpeg" `
    main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 打包失败" }

# ---------- 3. 收尾 ----------
Write-Host "[4/4] 输出产物"
if ($BuildMode -eq "onedir") {
    Compress-Archive -Path "dist\IPodConverter" `
        -DestinationPath "dist\IPodConverter-windows.zip" -Force
    Get-ChildItem "dist"
} else {
    Get-Item "dist\IPodConverter.exe" | Select-Object FullName, Length
}
Write-Host "构建完成。"
