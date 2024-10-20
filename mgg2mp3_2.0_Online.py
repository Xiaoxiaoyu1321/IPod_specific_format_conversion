#从mgg转换到mp3 的同时，自动通过网络下载当前专辑的专辑图

#导入所需要的库
import frida
import os
import hashlib
from pathlib import Path
import time
import subprocess
import json

#！！！下面是一些你需要修改的东西！！！

## 基础配置项
source_input_dir = r'' #设置为你的QQ音乐下载目录
mp3_output_dir = r'' #设置mp3 保存目录

## 缓存配置项

Keep_pic_temp = False #是否保留图片缓存

## 软件其他配置项

ffmpeg_dir = r'/bin/ffmpeg/'


# QQ音乐解密方法

def init_QD(): #初始化