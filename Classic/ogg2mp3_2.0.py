import subprocess
import json
import os

# 定义输入和输出目录
input_dir = r'D:\Music\QQ_Music_Unlocked'  # 替换为你的输入目录路径
output_dir = r'D:\Music\QQ_Music_Unlocked_mp3'  # 替换为你的输出目录路径

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 定义转换函数
def convert_ogg_to_mp3(source_file, output_file):
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
            print(f"Error decoding JSON: {e}")
            return
    else:
        print(f"No output from ffprobe for file: {source_file}")
        return

    # 提取元数据标签
    tags = metadata_json.get('streams', [{}])[0].get('tags', {})

    # 构建元数据参数
    metadata_args = []
    for tag, value in tags.items():
        metadata_args.extend(["-metadata", f"{tag.lower()}={value}"])

    # 使用ffmpeg将OGG文件转换为MP3格式并应用元数据
    ffmpeg_command = [
        "./bin/ffmpeg/ffmpeg",
        "-y",  # 自动确认覆盖输出文件
        "-analyzeduration", "2147483647",
        "-probesize", "2147483647",
        "-i", source_file,
        "-vn",
        "-acodec", "libmp3lame",
        "-threads", "4",  # 使用4个线程
    ] + metadata_args + [output_file]
    
    subprocess.run(ffmpeg_command)

# 遍历输入目录中的所有文件
for file_name in os.listdir(input_dir):
    # 检查文件是否为OGG文件
    if file_name.lower().endswith('.ogg'):
        source_file_path = os.path.join(input_dir, file_name)
        # 设置输出文件路径，扩展名为.mp3
        output_file_name = os.path.splitext(file_name)[0] + '.mp3'
        output_file_path = os.path.join(output_dir, output_file_name)
        
        # 转换文件
        convert_ogg_to_mp3(source_file_path, output_file_path)
        print(f"Converted {file_name} to {output_file_name}")

print("All OGG files have been converted.")
