#!/usr/bin/env python3
"""
독립 클라이언트 패키지 빌드 스크립트
모든 모듈을 내장한 완전 독립 실행 파일 생성
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def build_independent_client():
    """독립 클라이언트 exe 빌드"""
    current_dir = Path(__file__).parent
    
    print("독립 클라이언트 패키지 빌드 시작")
    print("=" * 50)
    
    # 이전 빌드 파일 정리
    print("이전 빌드 파일 정리 중...")
    for cleanup_dir in ['build', 'dist', '__pycache__']:
        cleanup_path = current_dir / cleanup_dir
        if cleanup_path.exists():
            shutil.rmtree(cleanup_path)
            print(f"   {cleanup_dir} 삭제됨")
    
    # .spec 파일 삭제
    spec_file = current_dir / 'client.spec'
    if spec_file.exists():
        spec_file.unlink()
        print("   client.spec 삭제됨")
    
    try:
        print("\nPyInstaller로 독립 빌드 중...")
        
        # PyInstaller 명령 구성 (모든 모듈 내장)
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",                    # 단일 실행 파일
            "--console",                    # 콘솔 창 표시
            "--name=IoT_Sensor_Client",     # 실행 파일 이름
            "--distpath=.",                 # 현재 디렉토리에 출력
            "--workpath=build",             # 임시 작업 디렉토리
            "--specpath=.",                 # .spec 파일 위치
            
            # 현재 디렉토리의 모든 모듈을 내장
            "--paths=.",                    # 현재 디렉토리를 경로에 추가
            
            # 클라이언트 모듈들 명시적으로 포함
            "--hidden-import=node_module",
            "--hidden-import=node_module.rsa_utils",
            "--hidden-import=node_module.generate_packet",
            "--hidden-import=node_module.geohash_encode",
            
            # 외부 라이브러리
            "--hidden-import=Crypto.PublicKey.RSA",
            "--hidden-import=Crypto.Cipher.PKCS1_OAEP",
            
            # 전체 node_module 디렉토리 포함
            "--add-data=node_module;node_module",
            
            "client.py"                     # 메인 스크립트
        ]
        
        print("실행 명령:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=current_dir)
        
        if result.returncode == 0:
            print("빌드 성공!")
            
            # 생성된 파일 확인
            exe_path = current_dir / "IoT_Sensor_Client.exe"
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"생성된 파일: {exe_path}")
                print(f"파일 크기: {file_size:.2f} MB")
                
                print("\n독립 클라이언트 패키지 빌드 완료!")
                print(f"실행 방법: {exe_path}")
                print("\n특징:")
                print("- 모든 모듈이 실행 파일에 내장됨")
                print("- 외부 폴더 의존성 없음")
                print("- config.json만 함께 배포하면 완전 독립 실행 가능")
                return True
            else:
                print(".exe 파일이 생성되지 않았습니다.")
                return False
                
        else:
            print("빌드 실패!")
            print("오류 출력:", result.stderr)
            return False
            
    except Exception as e:
        print(f"빌드 중 오류 발생: {e}")
        return False

def main():
    print("독립 클라이언트 패키지 빌드 도구")
    
    # 의존성 확인
    try:
        import PyInstaller
        print(f"PyInstaller 버전: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller가 설치되지 않았습니다.")
        print("설치 방법: pip install pyinstaller")
        sys.exit(1)
    
    # 빌드 실행
    if build_independent_client():
        print("\n빌드 성공! 이제 IoT_Sensor_Client.exe를 다른 기기에 배포할 수 있습니다.")
    else:
        print("\n빌드에 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()