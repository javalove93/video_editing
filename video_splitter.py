import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import logging
from datetime import datetime

def setup_logging(debug: bool = False):
    """로깅 설정을 초기화합니다."""
    level = logging.DEBUG if debug else logging.INFO
    
    # 로그 포맷 설정
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # 기본 로거 설정
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (디버그 모드일 때만)
    if debug:
        # 고정된 로그 파일명 사용
        log_file = 'debug.log'
        
        # 파일 핸들러 생성 (mode='w'로 덮어쓰기 설정)
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logging.info(f"Debug log file set to: {log_file} (will overwrite)")

def split_and_merge_video(video_path: str, timestamp_file: str, debug: bool = False) -> str:
    """
    주어진 비디오를 타임스탬프에 따라 분할하고 다시 병합합니다.
    
    Args:
        video_path (str): 원본 비디오 파일의 전체 경로
        timestamp_file (str): 타임스탬프 JSON 파일의 경로
        debug (bool): 디버그 모드 여부
    
    Returns:
        str: 병합된 비디오 파일의 경로
    """
    setup_logging(debug)
    
    # 비디오 파일 정보 확인
    probe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        duration = float(subprocess.check_output(probe_cmd).decode().strip())
        logging.info(f"Video duration: {duration:.2f} seconds")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get video duration: {e}")
        raise
    
    # 타임스탬프 파일 읽기
    with open(timestamp_file, 'r', encoding='utf-8') as f:
        timestamps = json.load(f)
    logging.info(f"Loaded {len(timestamps)} timestamps from {timestamp_file}")
    
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(dir='/tmp')
    logging.info(f"Created temporary directory: {temp_dir}")
    temp_files = []
    
    try:
        # 각 구간별로 비디오 분할
        for i, ts in enumerate(timestamps):
            start_time = ts['시작']
            end_time = ts['종료']
            
            # 시작 시간과 종료 시간이 같은 경우, 1초를 더해줍니다
            if start_time == end_time:
                # 시간 문자열을 초 단위로 변환
                minutes, seconds = map(int, end_time.split(':'))
                total_seconds = minutes * 60 + seconds + 1
                # 다시 시간 문자열로 변환
                new_minutes = total_seconds // 60
                new_seconds = total_seconds % 60
                end_time = f"{new_minutes:02d}:{new_seconds:02d}"
                logging.debug(f"Adjusted end time for segment {i}: {end_time}")
            
            output_file = os.path.join(temp_dir, f'segment_{i:03d}.mp4')
            temp_files.append(output_file)
            
            # FFmpeg 명령어 구성 - 비디오/오디오 재인코딩
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-ss', start_time,
                '-to', end_time,
                '-c:v', 'libx264', # 비디오는 H.264로 재인코딩
                '-crf', '23',      # 비디오 품질 설정 (낮을수록 좋음, 18-28 범위 일반적)
                '-preset', 'medium', # 인코딩 속도/압축률 트레이드오프
                '-c:a', 'aac',       # 오디오는 AAC로 재인코딩
                '-b:a', '128k',    # 오디오 비트레이트 설정
                # '-strict', 'experimental', # aac 인코더가 stable이면 필요 없음
                output_file
            ]
            
            logging.info(f"Processing segment {i}: {start_time} -> {end_time}")
            logging.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # FFmpeg 실행
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logging.debug(f"FFmpeg output: {result.stdout}")
            
            # 분할된 파일의 크기 확인
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                logging.debug(f"Segment {i} size: {size} bytes")
            else:
                logging.error(f"Segment {i} file was not created")
        
        # 분할된 파일들을 하나의 텍스트 파일로 나열
        concat_file = os.path.join(temp_dir, 'concat.txt')
        with open(concat_file, 'w') as f:
            for temp_file in temp_files:
                f.write(f"file '{temp_file}'\n")
        logging.info(f"Created concat file: {concat_file}")
        
        # 입력 파일의 디렉토리와 확장자 가져오기
        input_path = Path(video_path)
        output_dir = input_path.parent
        output_filename = f"{input_path.stem}_edited{input_path.suffix}"
        output_path = str(output_dir / output_filename)
        
        # 분할된 파일들을 병합 - 오디오 스트림 처리 개선
        merge_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', 'copy',  # 비디오는 그대로 복사
            '-c:a', 'copy',   # 오디오도 그대로 복사 (분할 시 AAC로 인코딩됨)
            # '-strict', 'experimental', # 복사 시에는 필요 없을 수 있음
            output_path
        ]
        
        logging.info(f"Merging segments into: {output_path}")
        logging.debug(f"Merge command: {' '.join(merge_cmd)}")
        
        # FFmpeg 병합 실행 및 로그 출력
        result = subprocess.run(merge_cmd, check=True, capture_output=True, text=True)
        logging.debug(f"Merge stdout: {result.stdout}") # 디버그 로그에는 계속 남김
        logging.debug(f"Merge stderr: {result.stderr}") # 디버그 로그에는 계속 남김
        
        # 디버그 모드와 상관없이 콘솔에 병합 로그 출력
        print("--- FFmpeg Merge Output ---")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("--- End FFmpeg Merge Output ---")
        
        # 최종 파일 크기 확인
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            logging.info(f"Final video size: {size} bytes")
        else:
            logging.error("Final video file was not created")
        
        if not debug:
            # 디버그 모드가 아닌 경우에만 임시 파일 삭제
            shutil.rmtree(temp_dir)
            logging.info("Cleaned up temporary files")
        else:
            logging.info(f"Debug mode: temporary files preserved in {temp_dir}")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during video processing: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Split and merge video based on timestamps')
    parser.add_argument('video_path', help='Path to the input video file')
    parser.add_argument('timestamp_file', help='Path to the timestamp JSON file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    try:
        output_path = split_and_merge_video(args.video_path, args.timestamp_file, args.debug)
        print(f"Successfully created merged video at: {output_path}")
    except Exception as e:
        print(f"Failed to process video: {str(e)}")
        sys.exit(1) 