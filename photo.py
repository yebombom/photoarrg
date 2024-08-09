# -*- coding: utf-8 -*-
import os
import shutil
from datetime import datetime
import subprocess
from PIL import Image
from PIL.ExifTags import TAGS
from tqdm import tqdm
import concurrent.futures

# 폴더 생성 캐시를 위한 딕셔너리
folder_cache = {}

# 이미지 파일의 촬영일을 추출하는 함수
def get_image_date_taken(path):
    try:
        # HEIC 파일 처리
        if path.lower().endswith('.heic'):
            result = subprocess.run(['exiftool', '-DateTimeOriginal', '-s3', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            date_str = result.stdout.decode().strip()
            if date_str:
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        # JPG, JPEG, PNG 파일 처리
        elif path.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = Image.open(path)
            exif_data = image._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == 'DateTimeOriginal':
                        return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        else:
            # GIF 및 기타 파일의 경우 수정일을 사용
            creation_time = os.path.getmtime(path)
            return datetime.fromtimestamp(creation_time)
    except Exception as e:
        print('Error reading {0}: {1}'.format(path, e))
    return None

# 동영상 파일의 촬영일을 추출하는 함수
def get_video_date_taken(path):
    try:
        # exiftool을 사용하여 MP4, MOV 파일의 CreateDate 또는 MediaCreateDate를 추출
        result = subprocess.run(['exiftool', '-CreateDate', '-MediaCreateDate', '-s3', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        date_str = result.stdout.decode().strip().split('\n')[0]  # 첫 번째로 찾은 날짜 사용
        if date_str:
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print('Error reading {0}: {1}'.format(path, e))
    return None

# 파일을 처리하고 적절한 폴더로 이동시키는 함수
def process_file(entry, folder_path):
    file_path = entry.path
    filename = entry.name

    # 파일의 촬영일 추출
    date_taken = None
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.heic')):
        date_taken = get_image_date_taken(file_path)
    elif filename.lower().endswith(('.mp4', '.mov')):
        date_taken = get_video_date_taken(file_path)

    # 촬영일이 없으면 파일의 수정일을 사용
    if not date_taken:
        creation_time = os.path.getmtime(file_path)
        date_taken = datetime.fromtimestamp(creation_time)

    if date_taken:
        # 연도/월 폴더 생성 (예: 2023/08)
        date_folder = date_taken.strftime('%Y/%m')
        destination_folder = os.path.join(folder_path, date_folder)

        # 폴더가 이미 생성되어 있는지 캐시를 통해 확인
        if date_folder not in folder_cache:
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            folder_cache[date_folder] = True

        # 파일이 이미 이동된 경우를 확인하고, 중복 이동 방지
        if not os.path.exists(os.path.join(destination_folder, filename)):
            shutil.move(file_path, os.path.join(destination_folder, filename))
    else:
        # 촬영일 정보를 찾을 수 없는 파일을 '생성일없음' 폴더로 이동
        no_date_folder = os.path.join(folder_path, '생성일없음')
        if not os.path.exists(no_date_folder):
            os.makedirs(no_date_folder)
        shutil.move(file_path, os.path.join(no_date_folder, filename))
        print('촬영일 정보를 찾을 수 없는 파일: {0} -> 생성일없음 폴더로 이동'.format(filename))

# 전체 파일을 처리하고 정리하는 메인 함수
def organize_files_by_creation_date(folder_path):
    # 폴더 내 파일 목록을 가져오고 총 파일 수 계산
    with os.scandir(folder_path) as it:
        entries = list(it)
        total_files = len(entries)

        # 병렬 처리로 파일을 처리하고 진행 상황을 tqdm을 사용해 표시
        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(lambda entry: process_file(entry, folder_path), entries), desc="Processing files", total=total_files, unit="file"))

    print("파일 정리가 완료되었습니다.")

# 메인 실행 부분
if __name__ == '__main__':
    folder_path = '/Volumes/home/Photos'  # 실제 경로로 변경
    organize_files_by_creation_date(folder_path)