import os
import requests
import subprocess
import urllib.parse
from mutagen.easymp4 import EasyMP4

# 输入和输出目录
input_dir = r"D:\Music\QQ_Music_Unlocked"
output_dir = "./output_m4a_files"

# FFmpeg路径
ffmpeg_path = r".\bin\ffmpeg\ffmpeg.exe"

# 检查输出目录是否存在，不存在则创建
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def get_qqmusic_data(song_name, artist_name):
    """
    从QQ音乐获取歌曲的歌词和专辑封面图片URL。
    """
    try:
        query = f"{song_name} {artist_name}"
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={encoded_query}&format=json"
        headers = {
            "Referer": "https://y.qq.com/portal/player.html"
        }
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if not data['data']['song']['list']:
            print(f"No search results for: {song_name} by {artist_name}")
            return None, None
        
        song_info = data['data']['song']['list'][0]
        song_id = song_info['songid']
        
        # 获取歌词
        lyric_url = f"https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?songmid={song_id}&format=json"
        lyric_response = requests.get(lyric_url, headers=headers)
        lyric_response.raise_for_status()
        lyrics_data = lyric_response.json()
        lyrics = lyrics_data.get('lyric', "No lyrics found")
        
        # 获取专辑图
        album_url = song_info['albummid']
        album_pic_url = f"https://y.qq.com/music/photo_new/T002R300x300M000{album_url}.jpg"
        
        return lyrics, album_pic_url
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None, None
    except KeyError as e:
        print(f"Data extraction error: {e}")
        return None, None

def download_data(lyrics, album_pic_url, song_name):
    """
    下载歌词和专辑封面图片。
    """
    try:
        # 保存歌词
        lyric_file = os.path.join(output_dir, f"{song_name}.txt")
        with open(lyric_file, "w", encoding='utf-8') as f:
            f.write(lyrics)
        
        # 下载专辑图
        album_pic_file = os.path.join(output_dir, f"{song_name}.jpg")
        img_data = requests.get(album_pic_url).content
        with open(album_pic_file, "wb") as f:
            f.write(img_data)

        return lyric_file, album_pic_file
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None, None

def add_cover_to_audio(audio_file, image_file, output_file):
    """
    将封面图片添加到音频文件中。
    """
    try:
        # 使用 PNG 文件以提高兼容性，并设置 ID3v2 版本为 3
        command = [
            ffmpeg_path, '-i', audio_file, '-i', image_file,
            '-map', '0:a', '-map', '1:v', '-c:a', 'copy', '-c:v', 'png',
            '-id3v2_version', '3', '-metadata:s:v', 'title="Album cover"', 
            '-metadata:s:v', 'comment="Cover (front)"',
            output_file
        ]
        subprocess.run(command, check=True)
        print(f"成功添加封面到 {output_file}")
    
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")

def embed_data_to_m4a(song_name, audio_file, album_pic_file):
    """
    将歌词和封面图片嵌入到 M4A 文件中。
    """
    output_file = os.path.join(output_dir, f"{song_name}_with_cover.m4a")
    add_cover_to_audio(audio_file, album_pic_file, output_file)

# 遍历输入目录中的所有 m4a 文件
for filename in os.listdir(input_dir):
    if filename.endswith(".m4a"):
        audio_file = os.path.join(input_dir, filename)
        
        try:
            # 提取音频文件中的元数据
            audio = EasyMP4(audio_file)
            song_name = audio.get('title', [None])[0]
            artist_name = audio.get('artist', [None])[0]
            
            if not song_name or not artist_name:
                print(f"Metadata not found for: {filename}")
                continue

            print(f"Processing: {filename}")
            
            # 获取 QQ 音乐数据
            lyrics, album_pic_url = get_qqmusic_data(song_name, artist_name)
            
            if lyrics and album_pic_url:
                # 下载歌词和专辑图片
                lyric_file, album_pic_file = download_data(lyrics, album_pic_url, song_name)
                
                if lyric_file and album_pic_file:
                    # 将专辑图片嵌入到 m4a 文件中
                    embed_data_to_m4a(song_name, audio_file, album_pic_file)
                else:
                    print(f"Failed to download data for: {filename}")
            else:
                print(f"Could not find data for: {filename}")
        
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
