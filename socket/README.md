# LIVECON IoT 센서 시스템

> 고급 암호화 기술을 적용한 실시간 IoT 센서 데이터 수집 및 모니터링 시스템

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Security](https://img.shields.io/badge/Security-ECDHE%20%7C%20Ed25519%20%7C%20ChaCha20-green.svg)](https://github.com)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

## 📋 목차

- [개요](#-개요)
- [주요 기능](#-주요-기능)
- [보안 기능](#-보안-기능)
- [시스템 요구사항](#-시스템-요구사항)
- [빠른 시작](#-빠른-시작)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [문서](#-문서)
- [프로젝트 구조](#-프로젝트-구조)
- [트러블슈팅](#-트러블슈팅)
- [라이선스](#-라이선스)

## 🌟 개요

LIVECON IoT 시스템은 IoT 센서로부터 실시간으로 데이터를 수집하고 모니터링하는 엔터프라이즈급 솔루션입니다. 최신 암호화 기술을 적용하여 데이터 보안을 보장하며, 자동 알람 및 이상 탐지 기능을 제공합니다.

### 센서 데이터 타입
- 🌡️ **온도** (Temperature)
- 💧 **용존산소** (Dissolved Oxygen)
- 🌊 **수온** (Water Temperature)
- 📍 **위치 정보** (Geohash 10자리, 약 60cm 정밀도)

## ✨ 주요 기능

### 실시간 모니터링
- 다중 센서 동시 모니터링
- 실시간 데이터 수집 및 저장
- 웹 기반 대시보드 (선택사항)

### 자동 알람 시스템
- 임계값 기반 알람
- 센서 오프라인 감지
- 데이터 이상 탐지 (급격한 변화, 고착 데이터)
- 센서 측정 범위 초과 감지
- 실시간 알람 로그

### 데이터 관리
- MySQL 데이터베이스 저장
- 원본 패킷 보관 (디버깅용)
- 센서 메타데이터 관리
- 알람 이력 추적

## 🔒 보안 기능

### 암호화 프로토콜
| 기술 | 용도 | 상세 |
|------|------|------|
| **ECDHE (X25519)** | 키 교환 | Perfect Forward Secrecy 보장 |
| **Ed25519** | 디지털 서명 | 서버 인증 및 공개키 피닝 |
| **ChaCha20-Poly1305** | 대칭 암호화 | AEAD (인증 암호화) |
| **HKDF-SHA256** | 키 유도 | 솔트 기반 강력한 키 생성 |

### 보안 특징
✅ **Perfect Forward Secrecy (PFS)** - 세션 키가 노출되어도 이전 통신 보호
✅ **공개키 피닝** - MITM 공격 방지
✅ **재생 공격 방지** - 논스 카운터 기반 중복 패킷 거부
✅ **무결성 보장** - Poly1305 MAC으로 데이터 변조 탐지
✅ **컨텍스트 바인딩** - AAD로 장치 ID 검증

## 💻 시스템 요구사항

### 서버
- **OS**: Windows 10+ / Linux (Ubuntu 20.04+, CentOS 7+)
- **Python**: 3.8 이상
- **데이터베이스**: MySQL 5.7+ 또는 MariaDB 10.3+
- **메모리**: 최소 2GB RAM
- **디스크**: 최소 10GB 여유 공간

### 클라이언트
- **OS**: Windows 10+ / Linux
- **Python**: 3.8 이상 (개발 시) / 실행 파일 사용 시 불필요
- **메모리**: 최소 512MB RAM

### 네트워크
- **포트**: TCP 12351 (기본값, 변경 가능)
- **방화벽**: 서버 포트 개방 필요

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/your-org/livecon-iot.git
cd livecon-iot
```

### 2. 데이터베이스 설정
```bash
# MySQL/MariaDB 접속
mysql -u root -p

# 데이터베이스 생성
CREATE DATABASE sensor_db CHARACTER SET utf8mb4;

# 테이블 생성 스크립트 실행
source database/schema.sql
```

### 3. 서버 설정 및 실행
```bash
cd server_package

# 의존성 설치
pip install -r requirements.txt

# 설정 파일 수정
# config.json 파일에서 데이터베이스 접속 정보 수정

# 서버 실행
python server.py
```

### 4. 서버 공개키 추출
```bash
cd server_package
python extract_server_pubkey.py

# 출력된 공개키를 클라이언트 config.json에 복사
```

### 5. 클라이언트 설정 및 실행
```bash
cd client_package

# 의존성 설치
pip install -r requirements.txt

# 설정 파일 수정
# config.json 파일에서 서버 주소, 포트, 공개키 설정

# 클라이언트 실행
python client.py
```

## 📦 설치 방법

### 개발 환경 설치

#### 서버
```bash
cd server_package
pip install -r requirements.txt
```

**requirements.txt**:
```
cryptography>=41.0.0
PyMySQL>=1.1.0
```

#### 클라이언트
```bash
cd client_package
pip install -r requirements.txt
```

**requirements.txt**:
```
cryptography>=41.0.0
```

### 실행 파일 빌드

#### Windows
```bash
# 클라이언트 빌드
cd client_package
pyinstaller --clean --noconfirm IoT_Sensor_Client.spec

# 서버 빌드
cd server_package
pyinstaller --clean --noconfirm IoT_Sensor_Server.spec
```

#### Linux
```bash
# 클라이언트 빌드
cd client_package
pyinstaller --clean --noconfirm IoT_Sensor_Client.spec

# 서버 빌드
cd server_package
pyinstaller --clean --noconfirm IoT_Sensor_Server.spec
```

빌드된 실행 파일은 각각 `dist/` 디렉토리에 생성됩니다.

## 📖 사용 방법

### 서버 설정 파일 (`server_package/config.json`)

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 12351
    },
    "database": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "your_password",
        "database": "sensor_db"
    }
}
```

### 클라이언트 설정 파일 (`client_package/config.json`)

```json
{
    "server": {
        "address": "192.168.1.100",
        "port": 12351,
        "ed25519_pubkey_hex": "a1b2c3d4e5f6...(64 hex characters)"
    },
    "client": {
        "device_id": "device001",
        "send_interval": 10
    }
}
```

**중요**: `ed25519_pubkey_hex`는 서버에서 `extract_server_pubkey.py`를 실행하여 얻은 값을 입력하세요.

### 센서 정보 등록

```sql
-- sensor_info 테이블에 센서 정보 등록
INSERT INTO sensor_info (device_id, sensor_type_id, sensor_name, alarm_min, alarm_max, sensor_min, sensor_max, resolution)
VALUES
('device001', 0, 'Temperature Sensor', 15.0, 35.0, -40.0, 125.0, 0.1),
('device001', 1, 'Water Temperature Sensor', 15.0, 35.0, 0.0, 100.0, 0.1),
('device001', 2, 'Dissolved Oxygen Sensor', 5.0, 15.0, 0.0, 60.0, 0.01);
```

### 실행

#### 개발 모드
```bash
# 서버
cd server_package
python server.py

# 클라이언트
cd client_package
python client.py
```

#### 실행 파일 모드
```bash
# Windows 서버
cd server_package\dist
IoT_Sensor_Server.exe

# Windows 클라이언트
cd client_package\dist
IoT_Sensor_Client.exe

# Linux 서버
cd server_package/dist
./IoT_Sensor_Server

# Linux 클라이언트
cd client_package/dist
./IoT_Sensor_Client
```

## 📚 문서

상세한 기술 문서는 다음 파일을 참조하세요:

- **[CODE_DOCUMENTATION.md](CODE_DOCUMENTATION.md)** - 전체 코드 설명 문서 (3,247줄)
  - 시스템 아키텍처
  - 모든 모듈 상세 설명
  - 보안 프로토콜 설명
  - 데이터베이스 스키마
  - 빌드 및 배포 가이드
  - 트러블슈팅

- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - 개발 가이드
  - 개발 환경 설정
  - 코딩 규칙
  - 보안 가이드라인

## 📁 프로젝트 구조

```
livecon-iot/
├── client_package/              # 클라이언트 패키지
│   ├── client.py               # 메인 클라이언트 프로그램
│   ├── config.json             # 클라이언트 설정 파일
│   ├── IoT_Sensor_Client.spec  # PyInstaller 빌드 설정
│   ├── requirements.txt        # Python 의존성
│   └── node_module/            # 클라이언트 모듈
│       ├── ecdhe_crypto.py     # ECDHE 암호화
│       ├── generate_packet.py  # 센서 패킷 생성
│       ├── geohash_encode.py   # Geohash 인코딩
│       └── security_utils.py   # 보안 유틸리티
│
├── server_package/              # 서버 패키지
│   ├── server.py               # 메인 서버 프로그램
│   ├── config.json             # 서버 설정 파일
│   ├── IoT_Sensor_Server.spec  # PyInstaller 빌드 설정
│   ├── requirements.txt        # Python 의존성
│   ├── extract_server_pubkey.py # 서버 공개키 추출 유틸리티
│   └── server_module/          # 서버 모듈
│       ├── crypto_manager.py       # 암호화 세션 관리
│       ├── key_exchange_handler.py # 키 교환 핸들러
│       ├── client_manager.py       # 클라이언트 관리
│       ├── packet_parser.py        # 패킷 파서
│       ├── server_core.py          # 서버 소켓 관리
│       ├── connection_manager.py   # 연결 상태 관리
│       ├── alarm_manager.py        # 알람 관리
│       ├── sensor_monitor.py       # 센서 모니터링
│       ├── database_manager.py     # 데이터베이스 관리
│       └── security_utils.py       # 보안 유틸리티
│
├── database/                    # 데이터베이스 스크립트
│   └── schema.sql              # 데이터베이스 스키마
│
├── CODE_DOCUMENTATION.md        # 전체 코드 설명 문서
├── DEVELOPMENT_GUIDE.md         # 개발 가이드
├── README.md                    # 이 파일
└── LICENSE                      # 라이선스 파일
```

## 🔧 트러블슈팅

### 연결 실패

**증상**: 클라이언트가 서버에 연결할 수 없음

**해결 방법**:
1. 서버 IP 주소 및 포트 확인
2. 방화벽 설정 확인
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="LIVECON Server" dir=in action=allow protocol=TCP localport=12351

   # Linux (iptables)
   sudo iptables -A INPUT -p tcp --dport 12351 -j ACCEPT
   ```
3. 서버가 실행 중인지 확인
   ```bash
   # Windows
   netstat -an | findstr 12351

   # Linux
   netstat -an | grep 12351
   ```

### 키 교환 실패

**증상**: "Server signature verification failed" 또는 "MITM attack detected"

**해결 방법**:
1. 서버 공개키를 다시 추출
   ```bash
   cd server_package
   python extract_server_pubkey.py
   ```
2. 출력된 공개키를 클라이언트 `config.json`의 `ed25519_pubkey_hex`에 정확히 복사
3. 클라이언트 재시작

### 재생 공격 감지

**증상**: "Replay attack detected"

**해결 방법**:
1. 클라이언트 재시작 (새로운 ECDHE 세션 수립)
2. 네트워크에서 패킷 중복 전송이 발생하는지 확인

### 데이터베이스 연결 실패

**증상**: "Database connection error"

**해결 방법**:
1. MySQL/MariaDB 서비스가 실행 중인지 확인
   ```bash
   # Windows
   net start MySQL

   # Linux
   sudo systemctl status mysql
   ```
2. 서버 `config.json`의 데이터베이스 접속 정보 확인
3. 데이터베이스 사용자 권한 확인
   ```sql
   GRANT ALL PRIVILEGES ON sensor_db.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

### 센서 데이터가 저장되지 않음

**증상**: 데이터베이스에 센서 데이터가 저장되지 않음

**해결 방법**:
1. `sensor_info` 테이블에 센서 정보가 등록되어 있는지 확인
   ```sql
   SELECT * FROM sensor_info WHERE device_id = 'device001';
   ```
2. 등록되지 않았다면 센서 정보 등록 ([사용 방법](#-사용-방법) 참조)

## 🔐 보안 권장사항

1. **공개키 피닝 활성화**: 클라이언트 `config.json`에 서버 공개키를 반드시 설정하세요.
2. **강력한 데이터베이스 비밀번호**: 데이터베이스 사용자 비밀번호를 강력하게 설정하세요.
3. **방화벽 설정**: 서버 포트를 신뢰할 수 있는 IP에서만 접근할 수 있도록 제한하세요.
4. **정기적인 업데이트**: cryptography 라이브러리를 최신 버전으로 유지하세요.
5. **로그 모니터링**: 알람 로그를 정기적으로 확인하세요.

## 🎯 향후 계획

- [ ] 웹 기반 대시보드 개발
- [ ] 다양한 센서 타입 지원 확장
- [ ] 클러스터링 지원 (서버 고가용성)
- [ ] REST API 제공
- [ ] 모바일 앱 개발

## 🤝 기여

이 프로젝트는 현재 비공개 프로젝트입니다. 기여에 대한 문의는 프로젝트 관리자에게 연락하세요.

## 📞 연락처

- **프로젝트 관리자**: LIVECON IoT Team
- **이메일**: contact@livecon.io
- **이슈 트래커**: [GitHub Issues](https://github.com/your-org/livecon-iot/issues)

## 📄 라이선스

이 프로젝트는 독점 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

**© 2025 LIVECON IoT Team. All rights reserved.**

**Made with ❤️ and 🔒 by Claude Code**
