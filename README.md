# photoarrg
지정된 경로의 모든 사진, 영상의 생성일(촬영일)을 토대로 년/월 폴더로 자동 정리 해주는 스크립트입니다.

이 스크립트 사전에 설치되어야 할 것은 다음과 같습니다.
1. python 3
2. Pillow
3. exiftool
4. tqdm


가상환경 만드는 세팅하는 법
1. python3 -m venv ~/myenv
2. source ~/myenv/bin/activate

실행방법
파이썬 파일을 다운로드 한다.
photo.py 를 편집기에서 열어서 맨 하단의 경로를 정리할 사진 폴더의 위치로 수정한다.
저정한다.
맥에서 터미널을 실행한다.
파이썬 파일이 있는 폴더로 이동한다.
python photo.py 를 친 후 기다린다.
