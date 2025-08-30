# LIVECON - 활어 수송 컨테이너 모니터링 시스템

![License](https://img.shields.io/badge/license-Private-red)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Security](https://img.shields.io/badge/security-ECDHE%20%2B%20PFS-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)

**ECDHE 암호화 기반 활어 수송 컨테이너 실시간 모니터링 시스템**

## 시스템 개요

LIVECON(Live Container)은 활어 수송 컨테이너의 실시간 추적을 위한 전문 IoT 모니터링 시스템입니다. 수온, 용존산소 농도, 컨테이너 위치를 지속적으로 모니터링하여 활어 운송 중 최적 조건을 보장하며, Perfect Forward Secrecy를 지원하는 엔터프라이즈급 암호화 보안을 특징으로 합니다.

### 주요 기능

- **활어 운송 모니터링**: 실시간 수질 및 환경 추적
- **수질 관리**: 용존산소, 수온, pH 모니터링
- **GPS 추적**: 실시간 컨테이너 위치 및 운송 경로 모니터링
- **위험 상황 알림**: 위험한 조건에 대한 즉각적인 알림
- **보안 통신**: ECDHE + Ed25519 + ChaCha20-Poly1305 암호화
- **완전 전방 보안**: 과거 통신 내용의 보안 보장
- **데이터 로깅**: 완전한 운송 이력 및 조건 기록
- **휴대 가능한 배포**: 운송 차량용 독립 실행 파일

## 아키텍처

```
┌─────────────────────────┐    ECDHE + ChaCha20    ┌──────────────────────┐
│     활어 운송 탱크      │◄──────────────────────►│    LIVECON 서버      │
│                         │    Perfect Forward     │                      │
│  수온                   │       Secrecy          │ • 컨테이너 모니터    │
│  용존산소               │                        │ • 알림 관리자        │
│  수질                   │                        │ • 경로 추적          │
│  GPS 위치               │                        │ • 어류 안전 확인     │
│  실시간 데이터          │                        │ • 응급 대응          │
└─────────────────────────┘                        └──────────────────────┘
                                                              │
                                                   ┌──────────▼──────────┐
                                                   │    MySQL 데이터베이스│
                                                   │                     │
                                                   │ • 운송 기록         │
                                                   │ • 수질 로그         │
                                                   │ • 어류 건강 데이터  │
                                                   │ • 경로 이력         │
                                                   │ • 비상 알림         │
                                                   └─────────────────────┘
```

## 보안 기능

### 암호화 구현

| 구성 요소 | 알고리즘 | 목적 |
|-----------|-----------|---------|
| **키 교환** | X25519 ECDHE | 임시 키 협상 |
| **인증** | Ed25519 | 서버 신원 확인 |
| **암호화** | ChaCha20-Poly1305 | AEAD 패킷 암호화 |
| **전방 보안** | 세션 격리 | 과거 통신 보호 |

### 보안 아키텍처

```
어류 탱크 센서 → ECDHE 키 교환 → ChaCha20-Poly1305 → 운송 관제센터
                        ↓
                 Ed25519 인증
                        ↓
                완전 전방 보안
```

## 데이터베이스 스키마

### 1. device_info 테이블
**목적**: 탱크 장치 인증 및 등록
- `device_id` (VARCHAR) - 어류 탱크 장치 식별자 (예: "device001")
- 추가 인증 및 장치 메타데이터 필드

### 2. sensor_info 테이블  
**목적**: 어류 탱크 센서 등록 및 알람 임계값 구성
- `sensor_id` (VARCHAR) - 고유 센서 식별자
- `device_id` (VARCHAR) - device_info 테이블 참조
- `sensor_type_id` (INT) - 센서 유형: 0=온도센서, 1=수온센서, 2=용존산소센서
- `alarm_min` (DECIMAL) - 알람 발생 하한값
- `alarm_max` (DECIMAL) - 알람 발생 상한값
- `sensor_min` (DECIMAL) - 센서 물리적 최소 측정 범위
- `sensor_max` (DECIMAL) - 센서 물리적 최대 측정 범위
- `resolution` (DECIMAL) - 센서 측정 해상도/정밀도
- `sensing_period` (INT) - 데이터 수집 간격 (초)
- `transfer_period` (INT) - 데이터 전송 간격 (초)

### 3. sensor_result 테이블
**목적**: 시계열 수질 측정값 및 센서 데이터 저장
- `result_id` (VARCHAR(20)) - 고유 결과 식별자
- `device_id` (VARCHAR) - 패킷의 장치 식별자
- `sensor_id` (VARCHAR) - sensor_info 테이블의 실제 센서 ID
- `value_type_id` (INT) - 값 유형: 1=온도, 2=용존산소, 3=수온
- `sensor_value` (DECIMAL) - 측정된 센서 값
- `alarm_state` (INT) - 알람 상태 (0=정상, >0=알람_유형_ID)
- `error_state` (INT) - 오류 상태 (0=정상, 1=오류 발생)
- `location` (VARCHAR) - GPS 좌표 "위도,경도" 형식
- `measured_at` (DATETIME) - 측정 타임스탬프

### 4. alarm_log 테이블
**목적**: 어류 안전 알림 및 위험 조건 위반 기록
- `alarm_id` (VARCHAR(20)) - 고유 알람 식별자
- `alarmed_at` (DATETIME) - 알람 발생 타임스탬프
- `sensor_id` (VARCHAR) - 연관된 센서 식별자
- `alarm_type_id` (INT) - 알람 유형 코드
- `alarm_log` (TEXT) - 상세 알람 메시지

### 5. raw_packet_log 테이블
**목적**: 디버깅 및 감사를 위한 운송 모니터링 패킷 저장
- `packet_id` (VARCHAR(20)) - 고유 패킷 식별자
- `device_id` (VARCHAR) - 장치 식별자 (nullable)
- `received_at` (DATETIME) - 패킷 수신 타임스탬프
- `packet_log` (TEXT) - 원시 패킷의 16진수 표현
- `parse_success` (TINYINT) - 파싱 성공 플래그 (1=성공, 0=실패)

## 32바이트 패킷 구조

| 바이트 위치 | 필드 | 크기 | 데이터 타입 | 설명 | 검증 규칙 |
|-------------|------|------|-------------|------|----------|
| 0 | STX | 1바이트 | UINT8 | 시작 마커 | 0x24 ('$')이어야 함 |
| 1-2 | 장치 ID | 2바이트 | UINT16 (Big Endian) | 장치 숫자 ID | "device{ID:03d}" 형식으로 변환 |
| 3-5 | 길이 | 3바이트 | UINT24 (Big Endian) | 패킷 길이 | 32여야 함 |
| 6-7 | 온도 | 2바이트 | UINT16 (Big Endian) | 대기 온도 × 10 | 범위: -400~1250 (-40.0°C~125.0°C) |
| 8-9 | 용존산소 | 2바이트 | UINT16 (Big Endian) | DO × 100 | 범위: 0~6000 (0.0~60.0 mg/L) |
| 10-11 | 수온 | 2바이트 | UINT16 (Big Endian) | 수온 × 10 | 범위: 0~1000 (0.0°C~100.0°C) |
| 12-21 | GPS 위치 | 10바이트 | ASCII | 지오해시 문자열 | Base32 인코딩 (정밀도=10) |
| 22-23 | 년도 | 2바이트 | UINT16 (Big Endian) | 년도 | 범위: 2000~2099 |
| 24 | 월 | 1바이트 | UINT8 | 월 | 범위: 1~12 |
| 25 | 일 | 1바이트 | UINT8 | 일 | 범위: 1~31 |
| 26 | 시 | 1바이트 | UINT8 | 시 | 범위: 0~23 |
| 27 | 분 | 1바이트 | UINT8 | 분 | 범위: 0~59 |
| 28 | 초 | 1바이트 | UINT8 | 초 | 범위: 0~59 |
| 29-30 | 체크섬 | 2바이트 | UINT16 (Big Endian) | CRC16 체크섬 | 1-28바이트 합, 0xFFFF로 마스킹 |
| 31 | ETX | 1바이트 | UINT8 | 종료 마커 | 0x5C ('\')이어야 함 |

## 활어 운송 안전 임계값

### 환경 한계
- **대기 온도**: -10°C~40°C (운송 환경)
- **수온**: 5°C~30°C (어종별 의존)
- **용존산소**: 4-15 mg/L (어류 생존에 중요)
- **온도 안정성**: 최대 ±3°C 변동

### 응급 대응 트리거
- **위험 용존산소 알림**: < 4.0 mg/L (즉시 대응 필요)
- **온도 충격**: > ±10°C 급변
- **센서 오프라인**: > 5분간 데이터 없음
- **GPS 신호 손실**: 위치 추적 중단

## 사용 사례

- **활어 운송**: 양식업 운송 작업 중 실시간 모니터링
- **양식업**: 상업적 어류 양식 및 유통 물류
- **어시장 공급망**: 양식장에서 시장까지 품질 유지
- **응급 대응**: 장비 고장이나 위험 조건에 대한 즉각적인 알림
- **규정 준수**: 식품 안전 및 운송 규정을 위한 자동 로깅
- **연구 응용**: 어류 운송 최적화 및 스트레스 감소 연구

---

# LIVECON - Live Fish Transport Container Monitoring System

![License](https://img.shields.io/badge/license-Private-red)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Security](https://img.shields.io/badge/security-ECDHE%20%2B%20PFS-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)

**Real-time monitoring system for live fish transport containers with enterprise-grade ECDHE encryption**

## System Overview

LIVECON (Live Container) is a specialized IoT monitoring system designed for real-time tracking of live fish transport containers. The system ensures optimal conditions for fish transport by continuously monitoring water temperature, dissolved oxygen levels, and container location, featuring enterprise-grade cryptographic security with Perfect Forward Secrecy.

### Key Features

- **Live Fish Transport Monitoring**: Real-time water quality and environmental tracking
- **Water Quality Control**: Dissolved oxygen, temperature, and pH monitoring
- **GPS Tracking**: Real-time container location and transport route monitoring
- **Critical Alerts**: Immediate notifications for dangerous conditions
- **Secure Communication**: ECDHE + Ed25519 + ChaCha20-Poly1305 encryption
- **Perfect Forward Secrecy**: Past communications remain secure
- **Data Logging**: Complete transport history and condition records
- **Portable Deployment**: Standalone executables for transport vehicles

## Architecture

```
┌─────────────────────────┐    ECDHE + ChaCha20    ┌──────────────────────┐
│  Fish Transport Tanks   │◄──────────────────────►│    LIVECON Server    │
│                         │    Perfect Forward     │                      │
│  Water Temperature      │       Secrecy          │ • Container Monitor  │
│  Dissolved Oxygen       │                        │ • Alert Manager      │
│  Water Quality          │                        │ • Route Tracking     │
│  GPS Location           │                        │ • Fish Safety Check  │
│  Real-time Data         │                        │ • Emergency Response │
└─────────────────────────┘                        └──────────────────────┘
                                                              │
                                                   ┌──────────▼──────────┐
                                                   │    MySQL Database   │
                                                   │                     │
                                                   │ • Transport Records │
                                                   │ • Water Quality Log │
                                                   │ • Fish Health Data  │
                                                   │ • Route History     │
                                                   │ • Emergency Alerts  │
                                                   └─────────────────────┘
```

## Security Features

### Cryptographic Implementation

| Component | Algorithm | Purpose |
|-----------|-----------|---------|
| **Key Exchange** | X25519 ECDHE | Ephemeral key agreement |
| **Authentication** | Ed25519 | Server identity verification |
| **Encryption** | ChaCha20-Poly1305 | AEAD packet encryption |
| **Forward Secrecy** | Session isolation | Past communication protection |

### Security Architecture

```
Fish Tank Sensor → ECDHE Key Exchange → ChaCha20-Poly1305 → Transport Control Center
                          ↓
                   Ed25519 Authentication
                          ↓
                  Perfect Forward Secrecy
```

## Database Schema

### 1. device_info Table
**Purpose**: Tank device authentication and registration
- `device_id` (VARCHAR) - Fish tank device identifier (format: "device001")
- Additional authentication and device metadata fields

### 2. sensor_info Table  
**Purpose**: Fish tank sensor registry and configuration with alarm thresholds
- `sensor_id` (VARCHAR) - Unique sensor identifier
- `device_id` (VARCHAR) - Reference to device_info table
- `sensor_type_id` (INT) - Sensor type: 0=temp_sensor, 1=wtr_temp_sensor, 2=do_sensor
- `alarm_min` (DECIMAL) - Lower threshold for alarm triggering
- `alarm_max` (DECIMAL) - Upper threshold for alarm triggering  
- `sensor_min` (DECIMAL) - Physical sensor minimum measurement range
- `sensor_max` (DECIMAL) - Physical sensor maximum measurement range
- `resolution` (DECIMAL) - Sensor measurement resolution/precision
- `sensing_period` (INT) - Data collection interval (seconds)
- `transfer_period` (INT) - Data transmission interval (seconds)

### 3. sensor_result Table
**Purpose**: Time-series water quality measurements and sensor data storage
- `result_id` (VARCHAR(20))` - Unique result identifier
- `device_id` (VARCHAR) - Device identifier from packet
- `sensor_id` (VARCHAR) - Actual sensor ID from sensor_info table
- `value_type_id` (INT) - Value type: 1=temp, 2=do, 3=wtr_temp
- `sensor_value` (DECIMAL) - Measured sensor value
- `alarm_state` (INT) - Alarm status (0=normal, >0=alarm_type_id)
- `error_state` (INT) - Error status (0=normal, 1=error occurred)
- `location` (VARCHAR) - GPS coordinates in "latitude,longitude" format  
- `measured_at` (DATETIME) - Measurement timestamp

### 4. alarm_log Table
**Purpose**: Fish safety alerts and critical condition violations
- `alarm_id` (VARCHAR(20)) - Unique alarm identifier
- `alarmed_at` (DATETIME) - Alarm occurrence timestamp
- `sensor_id` (VARCHAR) - Associated sensor identifier
- `alarm_type_id` (INT) - Alarm type code
- `alarm_log` (TEXT) - Detailed alarm message

### 5. raw_packet_log Table
**Purpose**: Transport monitoring packet storage for debugging and audit
- `packet_id` (VARCHAR(20)) - Unique packet identifier
- `device_id` (VARCHAR) - Device identifier (nullable)
- `received_at` (DATETIME) - Packet reception timestamp
- `packet_log` (TEXT) - Hexadecimal representation of raw packet
- `parse_success` (TINYINT) - Parsing success flag (1=success, 0=failed)

## 32-Byte Packet Structure

| Byte Position | Field | Size | Data Type | Description | Validation Rules |
|---------------|-------|------|-----------|-------------|------------------|
| 0 | STX | 1 byte | UINT8 | Start marker | Must be 0x24 ('$') |
| 1-2 | Device ID | 2 bytes | UINT16 (Big Endian) | Device numeric ID | Converted to "device{ID:03d}" format |
| 3-5 | Length | 3 bytes | UINT24 (Big Endian) | Packet length | Should be 32 |
| 6-7 | Temperature | 2 bytes | UINT16 (Big Endian) | Air temp × 10 | Range: -400 to 1250 (-40.0°C to 125.0°C) |
| 8-9 | Dissolved O₂ | 2 bytes | UINT16 (Big Endian) | DO × 100 | Range: 0 to 6000 (0.0 to 60.0 mg/L) |
| 10-11 | Water Temp | 2 bytes | UINT16 (Big Endian) | Water temp × 10 | Range: 0 to 1000 (0.0°C to 100.0°C) |
| 12-21 | GPS Location | 10 bytes | ASCII | Geohash string | Base32 encoded (precision=10) |
| 22-23 | Year | 2 bytes | UINT16 (Big Endian) | Year | Range: 2000 to 2099 |
| 24 | Month | 1 byte | UINT8 | Month | Range: 1 to 12 |
| 25 | Day | 1 byte | UINT8 | Day | Range: 1 to 31 |
| 26 | Hour | 1 byte | UINT8 | Hour | Range: 0 to 23 |
| 27 | Minute | 1 byte | UINT8 | Minute | Range: 0 to 59 |
| 28 | Second | 1 byte | UINT8 | Second | Range: 0 to 59 |
| 29-30 | Checksum | 2 bytes | UINT16 (Big Endian) | CRC16 checksum | Sum of bytes 1-28, masked with 0xFFFF |
| 31 | ETX | 1 byte | UINT8 | End marker | Must be 0x5C ('\') |

## Fish Transport Safety Thresholds

### Environmental Limits
- **Ambient Temperature**: -10°C to 40°C (transport environment)
- **Water Temperature**: 5°C to 30°C (species-dependent)
- **Dissolved Oxygen**: 4-15 mg/L (critical for fish survival)
- **Temperature Stability**: ±3°C variation maximum

### Emergency Response Triggers
- **Critical DO Alert**: < 4.0 mg/L (immediate response required)
- **Temperature Shock**: > ±10°C sudden change
- **Sensor Offline**: > 5 minutes without data
- **GPS Signal Loss**: Location tracking interruption

## Project Structure

```
socket/
├── server_package/           # Server Components
│   ├── server.py            # Main server entry point
│   ├── requirements.txt     # Server dependencies
│   ├── build_independent.py # Server build script
│   └── server_module/       # Core server modules
│       ├── server_core.py   # TCP server implementation
│       ├── crypto_manager.py# ECDHE cryptographic operations
│       ├── client_manager.py# Client connection lifecycle
│       ├── console_interface.py # Admin console interface
│       ├── database_manager.py  # MySQL operations
│       ├── packet_parser.py     # 32-byte packet parsing
│       ├── alarm_manager.py     # Threshold monitoring
│       └── sensor_monitor.py    # Sensor health monitoring
├── client_package/          # Tank Sensor Components  
│   ├── client.py           # Fish tank sensor client
│   ├── config.json         # Tank sensor configuration
│   ├── requirements.txt    # Client dependencies
│   ├── build_independent.py# Client build script
│   └── node_module/        # Sensor modules
│       ├── ecdhe_crypto.py # Client-side cryptography
│       ├── generate_packet.py # Water quality packet creation
│       └── geohash_encode.py  # GPS coordinate encoding
└── test_icon_creation.py   # Icon generation test
```

## Quick Start

### Prerequisites

- **Python 3.8+**
- **MySQL Server** (for server component)
- **Network connectivity** between client and server

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd socket
   ```

2. **Server Setup**
   ```bash
   cd server_package
   pip install -r requirements.txt
   
   # Configure MySQL database (see Configuration section)
   python server.py
   ```

3. **Tank Sensor Setup**
   ```bash
   cd client_package
   pip install -r requirements.txt
   
   # Edit config.json with server details and tank configuration
   python client.py
   ```

### Build Standalone Executables

**Server Build:**
```bash
cd server_package
python build_independent.py
# Generates: IoT_Sensor_Server.exe
```

**Tank Sensor Build:**
```bash
cd client_package  
python build_independent.py
# Generates: IoT_Sensor_Client.exe (Fish Tank Sensor)
```

## Configuration

### Server Configuration

Configure MySQL database connection in your environment or `server.py`:

```python
# Database settings
DB_HOST = "localhost"
DB_USER = "your_username" 
DB_PASSWORD = "your_password"
DB_NAME = "sensor_db"
```

### Fish Tank Sensor Configuration (`client_package/config.json`)

```json
{
    "server_host": "127.0.0.1",
    "server_port": 9999,
    "device_id": "tank001",
    "interval": 5,
    "sensor_config": {
        "water_temp_range": [10, 25],
        "do_range": [6, 12],
        "ambient_temp_range": [5, 35]
    },
    "fish_transport": {
        "species": "live_fish",
        "container_capacity": "500L",
        "critical_do_level": 4.0,
        "max_temp_variation": 3.0
    }
}
```

## Console Interface

The server provides a rich interactive console with comprehensive administrative commands:

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `status` | Transport monitoring status | `status` |
| `sessions` | Tank sensor session management | `sessions --active --details` |
| `clients` | Connected tank information | `clients tank001 --stats` |
| `logs` | Fish transport logs | `logs --follow --grep "tank001"` |
| `packets` | Water quality data inspection | `packets tank001 --follow --parsed` |
| `stats` | Tank performance metrics | `stats --client tank001 --latency` |
| `crypto` | Transport security information | `crypto` |

### Monitoring Features

- **Fish Safety Metrics**: Water quality parameters, response times, emergency alerts
- **Transport Tracking**: Route monitoring, tank location updates, delivery status
- **Critical Alerts**: Dissolved oxygen warnings, temperature fluctuations, equipment failures
- **Performance Analysis**: Data transmission rates, sensor response times, connection stability

## Use Cases

- **Live Fish Transport**: Real-time monitoring during aquaculture transport operations
- **Aquaculture Industry**: Commercial fish farming and distribution logistics
- **Fish Market Supply Chain**: Maintaining quality from farm to market
- **Emergency Response**: Immediate alerts for equipment failures or critical conditions
- **Regulatory Compliance**: Automated logging for food safety and transport regulations
- **Research Applications**: Fish transport optimization and stress reduction studies

## System Requirements

### Control Center Requirements
- **OS**: Windows 10+ or Linux
- **RAM**: 1GB+ recommended (multi-tank monitoring)
- **Storage**: 500MB+ for application, 10GB+ for transport database
- **Network**: Reliable internet connection for GPS tracking
- **Database**: MySQL 5.7+ or MariaDB 10.2+

### Fish Tank Sensor Requirements
- **OS**: Windows 10+ or Linux (embedded systems compatible)
- **RAM**: 256MB minimum
- **Storage**: 50MB for sensor application
- **Network**: 4G/WiFi connectivity for real-time data transmission
- **Power**: 12V DC compatible (vehicle power systems)
- **Sensors**: Water temperature, dissolved oxygen, GPS module

## Contributing

This is a specialized aquaculture monitoring system. For contributions:

1. Follow existing code structure and patterns
2. Maintain cryptographic security standards
3. Understand fish transport safety requirements
4. Test with realistic aquaculture scenarios
5. Validate against fish survival thresholds

## License

This project is private/proprietary. Unauthorized reproduction or distribution is prohibited.

## Support

For technical support or questions about the LIVECON fish transport system:

1. Check console interface `help` command for monitoring commands
2. Review transport logs for water quality alerts
3. Verify fish tank sensor connectivity and GPS tracking
4. Monitor dissolved oxygen levels and temperature stability
5. Confirm emergency alert notifications are functioning

## Emergency Response

**Critical Situations:**
- **Low Dissolved Oxygen (< 4.0 mg/L)**: Immediate intervention required
- **Temperature Fluctuation (> ±3°C)**: Check cooling/heating systems  
- **GPS Signal Loss**: Verify location and restore connectivity
- **Sensor Offline**: Check power and network connections

---

**LIVECON (Live Container)** - Secure fish transport monitoring with real-time safety alerts