#导入需要的库
import os
import re
import subprocess
import sys
import time
import shutil
import requests
import time
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
from PIL import Image
import zipfile
from tqdm import tqdm
import platform

############################################3
#！！！以下是你需要修改的内容！！！
#输入路径
input_dir = r'D:\Music\CloudMusic' 

#输出路径
output_dir = r'D:\TEMP\nms'

#是否保存缓存
song_temp_keep=False #歌曲缓存保存
pic_temp_keep=False #专辑图缓存保存



############################################
#高级配置：
pic_temp_dir = os.getcwd()+  r"\temp\pic"
song_temp_dir =os.getcwd()+ r'\temp\wav'
ffmpeg_dir =os.getcwd() +  r'\bin\ffmpeg\ffmpeg.exe'
pack_mode = True #打包模式
version="2.0.202408270858"
#############################################
#其他配置：
force_download = False #强制要求用户下载
ffmpeg_download_url = r"https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z"
ffmpeg_download_temp_dir_dir = os.getcwd() + r'\temp\ffmpeg'
ffmpeg_download_temp_dir = ffmpeg_download_temp_dir_dir + r'\ffmpeg.7z'
ffmpeg_unzip_temp_dir = ffmpeg_download_temp_dir_dir + r"\ffmpeg_7z"


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


#定义运行Shell 方法
def run_shell(shell):
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=sys.stderr, close_fds=True,
                           stdout=sys.stdout, universal_newlines=True, shell=True, bufsize=1)

    cmd.communicate()
    return cmd.returncode
def run_shell_a(shell):
    subprocess.run(shell, shell=True)
    

#定义控制台打印方法
def console_log(log): 
    print(log)
#用户欢迎信息
def welcome_message():
    print(bcolors.OKBLUE)
    print('当前文件：flac2m4a，版本',version)
    print(f'当前Python版本：{sys.version}')

    print('当前操作系统: ',platform.system(),platform.release())
    print('')
    print('软件开发By Xiaoxiaoyu1321，此软件通过Apache-2.0 协议开源')
    print('Github 项目地址：Github项目地址：https://github.com/Xiaoxiaoyu1321/IPod_specific_format_conversion')
    print('开发者哔哩哔哩首页：https://space.bilibili.com/531456803')
    print('')
    print(bcolors.ENDC)
#要求用户提供地址
def req_dir():
    global input_dir
    global output_dir

    input_dir = input('请输入源文件目录:\n')
    output_dir = input('请输入输出目录：\n')

    print('[Info]下面是你选择的输入目录和输出目录，请检查是否正确')
    print('输入目录：',input_dir)
    print('输出目录：',output_dir)

    input('要确认吗？要确认请按下回车键')
def time_wait(timess): #时间等待逻辑
    #print('将在',timess,'秒后继续运行')
    times = 0 
    while times != timess:
        wow = timess - times
        print('将在',wow,"秒后继续")
        times = times + 1
        time.sleep(1)
#下载文件方法
def download_file(url, filename):  
    """  
    从指定URL下载文件，并显示进度条。  
      
    :param url: 文件的URL地址  
    :param filename: 保存文件的名称  
    """  
    response = requests.get(url, stream=True)  # 开启stream模式  
    response.raise_for_status()  # 如果请求返回失败的HTTP状态码，抛出HTTPError异常  
  
    # 文件总大小  
    total_size_in_bytes = int(response.headers.get('content-length', 0))  
    block_size = 1024  # 每次读取的字节数  
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)  
  
    # 使用with语句确保文件正确关闭  
    with open(filename, 'wb') as file:  
        for data in response.iter_content(block_size):  
            progress_bar.update(len(data))  # 更新进度条  
            if not data:  
                # 有些服务器使用分块编码，发送空数据块来保持连接活跃  
                break  
            file.write(data)  
  
    progress_bar.close()  # 关闭进度条 








