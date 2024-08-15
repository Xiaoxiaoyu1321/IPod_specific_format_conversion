# iPod_Specific_Format_Conversion
一个可以用来将各种文件格式转换为适用于iPod的脚本集    

### 实现的基本功能   
- [x] mgg -> m4a
- [x] flac -> m4a (1411Kbps)
- [x] ogg -> m4a
- [x] mp4 (适用于iPod 的分辨率与码率)
- [x] wav -> m4a

### 文件夹命名定义：  
在仓库根目录下的基本为整合类型，比如* mgg2m4a * 可以协助您直接从mgg 文件转换到 m4a 文件。   
在Basic 目录下的文件，为基本转换文件，在这里您可以手动选择各个文件的转换。




### 使用方法：  
1.您的电脑需安装Python 3.6.6 或更新版本的Python   
2.下载ffmpeg 并放置到 bin\\ffmpeg 文件夹 [ffmpeg Windows的构建](https://www.gyan.dev/ffmpeg/builds/)     
3.通过pip 安装依赖    
```Python
# 一般情况：
pip install frida
# 无法找到pip:
python -m pip install frida
```
4.通过Python 运行您需要使用的脚本。
```
python mgg2mp4a.py
```

### 注意事项：
若要使用Basic 里面的脚本，请注意还要复制一份ffmpeg到Basic 文件夹的根目录下。  
### 特别鸣谢：
[decrypt-mflac-frida项目](https://github.com/yllhwa/decrypt-mflac-frida)  

