# IoT Sensor Data Collection System / IoT 센서 데이터 수집 시스템

## English

### Overview
This is a secure IoT sensor data collection system supporting RSA-2048 encryption, multi-client connections, and network-based public key distribution. The system enables secure communication between IoT sensors and a central server with automatic data storage in MySQL database.

### Key Features

#### Security
- **RSA-2048 Encryption**: All sensor data encrypted with RSA-2048 and PKCS1_OAEP padding
- **Network Public Key Distribution**: Clients automatically obtain public keys from server
- **Sensor Authentication**: Server validates registered sensor IDs
- **Packet Integrity**: Checksum verification for all data packets

#### Network & Deployment
- **Multi-Client Support**: Server handles multiple concurrent client connections
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Independent Deployment**: Completely standalone executable files
- **No External Dependencies**: All modules embedded in executables
- **Network Configuration**: Easy server IP configuration via JSON files

#### Data Processing
- **32-byte Sensor Packets**: Structured data format containing sensor measurements
- **Geohash Location Encoding**: Efficient GPS coordinate storage
- **MySQL Database Integration**: Automatic sensor data storage
- **Real-time Processing**: Real-time sensor data monitoring and logging

### System Architecture

```
[Client 1] ──┐
[Client 2] ──┼─→ [Server] ──→ [MySQL Database]
[Client N] ──┘
```

### Data Flow
1. Server generates RSA key pair on startup
2. Client requests public key from server (network-based)
3. Client generates 32-byte sensor packets (temperature, oxygen, water temp, GPS, timestamp)
4. Client encrypts packet with server's public key
5. Client transmits encrypted data via TCP
6. Server decrypts and validates packets
7. Server stores data in MySQL database

### Packet Structure (32 bytes)
```
STX(1) + ID(2) + LEN(3) + TEMP(2) + O2(2) + WATER_TEMP(2) + 
GEOHASH(10) + TIMESTAMP(6) + CHECKSUM(2) + ETX(1)
```

### Installation and Usage

#### Server Package
**Location**: `server_package/`

**Files**:
- `IoT_Sensor_Server.exe` - Standalone server executable (8.82 MB)
- `README.txt` - Detailed server usage instructions
- `build_independent.py` - Development build script

**Server Execution**:
1. Run `IoT_Sensor_Server.exe`
2. Server automatically generates RSA keys (private.pem, public.pem)
3. Starts listening for client connections on port 12351
4. Ready for client connections

**Requirements**:
- MySQL database setup (for data storage)
- Port 12351 available (automatically resolves if in use)

#### Client Package
**Location**: `client_package/`

**Files**:
- `IoT_Sensor_Client.exe` - Standalone client executable (8.31 MB)
- `config.json` - Client configuration file
- `README.txt` - Detailed client usage instructions
- `build_independent.py` - Development build script

**Client Configuration** (`config.json`):
```json
{
    "server": {
        "address": "192.168.1.100",  // Server IP address
        "port": 12351               // Server port
    },
    "client": {
        "sensor_id": "SENSOR_001",  // Unique sensor identifier
        "send_interval": 10,        // Data transmission interval (seconds)
        "public_key_path": "public.pem"
    }
}
```

**Client Execution**:
1. Configure server IP address in `config.json`
2. Set unique `sensor_id` for each client
3. Run `IoT_Sensor_Client.exe`
4. Client automatically obtains public key from server
5. Starts transmitting encrypted sensor data every N seconds

### Multi-Client Deployment

#### Server Deployment
1. Copy `server_package/IoT_Sensor_Server.exe` to server machine
2. Execute the file
3. Ready for multiple client connections

#### Client Deployment
For each sensor location:
1. Copy `client_package/` folder to client machine
2. Edit `config.json`:
   - Set server IP address
   - Set unique sensor ID (e.g., SENSOR_A01, SENSOR_B01, etc.)
   - Adjust transmission interval if needed
3. Run `IoT_Sensor_Client.exe`
4. Each client operates independently

### Database Configuration

The system requires a MySQL database with the following schema:

#### Database: `livecon_db`

**Table: `sensor_info`**
- Stores registered sensor IDs
- Used for sensor authentication

**Table: `sensor_result`**
- Stores all sensor measurements
- Includes location data and timestamps

### Network Requirements

#### Firewall Configuration
- **Server**: Allow incoming connections on port 12351
- **Client**: Allow outgoing connections to server IP port 12351

#### Network Topology
- Clients and server can connect via same LAN or internet
- Each client needs TCP connection to server
- No special routing or port forwarding required for basic LAN setup

### Development and Build

#### Prerequisites
- Python 3.7+
- PyInstaller
- Required packages: pycryptodome, pymysql

#### Build Process
```bash
# Server
cd server_package
python build_independent.py

# Client  
cd client_package
python build_independent.py
```

