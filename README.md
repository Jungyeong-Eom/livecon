# IoT Sensor Data Collection System / IoT 센서 데이터 수집 시스템

## English

### Overview
This system is an encrypted IoT sensor data collection system that enables secure communication between IoT sensors and a central server. It uses RSA encryption for secure data transmission and MySQL for data persistence.

### Key Features
- **Encrypted Communication**: All sensor data transmission uses RSA-2048 encryption
- **Data Integrity**: Packet integrity verification using checksums
- **Sensor Authentication**: Validation through registered sensor IDs
- **Input Validation**: Comprehensive validation for all sensor values (temperature ranges, timestamp verification)
- **Location Encoding**: GPS coordinates encoded in geohash format
- **Real-time Processing**: 10-second interval sensor data collection

### Architecture Components

**Server Side (`server/` and `server_module/`):**
- `server.py` - Main TCP server handling encrypted sensor data
- `server_app.py` - PyQt5 GUI application for server
- `parsing.py` - 32-byte sensor packet parsing with validation
- `sql_utils.py` - MySQL database operations for sensor data storage
- `rsa_utils.py` - RSA key generation, encryption/decryption utilities
- `checksum.py` - Packet integrity verification
- `geohash_decode.py` - Geohash location data decoding

**Client Side (`node/` and `node_module/`):**
- `client.py` - Sensor simulator that generates and transmits encrypted data
- `generate_packet.py` - 32-byte sensor data packet generation
- `geohash_encode.py` - GPS coordinate encoding to geohash format
- `rsa_utils.py` - Client-side RSA encryption utilities

### Data Flow
1. Server generates RSA key pair on startup
2. Client loads public key and generates sensor packets every 10 seconds
3. Packet contents: sensor ID, temperature, dissolved oxygen, water temperature, GPS location (geohash), timestamp, checksum
4. Client encrypts packet with RSA and transmits via TCP to server
5. Server decrypts, validates, parses packet and stores in MySQL database
6. Server validates sensor ID against registered sensors in database

### Database Schema
The system requires a MySQL database (`livecon_db`) with the following tables:
- `sensor_info` - Contains registered sensor IDs
- `sensor_result` - Stores sensor measurements with location and timestamps

### Installation and Execution

#### Running with Python

**Server Installation and Execution:**
```bash
# Install dependencies
python server/install.py

# Run server
python server/server.py
```

**Client Installation and Execution (Sensor Simulator):**
```bash
# Install dependencies
python node/install.py

# Run client
python node/client.py
```

#### Running as .exe Files

**Complete Build (Recommended):**
```bash
python build_all.py
```
After build completion, run the `.exe` files in the `release/` folder

**Individual Build:**
```bash
# Build server only
python server/build_server.py

# Build client only
python node/build_client.py
```

**Execution Order:**
1. Run `IoT_Sensor_Server.exe` (server)
2. Run `IoT_Sensor_Client.exe` (client)

### File Structure
```
server/
├── server.py           # Main TCP server (port 12346)
├── server_app.py       # GUI application
└── private.pem         # RSA private key

node/
├── client.py           # Sensor client simulator
└── public.pem          # RSA public key

server_module/          # Server utilities
├── parsing.py          # 32-byte packet parser
├── sql_utils.py        # Database operations
├── rsa_utils.py        # Encryption utilities
├── checksum.py         # Packet verification
└── geohash_decode.py   # Location decoding

node_module/            # Client utilities
├── generate_packet.py  # Packet generation
├── geohash_encode.py   # Location encoding
└── rsa_utils.py        # Client encryption
```

---

## 한국어

### 개요
이 시스템은 IoT 센서와 중앙 서버 간의 암호화된 통신을 통한 센서 데이터 수집 시스템입니다. 안전한 데이터 전송을 위해 RSA 암호화를 사용하고 데이터 지속성을 위해 MySQL을 사용합니다.

