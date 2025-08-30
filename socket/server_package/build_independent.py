#!/usr/bin/env python3
"""
Independent Server Package Build Script
Creates fully independent executable with all modules embedded
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def create_simple_icon():
    """Create a simple shell-style icon if not exists"""
    current_dir = Path(__file__).parent
    icon_path = current_dir / "server_icon.ico"
    
    if not icon_path.exists():
        try:
            from PIL import Image, ImageDraw
            print("Creating server shell icon...")
            
            # Create simple 32x32 blue shell icon
            img = Image.new('RGBA', (32, 32), (30, 30, 80, 255))
            draw = ImageDraw.Draw(img)
            
            # Draw border
            draw.rectangle([1, 1, 30, 30], outline=(255, 255, 255, 255), width=1)
            
            # Draw "SRV" text
            draw.text((6, 12), "SRV", fill=(255, 255, 255, 255))
            
            # Draw terminal prompt
            draw.text((3, 3), ">", fill=(255, 255, 255, 255))
            
            img.save(icon_path)
            print(f"Server icon created: {icon_path}")
            
        except ImportError:
            print("PIL not available, creating without icon")
        except Exception as e:
            print(f"Could not create icon: {e}")

def build_independent_server():
    """Build independent server executable"""
    current_dir = Path(__file__).parent
    
    print("Building independent server package...")
    print("=" * 50)
    
    # Try to create icon if it doesn't exist
    create_simple_icon()
    
    # 이전 빌드 파일 정리
    print("Cleaning up previous build files...")
    for cleanup_dir in ['build', 'dist', '__pycache__']:
        cleanup_path = current_dir / cleanup_dir
        if cleanup_path.exists():
            shutil.rmtree(cleanup_path)
            print(f"   {cleanup_dir} removed")
    
    # .spec 파일 삭제
    spec_file = current_dir / 'server.spec'
    if spec_file.exists():
        spec_file.unlink()
        print("   server.spec removed")
    
    try:
        print("\nBuilding with PyInstaller...")
        
        # 아이콘 파일 체크
        icon_path = current_dir / "server_icon.ico"
        
        # PyInstaller 명령 구성 (모든 모듈 내장)
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",                    # 단일 실행 파일
            "--console",                    # 콘솔 창 표시
            "--name=IoT_Sensor_Server",     # 실행 파일 이름
            "--distpath=.",                 # 현재 디렉토리에 출력
            "--workpath=build",             # 임시 작업 디렉토리
            "--specpath=.",                 # .spec 파일 위치
        ]
        
        # 아이콘 파일이 있으면 추가
        if icon_path.exists():
            cmd.append(f"--icon={icon_path}")
            print(f"Using icon: {icon_path}")
        else:
            print("No icon file found, building without icon")
        
        # 나머지 옵션들 추가
        cmd.extend([
            # 현재 디렉토리의 모든 모듈을 내장
            "--paths=.",                    # 현재 디렉토리를 경로에 추가
            
            # 서버 모듈들 명시적으로 포함 (최신 구조 반영)
            "--hidden-import=server_module",
            "--hidden-import=server_module.console_manager",
            "--hidden-import=server_module.console_interface", 
            "--hidden-import=server_module.database_manager",
            "--hidden-import=server_module.crypto_manager",
            "--hidden-import=server_module.process_manager",
            "--hidden-import=server_module.server_core",
            "--hidden-import=server_module.client_manager",
            "--hidden-import=server_module.connection_manager",
            "--hidden-import=server_module.alarm_manager",
            "--hidden-import=server_module.sensor_monitor",
            "--hidden-import=server_module.packet_parser",
            
            # 외부 라이브러리
            "--hidden-import=pymysql",
            "--hidden-import=Crypto.PublicKey.RSA",
            "--hidden-import=Crypto.Cipher.PKCS1_OAEP",
            
            # 전체 server_module 디렉토리 포함
            "--add-data=server_module;server_module",
            
            "server.py"                     # 메인 스크립트
        ])
        
        print("Build command:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=current_dir)
        
        if result.returncode == 0:
            print("Build successful!")
            
            # 생성된 파일 확인
            exe_path = current_dir / "IoT_Sensor_Server.exe"
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"Generated file: {exe_path}")
                print(f"File size: {file_size:.2f} MB")
                
                print("\nIndependent server package build completed!")
                print(f"Usage: {exe_path}")
                print("\nFeatures:")
                print("- All modules embedded in executable")
                print("- No external folder dependencies") 
                print("- Complete independent execution as single file")
                return True
            else:
                print(".exe file was not generated.")
                return False
                
        else:
            print("Build failed!")
            print("Error output:", result.stderr)
            return False
            
    except Exception as e:
        print(f"Error during build: {e}")
        return False

def main():
    print("Independent Server Package Build Tool")
    
    # 의존성 확인
    try:
        import PyInstaller
        print(f"PyInstaller 버전: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller is not installed.")
        print("Installation: pip install pyinstaller")
        sys.exit(1)
    
    # 빌드 실행
    if build_independent_server():
        print("\nBuild successful! You can now deploy IoT_Sensor_Server.exe to other devices.")
    else:
        print("\nBuild failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()