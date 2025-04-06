# Video Splitter based on Timestamps

이 스크립트는 제공된 타임스탬프 JSON 파일을 기반으로 비디오 파일을 분할하고 병합합니다.

## 기능

- 지정된 시작 및 종료 시간에 따라 비디오를 여러 세그먼트로 분할합니다.
- 분할된 세그먼트를 다시 하나의 비디오 파일로 병합합니다.
- 원본 비디오와 동일한 디렉토리에 `[원본 파일명]_edited.[확장자]` 형식으로 최종 비디오를 저장합니다.
- 디버그 모드를 지원하여 임시 파일을 보존하고 상세 로그를 `debug.log` 파일에 저장합니다.

## 요구사항

- Python 3.6 이상
- FFmpeg: 시스템에 설치되어 있고 PATH 환경 변수에 등록되어 있어야 합니다.

## FFmpeg 설치

FFmpeg가 설치되어 있지 않다면, 사용 중인 운영체제에 맞게 설치해야 합니다.

- **Windows:** 
    - [FFmpeg 공식 다운로드 페이지](https://ffmpeg.org/download.html#build-windows)
    - [설치 가이드 (BtbN)](https://github.com/BtbN/FFmpeg-Builds/wiki/ FFmpeg-Installation-Guide-for-Windows)
    - [설치 가이드 (Wikihow)](https://www.wikihow.com/Install-FFmpeg-on-Windows)
- **macOS:**
    - Homebrew 사용 (권장):
      ```bash
      brew install ffmpeg
      ```
    - [FFmpeg 공식 다운로드 페이지](https://ffmpeg.org/download.html#build-mac)
- **Linux:**
    - Debian/Ubuntu 기반:
      ```bash
      sudo apt update
      sudo apt install ffmpeg
      ```
    - Fedora 기반:
      ```bash
      sudo dnf install ffmpeg
      ```
    - [FFmpeg 공식 다운로드 페이지](https://ffmpeg.org/download.html#build-linux)

설치 후 터미널에서 `ffmpeg -version` 명령어를 실행하여 설치가 제대로 되었는지 확인할 수 있습니다.

## 사용법

스크립트는 명령줄 인터페이스를 통해 실행됩니다.

```bash
python video_splitter.py <video_path> <timestamp_file> [--debug]
```

**인자 설명:**

- `<video_path>`: 처리할 원본 비디오 파일의 전체 경로입니다. (필수)
- `<timestamp_file>`: 비디오 분할 지점 정보가 담긴 JSON 파일의 경로입니다. (필수) 
  JSON 형식 예시:
  ```json
  [
      {"시작": "HH:MM:SS", "종료": "HH:MM:SS"},
      ...
  ]
  ```
- `--debug`: (선택 사항) 디버그 모드를 활성화합니다. 활성화 시 상세 로그가 콘솔과 `debug.log` 파일에 출력되고, 임시 파일이 `/tmp` 디렉토리에 보존됩니다.

**예시:**

```bash
# 일반 실행
python video_splitter.py /path/to/my_video.mp4 /path/to/timestamps.json

# 디버그 모드로 실행
python video_splitter.py "/path/with spaces/input video.mov" "timestamps.json" --debug
```

## 예시 출력 (Example Output)

다음은 스크립트를 실행하여 생성된 샘플 영상입니다. (파일은 저장소 루트에 위치해야 합니다):
[축구 경기 영상2_edited.mp4](축구%20경기%20영상2_edited.mp4)

## 주의사항

- 비디오 재인코딩 과정은 시스템 성능에 따라 시간이 소요될 수 있습니다.
- 타임스탬프 JSON 파일의 시간 형식은 `HH:MM:SS` 또는 `MM:SS` 여야 합니다. (현재 스크립트는 `MM:SS` 형식만 처리합니다. 필요시 수정 가능)
- 임시 파일은 `/tmp` 디렉토리에 생성됩니다. 디버그 모드가 아닐 경우 작업 완료 후 자동으로 삭제됩니다. 