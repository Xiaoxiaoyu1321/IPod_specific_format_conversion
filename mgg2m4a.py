#导入需要的库
import frida
import os
import hashlib
from pathlib import Path
import time
import subprocess
import json
import os

#!!!下面是你需要修改的东西!!!
home = r"D:\Music\QQ_Music_Download\VipSongsDownload"#设置你的QQ 音乐下载目录
m4a_output_dir = r'' #设置你的m4a 保存目录


def init_QD():


    # 挂钩 QQ 音乐进程
    global session
    session = frida.attach("QQMusic.exe")
    

    # 加载并执行 JavaScript 脚本
    global script

    script = session.create_script(open(r"./bin/decrypt-qm/hook_qq_music.js", "r", encoding="utf-8").read())
    script.load()

    # 创建输出目录
    output_dir = "QQ-Music-decrypt-temp" #QQ_Music_Temp
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取用户音乐目录路径
    global home
    home = os.path.abspath(home)
    # 遍历目录下的所有文件
    total_number = 0
    print('[Info]正在扫描ogg文件')
    for root, dirs, files in os.walk(home):
        for file in files:
            file_path= os.path.splitext(file)
            if file_path[-1] in [".mgg"]:
                total_number = total_number + 1
    print('[Info]已找到',total_number,'个匹配项')
    time.sleep(1.5)
    now_de = 0
    for root, dirs, files in os.walk(home):
        for file in files:
            file_path = os.path.splitext(file)
            
            # 只处理 .mgg 文件
            if file_path[-1] in [".mgg"]:
                now_de = now_de + 1
                print("[Info][",now_de,r'/',total_number,"]Decrypting", file)
                
                # 修改文件扩展名
                file_path = list(file_path)
                file_path[-1] = file_path[-1].replace("mflac", "flac").replace("mgg", "ogg")
                file_path_str = "".join(file_path)
                
                # 检查解密文件是否已经存在
                output_file_path = os.path.join(output_dir, file_path_str)
                if os.path.exists(output_file_path):
                    print('[Info]',f"File {output_file_path} 已存在，跳过.")
                    continue

                tmp_file_path = hashlib.md5(file.encode()).hexdigest()
                tmp_file_path = os.path.join(output_dir, tmp_file_path)
                tmp_file_path = os.path.abspath(tmp_file_path)
                
                # 调用脚本中的 decrypt 方法解密文件
                data = script.exports_sync.decrypt(os.path.join(root, file), tmp_file_path)
                
                # 重命名临时文件
                os.rename(tmp_file_path, output_file_path)

    # 分离会话
    session.detach()
    print('[Info]已处理完成mgg文件')

def ogg2m4a():
    # 定义输入和输出目录
    ogg_input = r'QQ-Music-decrypt-temp'


init_QD()
