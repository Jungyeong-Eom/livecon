# IoT Sensor Data Collection System

A secure, encrypted IoT sensor data collection system with RSA-2048 encryption, multi-client support, and network-based public key distribution.

## Overview

This system consists of two main components:
- **Server**: Receives and processes encrypted sensor data from multiple clients
- **Client**: Simulates IoT sensors and sends encrypted data to the server

## Key Features

### Security
- **RSA-2048 Encryption**: All sensor data is encrypted using RSA-2048 with PKCS1_OAEP padding
- **Network Public Key Distribution**: Clients automatically fetch public keys from server
- **Sensor Authentication**: Server validates registered sensor IDs
- **Packet Integrity**: Checksum verification for all data packets

### Network & Deployment
- **Multi-Client Support**: Server handles multiple simultaneous client connections
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Independent Deployment**: Completely standalone executable files
- **No External Dependencies**: All modules embedded in executable files
- **Network Configuration**: Easy server IP configuration via JSON files

### Data Processing
- **32-byte Sensor Packets**: Structured data format with sensor readings
- **Geohash Location Encoding**: Efficient GPS coordinate storage
- **MySQL Database Integration**: Automatic sensor data storage
- **Real-time Processing**: Live sensor data monitoring and logging

## Architecture

```
[Client 1] ──┐
[Client 2] ──┼─→ [Server] ──→ [MySQL Database]
[Client N] ──┘
```

### Data Flow
1. Server generates RSA key pair on startup
2. Client requests public key from server (network-based)
3. Client generates 32-byte sensor packet (temperature, oxygen, water temp, GPS, timestamp)
4. Client encrypts packet using server's public key
5. Client sends encrypted data via TCP
6. Server decrypts and validates packet
7. Server stores data in MySQL database

### Packet Structure (32 bytes)
```
STX(1) + ID(2) + LEN(3) + TEMP(2) + O2(2) + WATER_TEMP(2) + 
GEOHASH(10) + TIMESTAMP(6) + CHECKSUM(2) + ETX(1)
```

## Installation & Usage

### Server Package

**Location**: `server_package/`

**Files**:
- `IoT_Sensor_Server.exe` - Standalone server executable (8.82 MB)
- `README.txt` - Detailed server usage instructions
- `build_independent.py` - Build script for development

**Running the Server**:
1. Simply run `IoT_Sensor_Server.exe`
2. Server automatically generates RSA keys (private.pem, public.pem)
3. Server starts listening on port 12351
4. Ready to accept client connections

**Requirements**:
- MySQL database configured (for data storage)
- Port 12351 available (automatically resolved if in use)

### Client Package

**Location**: `client_package/`

**Files**:
- `IoT_Sensor_Client.exe` - Standalone client executable (8.31 MB)
- `config.json` - Client configuration file
- `README.txt` - Detailed client usage instructions
- `build_independent.py` - Build script for development

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

**Running the Client**:
1. Edit `config.json` to set server IP address
2. Set unique `sensor_id` for each client instance
3. Run `IoT_Sensor_Client.exe`
4. Client automatically fetches public key from server
5. Starts sending encrypted sensor data every N seconds

## Multi-Client Deployment

### Server Deployment
1. Copy `server_package/IoT_Sensor_Server.exe` to server machine
2. Run the executable
3. Server is ready to accept multiple client connections

### Client Deployment
For each sensor location:
1. Copy `client_package/` folder to client machine
2. Edit `config.json`:
   - Set server IP address
   - Set unique sensor ID (e.g., SENSOR_A01, SENSOR_B01, etc.)
   - Adjust transmission interval if needed
3. Run `IoT_Sensor_Client.exe`
4. Each client operates independently

### Example Multi-Client Setup
```
Server (192.168.1.100):
└── IoT_Sensor_Server.exe

Client A (Sensor Location A):
├── IoT_Sensor_Client.exe
└── config.json (sensor_id: "SENSOR_A01")

Client B (Sensor Location B):
├── IoT_Sensor_Client.exe
└── config.json (sensor_id: "SENSOR_B01")

Client C (Sensor Location C):
├── IoT_Sensor_Client.exe
└── config.json (sensor_id: "SENSOR_C01")
```

## Database Setup

The system requires a MySQL database with the following schema:

### Database: `livecon_db`

**Table: `sensor_info`**
- Stores registered sensor IDs
- Used for sensor authentication

**Table: `sensor_result`**
- Stores all sensor measurements
- Includes location data and timestamps

### Connection Configuration
Database connection settings are handled internally by the server. Ensure MySQL is running and accessible.

## Network Requirements

### Firewall Configuration
- **Server**: Allow incoming connections on port 12351
- **Clients**: Allow outgoing connections to server IP on port 12351

### Network Topology
- Clients and server can be on same LAN or across internet
- Each client needs TCP connectivity to server
- No special routing or port forwarding required for basic LAN setup

## Development & Building

### Prerequisites
- Python 3.7+
- PyInstaller
- Required packages: pycryptodome, pymysql

### Build Process
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

## Troubleshooting

### Server Issues
- **Port already in use**: Server automatically resolves port conflicts
- **Database connection failed**: Check MySQL service and credentials
- **Key generation failed**: Ensure write permissions in server directory

### Client Issues
- **Connection refused**: Verify server is running and IP address is correct
- **Public key fetch failed**: Check network connectivity to server
- **Sensor ID validation failed**: Ensure sensor ID is registered in database

### Network Issues
- **Firewall blocking**: Allow port 12351 in firewall settings
- **IP address not reachable**: Verify network connectivity
- **Timeout errors**: Check for network latency or packet loss

## Security Considerations

### Encryption
- RSA-2048 provides strong security for sensor data
- Each packet is individually encrypted
- Public key distribution via secure channel

### Authentication
- Server validates all sensor IDs against database
- Unregistered sensors are automatically rejected
- Connection logging for audit purposes

### Best Practices
- Keep server private key secure (private.pem)
- Regularly rotate encryption keys if needed
- Monitor connection logs for unusual activity
- Use secure network connections when possible

## Performance

### Server Capacity
- Supports 100+ simultaneous client connections
- Multi-threaded client handling
- Efficient packet processing and database operations

### Network Usage
- Each sensor packet: 32 bytes (original) → 256 bytes (encrypted)
- Default transmission interval: 10 seconds per client
- Bandwidth usage: ~25 bytes/second per client

### System Requirements
- **Server**: 2GB RAM, 1GB disk space, network connectivity
- **Client**: 512MB RAM, 100MB disk space, network connectivity

## License & Support

This is a demonstration IoT sensor data collection system with enterprise-grade security features.

For technical support or deployment assistance, refer to the individual README.txt files in each package folder.

## Version Information

- **Server Package**: v1.0 - Standalone encrypted sensor data server
- **Client Package**: v1.0 - Standalone sensor simulator client
- **Encryption**: RSA-2048 with PKCS1_OAEP padding
- **Network Protocol**: TCP with automatic public key distribution
- **Database**: MySQL integration with sensor authentication