#导入需要的库
import os
import re
import subprocess
import sys
import time
import shutil

from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
from PIL import Image

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
ffmpeg_dir = r'.\bin\ffmpeg\ffmpeg.exe'

#############################################

#定义运行Shell 方法
def run_shell(shell):
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=sys.stderr, close_fds=True,
                           stdout=sys.stdout, universal_newlines=True, shell=True, bufsize=1)

    cmd.communicate()
    return cmd.returncode
def run_shell_a(shell):
    subprocess.run(shell, shell=True)
    
#正则列出文件列表
def list_input_dir():
    match_file = r'.*\.flac'
    #print(match_file)
    input_dir_list_all = os.listdir(input_dir)
    
    real_file_list = []
    
    num_count = 0
    for i in input_dir_list_all:
        #try:
        print(i)
        now_file_name =get_file_name(os.path.split(i)[1])
        print(now_file_name)
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
        print(f'[Info] 目录 {directory} 不存在，正在创建...')
        os.makedirs(directory)
        print(f'[Info] 目录 {directory} 创建成功')
    else:
        print(f'[Info] 目录 {directory} 已存在')
def check():
    check_and_create_dir(output_dir)
    check_and_create_dir(song_temp_dir)
    check_and_create_dir(pic_temp_dir)



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
        ffmpeg_dir,
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
        ffmpeg_dir,
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
            print('[Error]添加专辑图时遇到错误：',q) 
            return False
        
def clean(file):
    if pic_temp_keep == False:
        os.remove(get_pic_dir(file))
    if song_temp_keep == False:
        os.remove(get_wav_dir(file))


#开始
all_file = list_input_dir() #获取所有匹配文件
check()

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
        print('[Info]成功嵌入专辑图')
    else:
        print('[Info]嵌入专辑图失败')
    clean(i)

print('[Info]所有文件转换完毕')