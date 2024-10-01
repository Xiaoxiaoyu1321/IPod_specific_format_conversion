#导入需要的库
import frida
import os
import hashlib
from pathlib import Path
import time
import subprocess
import json
import os
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
from PIL import Image
import requests
import urllib.parse
from urllib.parse import quote  
####################################################################################################################################
#!!!下面是你需要修改的东西!!!
home = r"D:\Project\Progamming\IPod_specific_format_conversion\temp\111"#设置你的QQ 音乐下载目录
m4a_output_dir = r'D:\TEMP\454545\NMSL' #设置你的m4a 保存目录

Keep_temp = True #是否保留缓存ogg
Keep_temp_pic = False #是否保留缓存专辑图

Down_pic = True




###################################################################################################################################

#调试设置
pic_down_dir = r".\temp_pic"





#定义下载专辑图的部分
def get_qqmusic_album_pic(song_name, artist_name):  
    """  
    从QQ音乐获取歌曲的专辑封面图片URL。  
    """  
    try:  
        query = f"{song_name} {artist_name}"  
        encoded_query = quote(query)  
        search_url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={encoded_query}&format=json"  
        headers = {  
            "Referer": "https://y.qq.com/portal/player.html"  
        }  
        response = requests.get(search_url, headers=headers)  
        response.raise_for_status()  
        data = response.json()  
          
        if not data['data']['song']['list']:  
            print(f"No search results for: {song_name} by {artist_name}")  
            return None  
          
        song_info = data['data']['song']['list'][0]  
        album_url = song_info['albummid']  
        album_pic_url = f"https://y.qq.com/music/photo_new/T002R300x300M000{album_url}.jpg"  
          
        return album_pic_url  
    except requests.RequestException as e:  
        print(f"Request error: {e}")  
        return None  
    except KeyError as e:  
        print(f"Data extraction error: {e}")  
        return None  
  
def download_album_pic(album_pic_url, song_name,art_name):  
    """  
    下载专辑封面图片。  
    """  

    output_dir = pic_down_dir
    try:  
        # 确保输出目录存在  
        os.makedirs(output_dir, exist_ok=True)  
          
        # 下载专辑图  
        global pic_name
        pic_name = f"{song_name} - {art_name}.jpg"
        
        album_pic_file = os.path.join(output_dir, pic_name)  
        img_data = requests.get(album_pic_url).content  
        with open(album_pic_file, "wb") as f:  
            f.write(img_data)  
  
        return album_pic_file  
    except Exception as e:  
        print(f"Error downloading album picture: {e}")  
        return None  

#把图片嵌入到文件
def fuck_pic_to_m4a(song_file,pic_file):
    print('[Log][Pic2m4a]Song_File:',song_file)
    print('[Log][Pic2m4a]Pic_File:',pic_file)
    audio = MP4(song_file)# 打开 M4A 文件
    try:
        # 读取图片文件
        with open(os.path.join(pic_down_dir, pic_file), 'rb') as img_file:
            img_data = img_file.read()
        # 创建 MP4Cover 对象
        cover = MP4Cover(img_data, imageformat=MP4Cover.FORMAT_JPEG)
        # 添加专辑封面到 M4A 文件
        audio.tags['covr'] = [cover]
        
        # 保存修改
        audio.save()
    except:
        pass    
    


#初始化破解进程
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
    print('[Info]正在扫描mflac文件')
    for root, dirs, files in os.walk(home):
        for file in files:
            file_path= os.path.splitext(file)
            if file_path[-1] in [".mflac"]:
                total_number = total_number + 1
    print('[Info]已找到',total_number,'个匹配项')
    time.sleep(1.5)
    now_de = 0
    for root, dirs, files in os.walk(home):
        for file in files:
            file_path = os.path.splitext(file)
            
            # 只处理 .mgg 文件
            if file_path[-1] in [".mflac"]:
                now_de = now_de + 1
                print("[Info][",now_de,r'/',total_number,"]Decrypting", file)
                
                # 修改文件扩展名
                file_path = list(file_path)
                file_path[-1] = file_path[-1].replace("mflac", "flac").replace("mflac", "flac")
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
    print('[Info]已处理完flac文件')

