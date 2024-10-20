#导入需要的库
import frida
import os
import hashlib
from pathlib import Path
import time
import subprocess
import json
import os
import sys
import platform
import queue
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
from PIL import Image
import requests
import urllib.parse
from urllib.parse import quote  

#Basic Info
version = 2024102001
source_dir = ''
global_output_dir = ''

#Advanced Setting
global_temp_dir =os.getcwd()+  r'\tmp'
pic_down_dir =global_temp_dir + r'\pic_down'
wav_temp_dir = global_temp_dir + r'\wav_temp'
de_temp_dir = global_temp_dir + r'\de_temp'
ffmpeg_dir =os.getcwd() +  r'\bin\ffmpeg\ffmpeg.exe'
ffmpeg_dir_dir =os.getcwd() +  r'\bin\ffmpeg'
#控制台颜色
class bcolors:  
    HEADER = '\033[95m'  
    OKBLUE = '\033[94m'  
    OKGREEN = '\033[92m'  
    WARNING = '\033[93m'  
    FAIL = '\033[91m'  
    ENDC = '\033[0m'  
    BOLD = '\033[1m'  
    UNDERLINE = '\033[4m'  
    #检查各目录是否存在：
def check_and_create_dir(directory):
    """
    检查目录是否存在，如果不存在则创建它。

    :param directory: 需要检查的目录路径
    :return: None
    """
    if not os.path.exists(directory):
        print(bcolors.WARNING)
        print(f'[Warning] 目录 {directory} 不存在，正在创建...')
        os.makedirs(directory)
        print(bcolors.OKGREEN + f'[Info] 目录 {directory} 创建成功')
        print(bcolors.ENDC)
    else:
        print(bcolors.OKGREEN)
        print(f'[Info] 目录 {directory} 已存在')
        print(bcolors.ENDC)
#Welcome Message & Ask User set dir
class get_dir_type:
    PIC = 'pic'
    SONG_OUT = 'song_out'
    WAV_TEMP = 'wav_temp'
    DE_TEMP = 'de_temp'
    DE_TEMP_TEMP = 'de_temp_temp'
def get_dir(atype,song_name):
    if atype=='pic':
        return(pic_down_dir + '\\' + song_name + '.jpg')
    elif atype == 'song_out':
        return(global_output_dir + "\\" + song_name + ".m4a")
    elif atype == 'wav_temp':
        return(wav_temp_dir + '\\' + song_name + '.wav')
    elif atype == 'de_temp':
        return(de_temp_dir)
    elif atype == 'de_temp_temp':
        return(de_temp_dir + '\\' + song_name + '.flac')
    else:
        return(output_dir + "\\" + song_name + ".m4a")
        
def welcome_Message():
    print(bcolors.OKBLUE)
    print('当前文件：mflac2m34a_3.0，版本：',version)
    print(f'当前Python 版本：{sys.version}')
    print('当前操作系统：',platform.system(),platform.release())
    print('当前目录：',os.getcwd())
    print('缓存目录：',global_temp_dir)
    print('')
    print('软件开发By Xiaoxiaoyu1321，此软件通过Apache-2.0 协议开源')
    print('Github 项目地址：Github项目地址：https://github.com/Xiaoxiaoyu1321/IPod_specific_format_conversion')
    print('开发者哔哩哔哩首页：https://space.bilibili.com/531456803')
    print('')
    print(bcolors.ENDC)
    return True


def req_dir(): #要求用户提供地址
    global source_dir
    global global_output_dir

    source_dir = input('请输入源文件目录：\n')
    global_output_dir= input('请输入输出目录:\n')

    print(bcolors.OKBLUE)
    print('[Info]下面是你选择的目录，请检查是否正确')
    print('源文件目录：',source_dir)
    print('输出文件目录：',global_output_dir)

    input('若要确认上面的目录设置，请按下回车键')

    return True

#定义运行Shell 方法
def run_shell(shell):
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=sys.stderr, close_fds=True,
                           stdout=sys.stdout, universal_newlines=True, shell=True, bufsize=1)

    cmd.communicate()
    return cmd.returncode
def run_shell_a(shell):
    subprocess.run(shell, shell=True)
    
def get_qqmusic_album_pic(song_name,art_name):
    '''
    从QQ音乐获取专辑封面图片的URL
    '''

    try:  
        query = f"{song_name} {art_name}"  
        encoded_query = quote(query)  
        search_url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={encoded_query}&format=json"  
        headers = {  
            "Referer": "https://y.qq.com/portal/player.html"  
        }  
        response = requests.get(search_url, headers=headers)  
        response.raise_for_status()  
        data = response.json()  
          
        if not data['data']['song']['list']:  
            print(f"No search results for: {song_name} by {art_name}")  
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
    
