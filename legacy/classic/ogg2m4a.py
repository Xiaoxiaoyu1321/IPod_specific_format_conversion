import os
import re
import subprocess
import sys
#输入路径
#input_dir = r'D:\Music\禾念 - 洛天依共鸣合辑01｜洛天依 - Sing Sing Sing (2012) [WAV]\洛天依共鸣合集1 - Sing Sing Sing'
#input_dir = r'D:\Music\ilem - 2：3 (2019) [FLAC]\ilem - 2：3\ilem & 洛天依 & 言和 & 乐正龙牙 - 2比3 (2019) [CD2] [FLAC][IFPI-LQ220]'
input_dir = r'D:\TEMP\decrypt-mflac-frida-main\output'
#正则匹配
input_wow = r'[*.]ogg'
#输入格式
input_fuck = r'.ogg'
#输出路径
output_dir = r'D:\TEMP\nms'
#输出格式
output_fuck = r'.m4a'
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
    temp_dir = '"' +os.getcwd() + '\\' +SB_name + '.wav' + '"'
    temp_dir1 = os.getcwd() + '\\' +SB_name + '.wav' 
    now_full_output_filename ='"' + output_dir +"\\" +SB_name + output_fuck+  '"'



    #cmd = ['ffmpeg','-i',now_full_input_filename,'-vn','-acodec','alac',now_full_output_filename,'-b:a','1141k']
    #print('当前执行命令：')
    #nmsl_a = ''
    #for nmsl in cmd:
    #    nmsl_a = nmsl_a + nmsl + " "
    #print(nmsl_a)
    metadata_temp_dir = os.getcwd() + "\\" + SB_name + ".txt"

    cmd = "ffmpeg -i " + now_full_input_filename + " -f ffmetadata " + metadata_temp_dir
    print(cmd)
    print(run_shell(cmd))

    
    #cmd = "ffmpeg -i " + now_full_input_filename + " -vn -acodec alac -map_metadata 0 " + now_full_output_filename
    cmd = "ffmpeg -i " + now_full_input_filename + " -vn -acodec alac -i "+ metadata_temp_dir +" " + now_full_output_filename
    print("当前转换为m4a")
    print(cmd)
    print(run_shell(cmd))
    
    #os.remove(temp_dir1)


    #print(run_shell(nmsl_a))
