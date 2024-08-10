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
        if path.lower().endswith('.heic'):
            result = subprocess.run(['exiftool', '-DateTimeOriginal', '-s3', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            date_str = result.stdout.decode().strip()
            if date_str:
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        elif path.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = Image.open(path)
            exif_data = image._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == 'DateTimeOriginal':
                        return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        return None  # 날짜 파싱 실패 시 None 반환
    except Exception as e:
        print(f'Error reading {path}: {e}')
    return None

# 동영상 파일의 촬영일을 추출하는 함수
def get_video_date_taken(path):
    try:
        result = subprocess.run(['exiftool', '-CreateDate', '-MediaCreateDate', '-s3', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        date_str = result.stdout.decode().strip().split('\n')[0]
        
        # 잘못된 날짜 형식 처리
        if not date_str or date_str == '0000:00:00 00:00:00':
            return None

        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except (ValueError, Exception) as e:
        print(f'Error reading {path}: {e}')
    return None

# 파일을 적절한 폴더로 이동시키는 함수
def move_file_to_correct_folder(file_path, root_folder, filename, date_taken):
    # 연도/월 폴더 생성 (예: 2010/01)
    year_folder = date_taken.strftime('%Y')
    month_folder = date_taken.strftime('%m')
    destination_folder = os.path.join(root_folder, year_folder, month_folder)

    # 폴더가 이미 생성되어 있는지 캐시를 통해 확인
    if (year_folder, month_folder) not in folder_cache:
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        folder_cache[(year_folder, month_folder)] = True

    # 파일을 올바른 폴더로 이동
    if not os.path.exists(os.path.join(destination_folder, filename)):
        shutil.move(file_path, os.path.join(destination_folder, filename))

# 이미지 파일을 점검하고 재배치하는 함수
def check_and_relocate_images(import_folder, root_folder):
    for current_path, dirs, files in os.walk(import_folder):
        for filename in files:
            file_path = os.path.join(current_path, filename)

            # 파일의 촬영일 추출
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.heic')):
                date_taken = get_image_date_taken(file_path)

                if date_taken:
                    # 예상 폴더로 이동
                    print(f"Moving {filename} to {os.path.join(root_folder, date_taken.strftime('%Y'), date_taken.strftime('%m'))}")
                    move_file_to_correct_folder(file_path, root_folder, filename, date_taken)
                else:
                    # 촬영일 정보를 찾을 수 없는 파일을 '생성일없음' 폴더로 이동
                    no_date_folder = os.path.join(root_folder, '생성일없음')
                    if not os.path.exists(no_date_folder):
                        os.makedirs(no_date_folder)
                    shutil.move(file_path, os.path.join(no_date_folder, filename))
                    print(f'촬영일 정보를 찾을 수 없는 파일: {filename} -> 생성일없음 폴더로 이동')

# 동영상 파일을 점검하고 재배치하는 함수
def check_and_relocate_videos(import_folder, root_folder):
    for current_path, dirs, files in os.walk(import_folder):
        for filename in files:
            file_path = os.path.join(current_path, filename)

            # 파일의 촬영일 추출
            if filename.lower().endswith(('.mp4', '.mov')):
                date_taken = get_video_date_taken(file_path)

                if date_taken:
                    # 예상 폴더로 이동
                    print(f"Moving {filename} to {os.path.join(root_folder, date_taken.strftime('%Y'), date_taken.strftime('%m'))}")
                    move_file_to_correct_folder(file_path, root_folder, filename, date_taken)
                else:
                    # 촬영일 정보를 찾을 수 없는 파일을 '생성일없음' 폴더로 이동
                    no_date_folder = os.path.join(root_folder, '생성일없음')
                    if not os.path.exists(no_date_folder):
                        os.makedirs(no_date_folder)
                    shutil.move(file_path, os.path.join(no_date_folder, filename))
                    print(f'촬영일 정보를 찾을 수 없는 파일: {filename} -> 생성일없음 폴더로 이동')

# 전체 파일을 점검하고 재배치하는 메인 함수
def organize_existing_files(import_folder, root_folder):
    print("잘못된 위치에 있는 파일을 점검 중입니다... (이미지 파일)")
    check_and_relocate_images(import_folder, root_folder)
    print("이미지 파일 정리가 완료되었습니다.")

    print("잘못된 위치에 있는 파일을 점검 중입니다... (동영상 파일)")
    check_and_relocate_videos(import_folder, root_folder)
    print("동영상 파일 정리가 완료되었습니다.")

# 메인 실행 부분
if __name__ == '__main__':
    import_folder = '/Volumes/home/Photos/import'  # 스캔할 경로
    root_folder = '/Volumes/home/Photos'  # 정리할 대상 경로
    organize_existing_files(import_folder, root_folder)