def download_album_pic(album_pic_url,song_name):
    '''
    下载和储存封面图片
    '''
    temp_dir = get_dir('pic',song_name)
    try:
        #os.makedirs(temp_dir,exist_ok=True)
        pic_file = temp_dir

        img_data = requests.get(album_pic_url).content
        with open(pic_file,'wb') as f:
            f.write(img_data)
        return pic_file


        
    except Exception as q:
        print(bcolors.WARNING)
        print("[Error][PicDown]",q)
        print(bcolors.ENDC)
    

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
    #挂起QQ Music 进程
    global session
    session = frida.attach("QQMusic.exe")

    # 加载并执行 JavaScript 脚本
    global script

    script = session.create_script(open(r"./bin/decrypt-qm/hook_qq_music.js", "r", encoding="utf-8").read())
    script.load()

    #导出目录
    output_dir = get_dir('de_temp','')
    global home
    home = os.path.abspath(source_dir)
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

def con_wav(file):
    file_name = get_dir(get_dir_type.DE_TEMP_TEMP,file)
    print('[Info]正在转换',file_name,'到wav')
    wav_dir = get_dir(get_dir_type.WAV_TEMP,file)

    cmd=[
        ffmpeg_dir,'-y',
        '-i',file_name,
        '-vn',
        '-acodec','pcm_s16le',
        '-ar','44100',
        '-ac','2',  
        '-map_metadata','0',
        wav_dir
    ]

    run_shell_a(cmd)

def con_m4a(song_name,tags):
    metadata_file = 'metadata.txt'
    ffmpeg_command = [
        ffmpeg_dir,
        '-n',
        "-i",get_dir(get_dir_type.WAV_TEMP,song_name),
        '-vn',
        '-acodec','alac',
        '-metadata','title='+tags['TITLE'],
        '-metadata','artist='+tags['ARTIST'],
        '-metadata','album='+tags['ALBUM'],
        '-threads','4',
        get_dir(get_dir_type.SONG_OUT,song_name)
    ]
    subprocess.run(ffmpeg_command)
def get_source_info(file):
        print('[Info][Get_source]file:',file)
    # 使用ffprobe提取源文件的元数据
        ffprobe_command = [
            ffmpeg_dir_dir +"\\ffprobe.exe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file
        ]
        print('[Info][GetSource]Commond:',ffprobe_command)
        #run_shell_a(ffprobe_command)
        result = subprocess.run(ffprobe_command, capture_output=True, text=True, encoding='utf-8')
        print(result.stdout)
        # 检查ffprobe命令的输出
        if result.stdout:
            try:
                metadata_json = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"[Error]Error decoding JSON: {e}")
                return
        else:
            print(f"[Warning]No output from ffprobe for file: {file}")
            return

        # 提取元数据标签
        tags = metadata_json.get('format', [{}]).get('tags', {})
        print('[Info]Tags:',tags)
        # 创建元数据文件
        metadata_file = 'metadata.txt'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(';FFMETADATA1\n')
            for tag, value in tags.items():
                f.write(f'{tag.lower()}={value}\n')
        
        return(tags)

def c_main(): #转换全流程
    #首先调用解密脚本，把所有的文件解密
    init_QD()


    #遍历所有解密文件
    all_flac_file_list = []
    count_num_flac_temp = 0
    for fuck_file in os.listdir(get_dir(get_dir_type.DE_TEMP,'')):
        if fuck_file.lower().endswith('.flac'):
            all_flac_file_list.append(fuck_file)
            count_num_flac_temp = count_num_flac_temp + 1
            
    print(all_flac_file_list)
    
    #正式开始针对每个文件转换
    for i in all_flac_file_list:
        #分离后缀
        fname,ext = os.path.splitext(i)

        con_wav(fname)
        tags = get_source_info(get_dir(get_dir_type.DE_TEMP_TEMP,fname))
        #print('tags',tags)
        
        try:
            url_down = get_qqmusic_album_pic(tags['TITLE'],tags['ARTIST'])
            print('[Info][DownloadPic]Cover URL:',url_down)
            download_album_pic(url_down,fname)

        except Exception as q:
            print('[Error][DownloadPic]',q)

        try:
            con_m4a(fname,tags)
        except Exception as q:
            print("[Erorr][con_m4a]",q)

        try:
            fuck_pic_to_m4a(get_dir(get_dir_type.SONG_OUT,fname),get_dir(get_dir_type.PIC,fname))

        except Exception as q:
            print('[Error][Cover m4a]',q)


def main():
    welcome_Message()
    req_dir()
    #检查创建目录
    check_and_create_dir(global_temp_dir)
    check_and_create_dir(global_output_dir)
    check_and_create_dir(wav_temp_dir)
    check_and_create_dir(pic_down_dir)
    check_and_create_dir(de_temp_dir)
    c_main()


main()