### 핵심 기능
- **암호화된 통신**: 모든 센서 데이터 전송에 RSA-2048 암호화 사용
- **데이터 무결성**: 체크섬을 사용한 패킷 무결성 검증
- **센서 인증**: 등록된 센서 ID 검증을 통한 센서 인증
- **입력 검증**: 모든 센서 값에 대한 종합적인 검증 (온도 범위, 타임스탬프 검증)
- **위치 인코딩**: 지오해시 형식으로 GPS 좌표 인코딩
- **실시간 처리**: 10초 간격으로 센서 데이터 수집

### 아키텍처 구성 요소

**서버 측 (`server/` 및 `server_module/`):**
- `server.py` - 암호화된 센서 데이터를 처리하는 메인 TCP 서버
- `server_app.py` - 서버용 PyQt5 GUI 애플리케이션
- `parsing.py` - 검증을 포함한 32바이트 센서 패킷 파싱
- `sql_utils.py` - 센서 데이터 저장을 위한 MySQL 데이터베이스 연산
- `rsa_utils.py` - RSA 키 생성, 암호화/복호화 유틸리티
- `checksum.py` - 패킷 무결성 검증
- `geohash_decode.py` - 지오해시 위치 데이터 디코딩

**클라이언트 측 (`node/` 및 `node_module/`):**
- `client.py` - 암호화된 데이터를 생성하고 전송하는 센서 시뮬레이터
- `generate_packet.py` - 32바이트 센서 데이터 패킷 생성
- `geohash_encode.py` - GPS 좌표를 지오해시 형식으로 인코딩
- `rsa_utils.py` - 클라이언트 측 RSA 암호화 유틸리티

### 데이터 플로우
1. 서버가 시작 시 RSA 키 쌍을 생성
2. 클라이언트가 공개 키를 로드하고 10초마다 센서 패킷을 생성
3. 패킷 내용: 센서 ID, 온도, 용존산소, 수온, GPS 위치(지오해시), 타임스탬프, 체크섬
4. 클라이언트가 RSA로 패킷을 암호화하여 TCP를 통해 서버로 전송
5. 서버가 패킷을 복호화, 검증, 파싱하여 MySQL 데이터베이스에 저장
6. 서버가 데이터베이스에 등록된 센서에 대해 센서 ID를 검증

### 데이터베이스 스키마
시스템은 다음 테이블을 가진 MySQL 데이터베이스(`livecon_db`)를 필요로 합니다:
- `sensor_info` - 등록된 센서 ID들을 포함
- `sensor_result` - 위치와 타임스탬프가 포함된 센서 측정값들을 저장

### 설치 및 실행

#### Python으로 실행하기

**서버 설치 및 실행:**
```bash
# 의존성 설치
python server/install.py

# 서버 실행
python server/server.py
```

**클라이언트 설치 및 실행 (센서 시뮬레이터):**
```bash
# 의존성 설치
python node/install.py

# 클라이언트 실행
python node/client.py
```

#### .exe 파일로 실행하기

**전체 빌드 (권장):**
```bash
python build_all.py
```
빌드 완료 후 `release/` 폴더의 `.exe` 파일들을 실행

**개별 빌드:**
```bash
# 서버만 빌드
python server/build_server.py

# 클라이언트만 빌드  
python node/build_client.py
```

**실행 순서:**
1. `IoT_Sensor_Server.exe` 실행 (서버)
2. `IoT_Sensor_Client.exe` 실행 (클라이언트)

### 파일 구조
```
server/
├── server.py           # 메인 TCP 서버 (포트 12346)
├── server_app.py       # GUI 애플리케이션
└── private.pem         # RSA 개인 키

node/
├── client.py           # 센서 클라이언트 시뮬레이터
└── public.pem          # RSA 공개 키

server_module/          # 서버 유틸리티
├── parsing.py          # 32바이트 패킷 파서
├── sql_utils.py        # 데이터베이스 연산
├── rsa_utils.py        # 암호화 유틸리티
├── checksum.py         # 패킷 검증
└── geohash_decode.py   # 위치 디코딩

node_module/            # 클라이언트 유틸리티
├── generate_packet.py  # 패킷 생성
├── geohash_encode.py   # 위치 인코딩
└── rsa_utils.py        # 클라이언트 암호화
```