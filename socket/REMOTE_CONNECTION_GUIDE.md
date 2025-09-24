# 원격 디바이스 연결 가이드

## 문제 해결된 항목들

### 1. ECDHE 키 교환 최적화
- 네트워크 타임아웃을 60초 → 120초로 증가
- Keep-alive 및 소켓 재사용 옵션 추가
- 응답 데이터 수신 시 청크 크기 제한 및 타임아웃 처리 개선

### 2. 연결 설정 개선
- 연결 재시도 대기시간 증가 (5초 → 10초)
- 재연결 대기시간 증가 (10초 → 15초)

## 다른 디바이스에서 클라이언트 실행 방법

### 1. 서버 IP 주소 확인
서버가 실행되는 컴퓨터에서 IP 주소를 확인하세요:
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig 또는 ip addr show
```

### 2. 클라이언트 설정 파일 수정
`client_package/config.json` 파일을 다음과 같이 수정:

```json
{
    "server": {
        "address": "실제_서버_IP_주소",  // 예: "192.168.1.100"
        "port": 12351
    },
    "client": {
        "device_id": "device001",
        "send_interval": 10
    }
}
```

### 3. 방화벽 설정
- 서버 컴퓨터에서 포트 12351 인바운드 허용
- 클라이언트 컴퓨터에서 포트 12351 아웃바운드 허용

### 4. 네트워크 연결 확인
클라이언트에서 서버 연결 테스트:
```bash
# Windows
telnet 서버_IP_주소 12351

# Linux/Mac
nc -zv 서버_IP_주소 12351
```

## 주요 개선사항

### ECDHE 키 교환 개선 (`ecdhe_crypto.py:45-48`)
- 타임아웃: 60초 → 120초
- Keep-alive 소켓 옵션 추가
- 주소 재사용 옵션 추가

### 응답 수신 로직 개선 (`ecdhe_crypto.py:59-83`)
- 응답 길이 수신 시 타임아웃 처리
- 데이터 수신 시 청크 크기 제한 (4096 바이트)
- 상세한 에러 메시지 제공

### 연결 재시도 로직 개선 (`client.py:110-113`)
- 원격 연결에 최적화된 대기시간 설정

## 테스트 방법

1. 서버를 한 컴퓨터에서 실행
2. 다른 컴퓨터에서 config.json의 서버 주소를 실제 IP로 변경
3. 클라이언트 실행 후 연결 로그 확인

연결 성공 시 다음 메시지가 출력됩니다:
```
iot-client[device001]: ECDHE key exchange successful - PFS activated
iot-client[device001]: secure ECDHE session established - ready for data transmission
```