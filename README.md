# iPod_Specific_Format_Conversion
一个可以用来将各种文件格式转换为适用于iPod的脚本集    

## 实现的基本功能   
- [x] mgg -> m4a
- [x] flac -> m4a (1411Kbps)
- [x] ogg -> m4a
- [x] mp4 (适用于iPod 的规格)
- [x] wav -> m4a
- [x] mflac -> m4a
- [x] mgg -> m4a
## 文件说明：   

#### 仓库根目录
**mgg2m4a：** 提供mgg 到 m4a 文件的直接转换   
**mgg2m4a_2.0：** 在保留mgg 到 m4a 文件的转换同时，自动从服务器下载歌曲封面并嵌入到m4a文件内    
**mflac2m4a：** 提供mflac到m4a文件的直接转换    
**flac2m4a_2.0.py:** 提供flac到m4a 的转换，与旧版本不同的是，此版本增加了专辑图支持   

#### Classic 目录
**flac2m4a：** 提供flac到 m4a 文件的直接转换（为了能够在iPod 上播放，高于1411Kbps 的音质将被压缩为1411Kbps）      
**ogg2m4a_2.0：** 提供ogg到m4a 文件的直接转换     
**ogg2mp3_2.0：** 提供ogg到mp3 文件的直接转换     
**video2mp4_ipod：** 提供视频文件转换为iPod可播放的格式     
**wav2m4a：** 提供wav文件到 m4a 文件的转换    

##### 附录：文件夹命名定义：  
在仓库根目录下的基本为整合类型，比如 *mgg2m4a*  可以协助您直接从mgg 文件转换到 m4a 文件。   
在Classic 目录下的文件，为基本转换文件，在这里您可以手动选择各个文件的转换。





## 使用方法：  
由于本项目暂未计划实现GUI界面，故您需要修改Python 文件来实现您的操作。   
一般情况下，您通过编辑器打开.py 文件的头部即可看到您需要修改的变量。    

理论上根据Python 的兼容性，在Windows、Linux 和 macOS 上都可以正常运行

### Windows 的部署方法：

#### 使用编译的exe（推荐）     
1.前往[``Release页面``](https://github.com/Xiaoxiaoyu1321/IPod_specific_format_conversion/releases)下载最新的exe Release 版本。    
2.直接运行该程序
    
#### 手动执行修改和执行Python 文件（备用）    
1.您的电脑需安装Python 3.6.6 或更新版本的Python[下载Python](https://python.org)   
2.Clone项目main 分支或从 [*Release*](https://github.com/Xiaoxiaoyu1321/IPod_specific_format_conversion/releases) 下载  
3.下载ffmpeg 并放置到 bin\\ffmpeg 文件夹 [下载 ffmpeg Windows的构建](https://www.gyan.dev/ffmpeg/builds/)     
4.通过pip 安装依赖    
```Terminal
# 自动安装
>> pip install -r requirements.txt
# 手动安装
>> pip install frida
>> pip install ....
```
5.通过编辑器如``notepad``或``notepad++`` 等工具打开您需要使用的脚本，如``flac2m4a_2.0.py``      
     
在这里，您可以注意到开头存在一些您需要修改的部分
```python
……

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
……
```
将上面的``input_dir``和``output_dir``更改为您的路径，然后保存文件。

6.通过Python 运行您需要使用的脚本。
```
python flac2m4a_2.0.py
```

### Linux & macOS 部署方法：   
1. 检查python3 版本是否≥ 3.6.6   
```
>> python3 --version
Python 3.11.2
```
2. 检查是否已安装pip   
```
>> python3 -m pip --version
pip 23.0.1 from /usr/lib/python3/dist-packages/pip (python 3.11)
```
若未安装pip，请先安装pip，或在后面的过程中手动下载包并配置Python 环境    
```Terminal
>> sudo apt install python3-pip
```
3. 从Github 克隆仓库到本地或下载zip 文件并解压   
4. 前往[ffmpeg 官网](https://ffmpeg.org/download.html)，下载ffmpeg 独立程序并放置在 bin\\ffmpeg 文件夹下   
5. 通过pip 安装所需包：
```Terminal
# 自动安装
>> pip install -r requirements.txt
# 手动安装
>> pip install frida
>> pip install ....
```

6.通过编辑器如``vim``或``nano``打开您需要使用的脚本，如``flac2m4a_2.0.py``。    
在这里，您可以注意到开头存在一些您需要修改的部分
```python
……

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
……
```
将上面的``input_dir``和``output_dir``更改为您的路径，然后保存文件。
7.执行所需的项目文件
```Terminal
>> python3 flac2m4a_2.0.py
```



## 常见问题Q&A：
**为什么使用Classic 里的脚本时，提示找不到ffmepg:**  
若要使用Classic 里面的脚本，请注意还要复制一份ffmpeg到Basic 文件夹的根目录下。  
**为什么我在运行脚本时提示缺少库**    
每个脚本使用的库可能存在差异，若缺少某个库，请直接使用pip 安装行了。   

## 特别鸣谢：
[decrypt-mflac-frida项目](https://github.com/yllhwa/decrypt-mflac-frida)  