### Source Code Structure
```
server_package/
├── server.py              # Main server application
├── server_module/         # Server utility modules
│   ├── rsa_utils.py      # RSA encryption/decryption
│   ├── parsing.py        # Packet parsing and validation
│   ├── sql_utils.py      # Database operations
│   ├── checksum.py       # Packet integrity verification
│   └── geohash_decode.py # Location data decoding

client_package/
├── client.py              # Main client application
├── node_module/          # Client utility modules
│   ├── rsa_utils.py      # RSA encryption
│   ├── generate_packet.py # Sensor data packet generation
│   └── geohash_encode.py # Location data encoding
```

### Performance

#### Server Capacity
- Supports 100+ concurrent client connections
- Multi-threaded client handling
- Efficient packet processing and database operations

#### Network Usage
- Per sensor packet: 32 bytes (raw) → 256 bytes (encrypted)
- Default transmission interval: 10 seconds per client
- Bandwidth usage: ~25 bytes/second per client

### Security Considerations

#### Encryption
- RSA-2048 provides strong security for sensor data
- Each packet is individually encrypted
- Public key distribution via secure channel

#### Authentication
- Server validates all sensor IDs against database
- Unauthorized sensors automatically blocked
- Connection logging for audit purposes

#### Best Practices
- Keep server private key secure (private.pem)
- Regular key rotation if required
- Monitor connection logs for suspicious activity
- Use secure network connections when possible

---

## 한국어

### 개요
RSA-2048 암호화, 다중 클라이언트 지원, 네트워크 기반 공개키 배포를 지원하는 안전한 IoT 센서 데이터 수집 시스템입니다. 이 시스템은 IoT 센서와 중앙 서버 간의 안전한 통신을 가능하게 하며 MySQL 데이터베이스에 자동 데이터 저장 기능을 제공합니다.

### 핵심 기능

#### 보안
- **RSA-2048 암호화**: 모든 센서 데이터를 RSA-2048과 PKCS1_OAEP 패딩으로 암호화
- **네트워크 공개키 배포**: 클라이언트가 서버에서 자동으로 공개키 획득
- **센서 인증**: 서버에서 등록된 센서 ID 검증
- **패킷 무결성**: 모든 데이터 패킷의 체크섬 검증

#### 네트워크 및 배포
- **다중 클라이언트 지원**: 서버가 여러 클라이언트의 동시 연결 처리
- **크로스 플랫폼**: Windows, Linux, macOS에서 동작
- **독립 배포**: 완전히 독립적인 실행 파일
- **외부 의존성 없음**: 모든 모듈이 실행 파일에 내장
- **네트워크 설정**: JSON 파일을 통한 간편한 서버 IP 설정

#### 데이터 처리
- **32바이트 센서 패킷**: 센서 측정값을 포함한 구조화된 데이터 형식
- **지오해시 위치 인코딩**: GPS 좌표의 효율적인 저장
- **MySQL 데이터베이스 연동**: 자동 센서 데이터 저장
- **실시간 처리**: 실시간 센서 데이터 모니터링 및 로깅

### 시스템 아키텍처

```
[클라이언트 1] ──┐
[클라이언트 2] ──┼─→ [서버] ──→ [MySQL 데이터베이스]
[클라이언트 N] ──┘
```

### 데이터 플로우
1. 서버가 시작 시 RSA 키 쌍 생성
2. 클라이언트가 서버에 공개키 요청 (네트워크 기반)
3. 클라이언트가 32바이트 센서 패킷 생성 (온도, 산소, 수온, GPS, 타임스탬프)
4. 클라이언트가 서버의 공개키로 패킷 암호화
5. 클라이언트가 TCP를 통해 암호화된 데이터 전송
6. 서버가 패킷 복호화 및 검증
7. 서버가 MySQL 데이터베이스에 데이터 저장

### 패킷 구조 (32바이트)
```
STX(1) + ID(2) + LEN(3) + TEMP(2) + O2(2) + WATER_TEMP(2) + 
GEOHASH(10) + TIMESTAMP(6) + CHECKSUM(2) + ETX(1)
```

### 설치 및 사용법

#### 서버 패키지
**위치**: `server_package/`

**파일들**:
- `IoT_Sensor_Server.exe` - 독립 실행 서버 파일 (8.82 MB)
- `README.txt` - 상세한 서버 사용법
- `build_independent.py` - 개발용 빌드 스크립트

**서버 실행**:
1. `IoT_Sensor_Server.exe` 실행
2. 서버가 자동으로 RSA 키 생성 (private.pem, public.pem)
3. 포트 12351에서 클라이언트 연결 대기 시작
4. 클라이언트 연결 준비 완료

**요구사항**:
- MySQL 데이터베이스 설정 (데이터 저장용)
- 포트 12351 사용 가능 (사용 중이면 자동으로 해결)

#### 클라이언트 패키지
**위치**: `client_package/`

**파일들**:
- `IoT_Sensor_Client.exe` - 독립 실행 클라이언트 파일 (8.31 MB)
- `config.json` - 클라이언트 설정 파일
- `README.txt` - 상세한 클라이언트 사용법
- `build_independent.py` - 개발용 빌드 스크립트

**클라이언트 설정** (`config.json`):
```json
{
    "server": {
        "address": "192.168.1.100",  // 서버 IP 주소
        "port": 12351               // 서버 포트
    },
    "client": {
        "sensor_id": "SENSOR_001",  // 고유 센서 식별자
        "send_interval": 10,        // 데이터 전송 간격 (초)
        "public_key_path": "public.pem"
    }
}
```