#正则列出文件列表
def list_input_dir():
    match_file = r'.*\.flac'
    #print(match_file)
    input_dir_list_all = os.listdir(input_dir)
    
    real_file_list = []
    
    num_count = 0
    for i in input_dir_list_all:
        #try:
        #print(i)
        now_file_name =get_file_name(os.path.split(i)[1])
        #print(now_file_name)
        match = re.search(match_file,i)
        if match:
            real_file_list.append(input_dir+'\\'+i)
            num_count = num_count + 1
            print('[Info]找到第',num_count,'个匹配项',now_file_name[0])

        #except Exception as q:
            #print('[Error]加载文件',i,'时出现问题:\n',q)
            #print(i)

    print('[Info]所有文件加载完毕，共找到',num_count,'个匹配项')
    return(real_file_list)

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


#检查ffmpeg 是否存在
def check_ffmpeg(): 
    result = os.path.isfile(ffmpeg_dir)
    if force_download:
        result = False
    return(result)


#定义解压缩方法
def unzip_file(zip_path, extract_path='.'):  
    """  
    解压zip文件到指定目录  
  
    :param zip_path: zip文件的路径  
    :param extract_path: 解压到的目录，默认为当前目录  
    """  
    print('[Info]当前解压缩文件',zip_path)
    # 确保解压目录存在  
    if not os.path.exists(extract_path):  
        os.makedirs(extract_path)  
  
    # 使用zipfile的ZipFile类来打开zip文件  
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:  
        # 解压所有文件到指定目录  
        zip_ref.extractall(extract_path)  
        print(f"解压完成，文件已保存到：{extract_path}")  


#下载ffmpeg 逻辑
def download_ffmpeg():
    download_file(url=ffmpeg_download_url,filename=ffmpeg_download_temp_dir)
    #unzip_file(ffmpeg_download_temp_dir,ffmpeg_unzip_temp_dir)
    print('[Info]文件已保存至',ffmpeg_download_temp_dir,'请手动解压到exe下的bin\\ffmpeg 目录。（写7z解压逻辑要崩溃了，不写了）')
    input('在一切准备就绪后，请按下回车键继续')
    print('[Info]正在重新检查ffmpeg')
    check_ffmpeg_is()
#用户交互是否ffmpeg存在    
def check_ffmpeg_is():
    if check_ffmpeg():
        print('[Info]已在系统中检测到拓展"ffmpeg"')
    elif check_ffmpeg() == False:
        print(bcolors.WARNING)
        print('[Warning]未在系统中检测到ffmpeg')
        print(bcolors.ENDC)
        print('此软件中部分功能需要调用到ffmpeg，在此软件中是必须的。')
        print('您可以通过软件自动下载，或者手动下载ffmpeg并放置到以下路径:',ffmpeg_dir)
        need_download= input('是否需要软件自动下载(Y/n)').strip().upper() 
        if need_download == 'Y':
            download_ffmpeg()
            #time.sleep(10)
        elif need_download == "N":
            print('软件无法继续运行，即将退出')
            time.sleep(1)
            exit()
        else:
            download_ffmpeg()
    time_wait(2)
def check():
    print('')
    print('[Info]正在检查所需目录是否存在')
    check_and_create_dir(output_dir)
    check_and_create_dir(song_temp_dir)
    check_and_create_dir(pic_temp_dir)
    check_and_create_dir(ffmpeg_download_temp_dir_dir)
    print('')
    check_ffmpeg_is()

#分离文件名和后缀
def get_file_name(file):
    return os.path.splitext(file)


#获取封面的路径
def get_pic_dir(file): 
    file_name =get_file_name(os.path.split(file)[1])[0]
    pic_dir = pic_temp_dir + '\\' +  file_name  + '_cover.jpg'
    return pic_dir

#判断是否存在封面
def is_pic(file):
    result = os.path.isfile(get_pic_dir(file))
    return result

#获取缓存wav的路径
def get_wav_dir(file):
    file_name = get_file_name(os.path.split(file)[1])[0]
    wav_dir = song_temp_dir + "\\" + file_name + '.wav'
    return wav_dir

#获取输出文件名
def get_output_dir(file):
    file_name = get_file_name(os.path.split(file)[1])[0]
    wow_output= output_dir + '\\' + file_name + '.m4a'
    return(wow_output)

