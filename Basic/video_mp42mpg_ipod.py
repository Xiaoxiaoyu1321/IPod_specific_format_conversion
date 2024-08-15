import os
import re
import subprocess
import sys
#输入路径
#input_dir = r'D:\Music\洛天依×乐正绫 - TUNO桐音 - 南北寻光 (Final Edition, A + B Side) (2015) [FLAC]\南北寻光B'
#input_dir = r'D:\Music\ilem - 2：3 (2019) [FLAC]\ilem - 2：3\ilem & 洛天依 & 言和 & 乐正龙牙 - 2比3 (2019) [CD2] [FLAC][IFPI-LQ220]'
#input_dir = r'C:\Users\Xiaoxiaoyu\Desktop\妄想症系列'
#input_dir = r'D:\Downloads\Videos\Vsinger Live 2017洛天依全息演唱会【官方录播完整版】'
input_dir = r'E:\DownKyi-1.6.1\Media\从0开始学编曲'
#正则匹配
input_wow = r'[*.]mp4'
#输入格式
input_fuck = r'.mp4'
#输出路径
output_dir = r'D:\TEMP\nms'
#输出格式
output_fuck = r'.mpg'
#print(input_wow)
input_dir_list = os.listdir(input_dir)
print('已找到的文件：')
print(input_dir_list)

match_filename = []

#运行shell
def run_shell(shell):
    cmd = subprocess.Popen(shell, stdin=subprocess.PIPE, stderr=sys.stderr, close_fds=True,
                           stdout=sys.stdout, universal_newlines=True, shell=True, bufsize=1)

    cmd.communicate()
    return cmd.returncode

#matches = re.findall(input_wow, input_dir_list)
#print(matches)
for i in input_dir_list:
    now_match = re.search(input_wow,i)
    if now_match:
        print(i)
        match_filename.append(i)
    else:
        print(now_match)


for i in match_filename:
    SB = i.split('.') #看看你妈有几个点
    SB_time = 0 #循环次数
    SB_fuckyou = len(SB) #总个数
    for iSB in SB: 
        SB_time = SB_time + 1 #技术
        if SB_time == SB_fuckyou: #达到最大次数
            pass
        elif SB_time < SB_fuckyou and SB_time != 1: #不是第一次的
            SB_name = SB_name + '.' + iSB
        elif SB_time == 1: #是第一次的
            SB_name = iSB

    print('当前处理：',SB_name)
        
    #完整输入文件名
    now_full_input_filename ='"'+ input_dir  +"\\" +SB_name + input_fuck + '"'
    now_full_output_filename ='"' + output_dir +"\\" +SB_name + output_fuck+  '"'



   # cmd = ['ffmpeg','-i',now_full_input_filename,'-vn','-acodec','alac',now_full_output_filename,'-b:a','1141k']
    print('当前执行命令：')
    #nmsl_a = ''
    #for nmsl in cmd:
    #    nmsl_a = nmsl_a + nmsl + " "
    #nmsl_a = r"ffmpeg -y -i "+now_full_input_filename + r" -c:a aac -b:a 160k -c:v libx264 -profile:v baseline -level 3.0 -pix_fmt yuv420p -r 30 -crf 23 -b:v 1500k -s 640x480 -movflags +faststart " + now_full_output_filename
    nmsl_a = r"ffmpeg -i " +  now_full_input_filename+ " -vf "+'"'+r"scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2"+'"'+r" -r 30 -c:v mpeg2video -b:v 1000k -c:a mp3 -b:a 160k " + now_full_output_filename
    print(nmsl_a)

    print(run_shell(nmsl_a))
