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


#### Basic 目录
**flac2m4a：** 提供flac到 m4a 文件的直接转换（为了能够在iPod 上播放，高于1411Kbps 的音质将被压缩为1411Kbps）      
**ogg2m4a_2.0：** 提供ogg到m4a 文件的直接转换 
**ogg2mp3_2.0：** 提供ogg到mp3 文件的直接转换   
**video2mp4_ipod：** 提供视频文件转换为iPod可播放的格式 
**wav2m4a：** 提供wav文件到 m4a 文件的转换

##### 附录：文件夹命名定义：  
在仓库根目录下的基本为整合类型，比如 *mgg2m4a*  可以协助您直接从mgg 文件转换到 m4a 文件。   
在Basic 目录下的文件，为基本转换文件，在这里您可以手动选择各个文件的转换。





## 使用方法：  
由于本项目暂未计划实现GUI界面，故您需要修改Python 文件来实现您的操作。   
一般情况下，您通过编辑器打开.py 文件的头部即可看到您需要修改的变量。    

#### Windows 的部署方法：
1.您的电脑需安装Python 3.6.6 或更新版本的Python[下载Python](https://python.org)   
2.Clone项目main 分支或从 [*Release*](https://github.com/Xiaoxiaoyu1321/IPod_specific_format_conversion/releases) 下载  
3.下载ffmpeg 并放置到 bin\\ffmpeg 文件夹 [下载 ffmpeg Windows的构建](https://www.gyan.dev/ffmpeg/builds/)     
4.通过pip 安装依赖    
```Python
# 一般情况：
pip install frida
# 无法找到pip:
python -m pip install frida
```
5.通过Python 运行您需要使用的脚本。
```
python mgg2mp4a.py
```

### 注意事项：
若要使用Basic 里面的脚本，请注意还要复制一份ffmpeg到Basic 文件夹的根目录下。  
### 特别鸣谢：
[decrypt-mflac-frida项目](https://github.com/yllhwa/decrypt-mflac-frida)  