#提取歌曲封面方法
def take_Pic(file): 
    file_name = get_file_name(os.path.split(file)[1])[0]
    print('[Info]正在提取',file_name,'的专辑图')

    pic_dir = get_pic_dir(file)


    
    '''cmd = [
        ffmpeg_dir,
        '-i',
        file,
        '-an',
        '-vcodec','copy',pic_dir
    ]'''

    cmd = [
        ffmpeg_dir,'-y',
        '-i', file,
        '-an',
        '-vcodec', 'copy',
        '-update', '1',
        pic_dir
    ]


    run_shell_a(cmd)
    
    if os.path.isfile(pic_dir):
        print('[Info]成功提取',file_name,'的专辑图')
        return(pic_dir)
    else:
        print('[Info]提取',file_name,'的专辑图失败，可能该文件并没有专辑图')
        return(False)

#转换到1411Kbps WAV文件
def con_wav(file):
    file_name = get_file_name(os.path.split(file)[1])[0]
    print('[Info]正在转换',file_name,'到wav')
    wav_dir = get_wav_dir(file)
    cmd=[
        ffmpeg_dir,'-y',
        '-i',file,
        '-vn',
        '-acodec','pcm_s16le',
        '-ar','44100',
        '-ac','2',  
        '-map_metadata','0',
        wav_dir
    ]

    run_shell_a(cmd)
#转换为
def con_m4a(file):
    wav_dir = get_wav_dir(file)
    #if is_pic(file): #封面存在
    if False:
        cmd = [
            ffmpeg_dir,
            '-i',wav_dir,
            '-vn',
            '-acodec','alac',
            '-map_metadata','0',
            '-map','0',
            '-map','1',
            '-disposition:v:0','attached_pic',
            get_output_dir(file)   
        ]
    else:
        cmd = [
            ffmpeg_dir,'-n',
            '-i',get_wav_dir(file),
            '-vn',
            '-acodec','alac',
            '-map_metadata','0',
            get_output_dir(file)

        ]
    run_shell_a(cmd)

#嵌入封面到m4a
def fuck_pic_m4a(file):
    
    if is_pic(file):

        audio = MP4(get_output_dir(file)) #打开M4A文件
        try:
            #读取图片文件
            with open(get_pic_dir(file),'rb') as img_file:
                img_data = img_file.read()
            #创建MP4Cover 对象
            cover = MP4Cover(img_data,imageformat=MP4Cover.FORMAT_JPEG)
            #添加专辑封面到M4A文件
            audio.tags['covr'] = [cover]
            #保存修改
            audio.save()
            return True
        except Exception as q:
            print(bcolors.FAIL)
            print('[Error]添加专辑图时遇到错误：',q) 
            print(bcolors.ENDC)
            return False
        
def clean(file):
    if pic_temp_keep == False:
        try:
            os.remove(get_pic_dir(file))
        except Exception as q:
            print('[Error]',q)
    if song_temp_keep == False:
        try:
            os.remove(get_wav_dir(file))
        except Exception as q:
            print('[Error]',q)


####开始####

#检查是否为pack_mode
if pack_mode:
    welcome_message()
    req_dir()
check()
all_file = list_input_dir() #获取所有匹配文件


time_wait(5)



len_allfile = len(all_file)
count = 0
for i in all_file:
    count = count + 1
    file_name = os.path.split(i)
    print('[Info]正在处理[',count,'/',len_allfile,']',file_name)
    take_Pic(i) #提取封面
    con_wav(i)
    con_m4a(i)
    if fuck_pic_m4a(i):
        print(bcolors.OKGREEN)
        print('[Info]成功嵌入专辑图')
        print(bcolors.ENDC)
    else:
        print(bcolors.WARNING)
        print('[Error]嵌入专辑图失败')
        print(bcolors.ENDC)
    clean(i)
print(bcolors.OKGREEN)
print('[Info]所有文件转换完毕，共转换',len_allfile,'个文件')
print(bcolors.ENDC)