**클라이언트 실행**:
1. `config.json`에서 서버 IP 주소 설정
2. 각 클라이언트마다 고유한 `sensor_id` 설정
3. `IoT_Sensor_Client.exe` 실행
4. 클라이언트가 서버에서 자동으로 공개키 획득
5. N초마다 암호화된 센서 데이터 전송 시작

### 다중 클라이언트 배포

#### 서버 배포
1. `server_package/IoT_Sensor_Server.exe`를 서버 기기에 복사
2. 실행 파일 실행
3. 다중 클라이언트 연결 준비 완료

#### 클라이언트 배포
각 센서 위치별로:
1. `client_package/` 폴더를 클라이언트 기기에 복사
2. `config.json` 편집:
   - 서버 IP 주소 설정
   - 고유한 센서 ID 설정 (예: SENSOR_A01, SENSOR_B01 등)
   - 필요시 전송 간격 조정
3. `IoT_Sensor_Client.exe` 실행
4. 각 클라이언트가 독립적으로 동작

### 데이터베이스 설정

시스템은 다음 스키마를 가진 MySQL 데이터베이스가 필요합니다:

#### 데이터베이스: `livecon_db`

**테이블: `sensor_info`**
- 등록된 센서 ID 저장
- 센서 인증에 사용

**테이블: `sensor_result`**
- 모든 센서 측정값 저장
- 위치 데이터와 타임스탬프 포함

### 네트워크 요구사항

#### 방화벽 설정
- **서버**: 포트 12351에서 들어오는 연결 허용
- **클라이언트**: 서버 IP의 포트 12351로 나가는 연결 허용

#### 네트워크 토폴로지
- 클라이언트와 서버는 동일 LAN 또는 인터넷을 통해 연결 가능
- 각 클라이언트는 서버와 TCP 연결 필요
- 기본 LAN 설정에서는 특별한 라우팅이나 포트 포워딩 불필요

### 개발 및 빌드

#### 전제조건
- Python 3.7+
- PyInstaller
- 필요 패키지: pycryptodome, pymysql

#### 빌드 과정
```bash
# 서버
cd server_package
python build_independent.py

# 클라이언트  
cd client_package
python build_independent.py
```

### 소스 코드 구조
```
server_package/
├── server.py              # 메인 서버 애플리케이션
├── server_module/         # 서버 유틸리티 모듈
│   ├── rsa_utils.py      # RSA 암호화/복호화
│   ├── parsing.py        # 패킷 파싱 및 검증
│   ├── sql_utils.py      # 데이터베이스 연산
│   ├── checksum.py       # 패킷 무결성 검증
│   └── geohash_decode.py # 위치 데이터 디코딩

client_package/
├── client.py              # 메인 클라이언트 애플리케이션
├── node_module/          # 클라이언트 유틸리티 모듈
│   ├── rsa_utils.py      # RSA 암호화
│   ├── generate_packet.py # 센서 데이터 패킷 생성
│   └── geohash_encode.py # 위치 데이터 인코딩
```

### 성능

#### 서버 용량
- 100개 이상의 동시 클라이언트 연결 지원
- 멀티스레드 클라이언트 처리
- 효율적인 패킷 처리 및 데이터베이스 연산

#### 네트워크 사용량
- 센서 패킷당: 32바이트 (원본) → 256바이트 (암호화)
- 기본 전송 간격: 클라이언트당 10초
- 대역폭 사용량: 클라이언트당 약 25바이트/초

### 보안 고려사항

#### 암호화
- RSA-2048가 센서 데이터에 강력한 보안 제공
- 각 패킷이 개별적으로 암호화됨
- 보안 채널을 통한 공개키 배포

#### 인증
- 서버가 데이터베이스와 비교하여 모든 센서 ID 검증
- 미등록 센서 자동 차단
- 감사 목적의 연결 로깅

#### 모범 사례
- 서버 개인키 보안 유지 (private.pem)
- 필요시 정기적인 암호화 키 교체
- 비정상적인 활동에 대한 연결 로그 모니터링
- 가능한 경우 보안 네트워크 연결 사용

## System Overview

This system provides enterprise-grade security features for IoT sensor data collection with:

### 🔒 Security Features
- RSA-2048 end-to-end encryption
- Automatic public key distribution
- Sensor ID-based authentication
- Packet integrity verification

### 🌐 Network Features  
- Multi-client concurrent connections
- Automatic port conflict resolution
- Cross-platform compatibility
- Network-based configuration

### 📦 Deployment Features
- Completely standalone executables
- No external dependencies
- Simple JSON configuration
- Independent client packages

### 💾 Data Features
- Structured 32-byte packets
- Real-time MySQL storage
- Geohash location encoding
- Comprehensive logging

### 🔧 Operational Features
- Automatic server cleanup
- Real-time monitoring
- Multi-threaded processing
- Error handling and recovery

This system provides all necessary features for building a production IoT sensor network.