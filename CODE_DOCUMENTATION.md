# LIVECON IoT 시스템 - 코드 문서

## 목차
1. [시스템 개요](#1-시스템-개요)
2. [보안 아키텍처](#2-보안-아키텍처)
3. [핵심 코드 설명](#3-핵심-코드-설명)
4. [빌드 및 배포](#4-빌드-및-배포)

---

## 1. 시스템 개요

### 1.1 프로젝트 정보
- **프로젝트명**: LIVECON IoT Sensor System
- **설명**: ECDHE + Ed25519 기반의 보안 IoT 센서 모니터링 시스템
- **주요 기능**:
  - 안전한 ECDHE 키 교환 (Perfect Forward Secrecy)
  - Ed25519 디지털 서명 및 서버 공개키 고정 (MITM 방지)
  - ChaCha20-Poly1305 AEAD 암호화
  - 실시간 센서 데이터 모니터링 및 알람

### 1.2 기술 스택
```
암호화: cryptography (ECDHE, Ed25519, ChaCha20-Poly1305, HKDF)
통신: TCP 소켓 (커스텀 프로토콜)
데이터베이스: SQLite3
빌드: PyInstaller (단일 실행파일)
```

### 1.3 디렉토리 구조
```
socket/
├── client_package/          # 클라이언트 (센서 디바이스)
│   ├── client.py           # 메인 클라이언트
│   ├── config.json         # 클라이언트 설정
│   ├── node_module/
│   │   ├── ecdhe_crypto.py     # ECDHE + 암호화
│   │   ├── generate_packet.py   # 패킷 생성
│   │   └── security_utils.py    # 보안 유틸리티
│   └── IoT_Sensor_Client.spec  # PyInstaller 빌드 설정
│
└── server_package/          # 서버 (모니터링 시스템)
    ├── server.py           # 메인 서버
    ├── server_module/
    │   ├── server_core.py          # TCP 서버 코어
    │   ├── crypto_manager.py       # 암호화 관리
    │   ├── key_exchange_handler.py # 키 교환 핸들러
    │   ├── client_manager.py       # 클라이언트 세션 관리
    │   ├── database_manager.py     # SQLite DB 관리
    │   ├── console_manager.py      # CLI 인터페이스
    │   └── security_utils.py       # 보안 유틸리티
    ├── extract_server_pubkey.py    # 서버 공개키 추출 도구
    └── IoT_Sensor_Server.spec      # PyInstaller 빌드 설정
```

---

## 2. 보안 아키텍처

### 2.1 전체 보안 흐름

```
[클라이언트]                                    [서버]
    │
    │  1. ECDHE 키 교환 요청
    ├──────────────────────────────────────────>
    │  "ECDHE_KEY_EXCHANGE:<device_id>:<client_x25519_pubkey_hex>"
    │
    │  2. 서버 응답 (144 bytes)
    <──────────────────────────────────────────┤
    │  [server_x25519_pubkey(32) + signature(64) +
    │   server_ed25519_pubkey(32) + hkdf_salt(16)]
    │
    │  3. 서버 공개키 고정 검증 (MITM 방지)
    │  4. Ed25519 서명 검증
    │  5. ECDHE 공유 비밀 계산
    │  6. HKDF로 세션 키 유도
    │
    │  7. 암호화된 센서 데이터 전송
    ├──────────────────────────────────────────>
    │  [encrypted_data + auth_tag]
    │
    │  8. 데이터 복호화 및 저장
    │  9. 재생 공격 방지 검증
    <──────────────────────────────────────────┤
```

### 2.2 핵심 보안 기능

#### ✅ Perfect Forward Secrecy (PFS)
- 매 세션마다 새로운 X25519 임시 키쌍 생성
- 세션 종료 시 private key 완전 삭제
- 과거 세션 데이터는 새 세션 키로 복호화 불가능

#### ✅ MITM 공격 방지 (서버 공개키 고정)
```python
# client_package/config.json
{
    "server": {
        "ed25519_pubkey_hex": "a1b2c3d4..."  # 서버의 Ed25519 공개키 (64자 hex)
    }
}

# client_package/node_module/ecdhe_crypto.py:104-113
if self.pinned_server_pubkey is not None:
    if self.server_ed25519_pubkey_bytes != self.pinned_server_pubkey:
        raise AuthenticationError("MITM attack detected!")
```

#### ✅ 재생 공격 방지 (Nonce 검증)
```python
# Nonce 구조: 12 bytes
# [session_prefix(4)] + [counter(8)]
#  - session_prefix: 세션 시작 시 랜덤 생성 (4 bytes)
#  - counter: 메시지마다 증가 (8 bytes, big-endian)

# server_module/crypto_manager.py:42-73
def decrypt(self, ciphertext: bytes, aad: bytes) -> bytes:
    # 1. Nonce에서 counter 추출
    received_counter = int.from_bytes(nonce[4:], 'big')

    # 2. Counter 검증 (재생 공격 방지)
    if received_counter <= self.last_nonce_counter:
        raise ValueError("Replay attack detected: nonce reused")

    # 3. Counter 업데이트
    self.last_nonce_counter = received_counter
```

#### ✅ AEAD 암호화 (ChaCha20-Poly1305)
```python
# AAD (Additional Authenticated Data)
aad = f"{device_id}|LIVECON_v1.0".encode()

# 암호화 (client_package/node_module/ecdhe_crypto.py:158-170)
ciphertext = cipher.encrypt(nonce, plaintext, aad)
# Output: encrypted_data + 16-byte authentication tag

# 복호화 (server_module/crypto_manager.py:42-73)
plaintext = cipher.decrypt(nonce, ciphertext, aad)
# InvalidTag 예외 발생 시 위변조 감지
```

---

## 3. 핵심 코드 설명

### 3.1 클라이언트: ECDHE 키 교환 및 암호화

#### `client_package/node_module/ecdhe_crypto.py`

**클래스**: `ECDHECrypto`

**핵심 메서드**:

##### `__init__(device_id, pinned_server_pubkey=None)`
```python
def __init__(self, device_id: str, pinned_server_pubkey: Optional[bytes] = None):
    self.device_id = device_id
    self.session_key = None
    self.nonce_counter = 0
    self.nonce_session_prefix = None  # 세션별 Nonce 프리픽스
    self.pinned_server_pubkey = pinned_server_pubkey  # MITM 방지용
```

##### `perform_key_exchange(server_address, server_port)` (핵심!)
```python
def perform_key_exchange(self, server_address: str, server_port: int):
    """
    ECDHE 키 교환 수행 및 세션 키 생성

    흐름:
    1. X25519 임시 키쌍 생성
    2. 서버에 공개키 전송
    3. 서버 응답 수신 (144 bytes)
    4. 서버 공개키 고정 검증 (MITM 방지)
    5. Ed25519 서명 검증
    6. ECDHE 공유 비밀 계산
    7. HKDF로 세션 키 유도
    8. Nonce 세션 프리픽스 생성

    Returns:
        socket: 연결된 소켓 (성공 시)
        None: 실패 시
    """
    # 1. X25519 임시 키쌍 생성 (PFS)
    client_private_key = X25519PrivateKey.generate()
    client_public_key_bytes = client_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # 2. 키 교환 요청 전송
    key_exchange_msg = f"ECDHE_KEY_EXCHANGE:{self.device_id}:{client_public_key_bytes.hex()}"

    # 3. 서버 응답 수신 (144 bytes)
    # [server_x25519_pubkey(32) + signature(64) +
    #  server_ed25519_pubkey(32) + hkdf_salt(16)]

    # 4. 서버 공개키 고정 검증 (CRITICAL!)
    if self.pinned_server_pubkey is not None:
        if self.server_ed25519_pubkey_bytes != self.pinned_server_pubkey:
            raise AuthenticationError("MITM attack detected!")

    # 5. Ed25519 서명 검증
    server_ed25519_pubkey.verify(signature, message_to_verify)

    # 6. ECDHE - 공유 비밀 계산
    shared_secret = client_private_key.exchange(server_x25519_pubkey)

    # 7. HKDF로 세션 키 유도
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=hkdf_salt,
        info=b"LIVECON_IoT_Session_v1.0"
    )
    self.session_key = hkdf.derive(shared_secret)

    # 8. Nonce 세션 프리픽스 생성 (재생 공격 방지)
    self.nonce_session_prefix = os.urandom(4)
```

##### `encrypt(plaintext)`
```python
def encrypt(self, plaintext: bytes) -> bytes:
    """
    ChaCha20-Poly1305 AEAD 암호화

    Returns:
        nonce(12) + ciphertext + auth_tag(16)
    """
    # Nonce 생성: [session_prefix(4)] + [counter(8)]
    self.nonce_counter += 1
    nonce = self.nonce_session_prefix + self.nonce_counter.to_bytes(8, 'big')

    # AAD 구성
    aad = f"{self.device_id}|LIVECON_v1.0".encode()

    # 암호화
    cipher = ChaCha20Poly1305(self.session_key)
    ciphertext = cipher.encrypt(nonce, plaintext, aad)

    return nonce + ciphertext
```

---

### 3.2 서버: 암호화 관리자

#### `server_package/server_module/crypto_manager.py`

**클래스**: `CryptoManager`

**핵심 메서드**:

##### `generate_key_exchange_response(client_x25519_pubkey_bytes, device_id)`
```python
def generate_key_exchange_response(self, client_x25519_pubkey_bytes: bytes, device_id: str):
    """
    ECDHE 키 교환 응답 생성

    Returns:
        tuple: (response_bytes(144), session_key(32), hkdf_salt(16))
    """
    # 1. X25519 임시 키쌍 생성 (PFS)
    server_private_key = X25519PrivateKey.generate()
    server_public_key_bytes = server_private_key.public_key().public_bytes(...)

    # 2. HKDF salt 생성 (암호학적 안전)
    hkdf_salt = os.urandom(16)

    # 3. Ed25519 서명 생성
    message_to_sign = server_public_key_bytes + client_x25519_pubkey_bytes + \
                      device_id.encode() + hkdf_salt
    signature = self.ed25519_private_key.sign(message_to_sign)

    # 4. 응답 구성 (144 bytes)
    response = server_public_key_bytes + signature + \
               self.ed25519_public_key_bytes + hkdf_salt

    # 5. ECDHE - 공유 비밀 계산
    shared_secret = server_private_key.exchange(client_x25519_pubkey)

    # 6. HKDF로 세션 키 유도
    session_key = HKDF(...).derive(shared_secret)

    # 7. 임시 키 삭제 (PFS)
    del server_private_key

    return response, session_key, hkdf_salt
```

**클래스**: `ClientSession`

##### `decrypt(ciphertext, aad)` (재생 공격 방지!)
```python
def decrypt(self, ciphertext: bytes, aad: bytes) -> bytes:
    """
    ChaCha20-Poly1305 복호화 + 재생 공격 검증

    Raises:
        ValueError: Nonce 재사용 감지 (재생 공격)
        InvalidTag: 인증 태그 검증 실패 (위변조)
    """
    # 1. Nonce 추출 (12 bytes)
    nonce = ciphertext[:12]
    actual_ciphertext = ciphertext[12:]

    # 2. Counter 추출 및 검증
    received_counter = int.from_bytes(nonce[4:], 'big')

    if received_counter <= self.last_nonce_counter:
        raise ValueError("Replay attack detected!")

    # 3. 복호화
    plaintext = self.cipher.decrypt(nonce, actual_ciphertext, aad)

    # 4. Counter 업데이트
    self.last_nonce_counter = received_counter

    return plaintext
```

---

### 3.3 서버: 키 교환 핸들러

#### `server_package/server_module/key_exchange_handler.py`

##### `handle_key_exchange(client_socket, client_address, message, crypto_manager, client_manager)`
```python
def handle_key_exchange(client_socket, client_address, message,
                       crypto_manager, client_manager):
    """
    ECDHE 키 교환 프로토콜 처리

    메시지 형식:
        "ECDHE_KEY_EXCHANGE:<device_id>:<client_x25519_pubkey_hex>"

    응답:
        [4-byte length] + [144-byte response]
    """
    # 1. 메시지 파싱
    parts = message.split(':')
    device_id = parts[1]
    client_public_key_hex = parts[2]
    client_x25519_pubkey_bytes = bytes.fromhex(client_public_key_hex)

    # 2. 키 교환 응답 생성
    response, session_key, hkdf_salt = crypto_manager.generate_key_exchange_response(
        client_x25519_pubkey_bytes, device_id
    )

    # 3. 클라이언트 세션 등록
    client_manager.register_client(
        device_id, client_socket, client_address,
        session_key, hkdf_salt
    )

    # 4. 응답 전송
    response_length = len(response).to_bytes(4, 'big')
    client_socket.sendall(response_length + response)
```

---

### 3.4 서버: 클라이언트 관리자

#### `server_package/server_module/client_manager.py`

**클래스**: `ClientManager`

##### `register_client(device_id, socket, address, session_key, hkdf_salt)`
```python
def register_client(self, device_id: str, socket, address,
                   session_key: bytes, hkdf_salt: bytes):
    """
    클라이언트 세션 등록

    - ClientSession 객체 생성 (암호화 + 재생 공격 방지)
    - 세션별 Nonce counter 관리
    """
    session = ClientSession(session_key, hkdf_salt)

    self.clients[device_id] = {
        'socket': socket,
        'address': address,
        'session': session,
        'connected_at': time.time(),
        'last_seen': time.time()
    }
```

---

### 3.5 클라이언트: 설정 파일

#### `client_package/config.json`
```json
{
    "server": {
        "address": "127.0.0.1",
        "port": 12351,
        "ed25519_pubkey_hex": "abc123..."  // 서버 공개키 고정 (MITM 방지)
    },
    "client": {
        "device_id": "device001",
        "send_interval": 5
    }
}
```

**서버 공개키 추출 방법**:
```bash
# 서버에서 공개키 추출
python server_package/extract_server_pubkey.py

# 출력:
# Server Ed25519 Public Key (Hex): a1b2c3d4e5f6...
#
# Add this to client config.json:
# "ed25519_pubkey_hex": "a1b2c3d4e5f6..."
```

---

## 4. 빌드 및 배포

### 4.1 PyInstaller 빌드

**클라이언트 빌드**:
```bash
cd client_package
pyinstaller IoT_Sensor_Client.spec
# 출력: dist/IoT_Sensor_Client.exe
```

**서버 빌드**:
```bash
cd server_package
pyinstaller IoT_Sensor_Server.spec
# 출력: dist/IoT_Sensor_Server.exe
```

### 4.2 배포 구조
```
배포 폴더/
├── IoT_Sensor_Client.exe   # 클라이언트 실행파일
├── config.json             # 클라이언트 설정 (서버 주소, 공개키 등)
└── [센서 디바이스에 배포]

서버 폴더/
├── IoT_Sensor_Server.exe   # 서버 실행파일
├── server_ed25519.key      # 서버 개인키 (비밀!)
└── iot_monitoring.db       # SQLite 데이터베이스 (자동 생성)
```

### 4.3 중요 보안 사항

1. **서버 개인키 보호**
   - `server_ed25519.key` 파일은 절대 외부 노출 금지
   - Git에 커밋하지 말 것 (.gitignore 등록 권장)

2. **클라이언트 공개키 고정**
   - 프로덕션 환경에서는 반드시 `ed25519_pubkey_hex` 설정
   - MITM 공격 방지를 위한 필수 설정

3. **네트워크 보안**
   - 방화벽에서 서버 포트(12351) 허용
   - TLS/SSL 레이어 추가 고려 (선택사항)

---

## 참고: 주요 파일 위치

| 기능 | 파일 경로 |
|------|----------|
| 클라이언트 메인 | `client_package/client.py` |
| 클라이언트 암호화 | `client_package/node_module/ecdhe_crypto.py` |
| 서버 메인 | `server_package/server.py` |
| 서버 암호화 관리 | `server_package/server_module/crypto_manager.py` |
| 키 교환 핸들러 | `server_package/server_module/key_exchange_handler.py` |
| 클라이언트 관리 | `server_package/server_module/client_manager.py` |
| 공개키 추출 도구 | `server_package/extract_server_pubkey.py` |

---

**문서 버전**: 2.0 (간소화)
**마지막 업데이트**: 2025-10-23