def del_temp(file):
    if Keep_temp == False:
        os.remove(file)
def del_temp_pic(file):       
    try:
        if Keep_temp_pic == False:
            os.remove(file)
    except:
        pass



def ogg2m4a():
    # 定义输入和输出目录
    ogg_input = r'QQ-Music-decrypt-temp'
    ogg_output_dir = m4a_output_dir
    
    # 确保输出目录存在
    os.makedirs(ogg_output_dir, exist_ok=True)
    # 定义转换函数
    def convert_ogg_to_alac(source_file, output_file):
    # 使用ffprobe提取源文件的元数据
        ffprobe_command = [
            "./bin/ffmpeg/ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            source_file
        ]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True, encoding='utf-8')
        
        # 检查ffprobe命令的输出
        if result.stdout:
            try:
                metadata_json = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"[Error]Error decoding JSON: {e}")
                return
        else:
            print(f"[Warning]No output from ffprobe for file: {source_file}")
            return

        # 提取元数据标签
        tags = metadata_json.get('streams', [{}])[0].get('tags', {})
        print('[Info]Tags:',tags)
        # 创建元数据文件
        metadata_file = 'metadata.txt'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(';FFMETADATA1\n')
            for tag, value in tags.items():
                f.write(f'{tag.lower()}={value}\n')

        # 使用ffmpeg将OGG文件转换为ALAC格式并应用元数据
        ffmpeg_command = [
            "./bin/ffmpeg/ffmpeg",
            "-n",
            "-analyzeduration", "2147483647",
            "-probesize", "2147483647",
            "-i", source_file,
            "-vn",
            "-acodec", "alac",
            "-i", metadata_file,
            "-map_metadata", "1",
            "-threads", "4",  # 使用4个线程
            output_file
        ]
        subprocess.run(ffmpeg_command)



        
        #下载专辑图
        try:
            if Down_pic:
                album_pic_url = get_qqmusic_album_pic(tags['TITLE'], tags['ARTIST']) 
                if album_pic_url:  
                    downloaded_file = download_album_pic(album_pic_url, tags['TITLE'],tags['ARTIST'])  
                    if downloaded_file:  
                        print(f"[Info]picture downloaded to: {downloaded_file}")
                fuck_pic_to_m4a(output_file,pic_name)
                print('[Info]Output_file:',output_file)
                print('[Info]Pic_file:',pic_name)
        except Exception as q:
            print('[Error]',q)







        # 删除临时元数据文件
        os.remove(metadata_file)
        try:
            del_temp_pic(os.path.join(pic_down_dir, pic_name))
        except Exception as q:
            print('[Error]',q)
    # 遍历输入目录中的所有文件
    total_file = 0
    for file_name in os.listdir(ogg_input):
        if file_name.lower().endswith('.flac'):
            total_file = total_file + 1
    now_file = 0
    for file_name in os.listdir(ogg_input):
        # 检查文件是否为OGG文件
        if file_name.lower().endswith('.flac'):
            now_file = now_file + 1
            source_file_path = os.path.join(ogg_input, file_name)
            # 设置输出文件路径，扩展名为.m4a
            output_file_name = os.path.splitext(file_name)[0] + '.m4a'
            output_file_path = os.path.join(ogg_output_dir, output_file_name)
            
            # 转换文件
            convert_ogg_to_alac(source_file_path, output_file_path)
            print(f"[Info][",now_file,r'/',total_file,"]Converted {file_name} to {output_file_name}")
            del_temp(source_file_path)
            

    print("[Info]All OGG files have been converted.")




init_QD()
ogg2m4a()
