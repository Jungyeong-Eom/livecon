# LIVECON IoT Sensor System

> Real-time IoT sensor data collection and monitoring system with advanced encryption technology

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Security](https://img.shields.io/badge/Security-ECDHE%20%7C%20Ed25519%20%7C%20ChaCha20-green.svg)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Security Features](#-security-features)
- [System Requirements](#-system-requirements)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Documentation](#-documentation)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## 🌟 Overview

LIVECON IoT System is an enterprise-grade solution that collects and monitors data from IoT sensors in real-time. It ensures data security with cutting-edge encryption technology and provides automatic alarm and anomaly detection features.

### Sensor Data Types
- 🌡️ **Temperature**
- 💧 **Dissolved Oxygen**
- 🌊 **Water Temperature**
- 📍 **Location Information** (Geohash 10 digits, ~60cm precision)

## ✨ Key Features

### Real-time Monitoring
- Simultaneous monitoring of multiple sensors
- Real-time data collection and storage
- Web-based dashboard (optional)

### Automatic Alarm System
- Threshold-based alarms
- Sensor offline detection
- Data anomaly detection (sudden changes, stuck data)
- Sensor measurement range overflow detection
- Real-time alarm logging

### Data Management
- MySQL database storage
- Original packet preservation (for debugging)
- Sensor metadata management
- Alarm history tracking

## 🔒 Security Features

### Encryption Protocols
| Technology | Purpose | Details |
|------------|---------|---------|
| **ECDHE (X25519)** | Key Exchange | Perfect Forward Secrecy guaranteed |
| **Ed25519** | Digital Signature | Server authentication and public key pinning |
| **ChaCha20-Poly1305** | Symmetric Encryption | AEAD (Authenticated Encryption) |
| **HKDF-SHA256** | Key Derivation | Salt-based strong key generation |

### Security Features
✅ **Perfect Forward Secrecy (PFS)** - Protects previous communications even if session key is compromised
✅ **Public Key Pinning** - Prevents MITM attacks
✅ **Replay Attack Prevention** - Nonce counter-based duplicate packet rejection
✅ **Integrity Assurance** - Data tampering detection with Poly1305 MAC
✅ **Context Binding** - Device ID verification with AAD

## 💻 System Requirements

### Server
- **OS**: Windows 10+ / Linux (Ubuntu 20.04+, CentOS 7+)
- **Python**: 3.8 or higher
- **Database**: MySQL 5.7+ or MariaDB 10.3+
- **Memory**: Minimum 2GB RAM
- **Disk**: Minimum 10GB free space

### Client
- **OS**: Windows 10+ / Linux
- **Python**: 3.8 or higher (for development) / Not required when using executable
- **Memory**: Minimum 512MB RAM

### Network
- **Port**: TCP 12351 (default, configurable)
- **Firewall**: Server port must be open

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/livecon-iot.git
cd livecon-iot
```

### 2. Database Setup
```bash
# Connect to MySQL/MariaDB
mysql -u root -p

# Create database
CREATE DATABASE sensor_db CHARACTER SET utf8mb4;

# Execute table creation script
source database/schema.sql
```

### 3. Server Configuration and Execution
```bash
cd server_package

# Install dependencies
pip install -r requirements.txt

# Edit configuration file
# Modify database connection information in config.json

# Run server
python server.py
```

### 4. Extract Server Public Key
```bash
cd server_package
python extract_server_pubkey.py

# Copy the output public key to client config.json
```

### 5. Client Configuration and Execution
```bash
cd client_package

# Install dependencies
pip install -r requirements.txt

# Edit configuration file
# Set server address, port, and public key in config.json

# Run client
python client.py
```

## 📦 Installation

### Development Environment Setup

#### Server
```bash
cd server_package
pip install -r requirements.txt
```

**requirements.txt**:
```
cryptography>=41.0.0
PyMySQL>=1.1.0
```

#### Client
```bash
cd client_package
pip install -r requirements.txt
```

**requirements.txt**:
```
cryptography>=41.0.0
```

### Building Executables

#### Windows
```bash
# Build client
cd client_package
pyinstaller --clean --noconfirm IoT_Sensor_Client.spec

# Build server
cd server_package
pyinstaller --clean --noconfirm IoT_Sensor_Server.spec
```

#### Linux
```bash
# Build client
cd client_package
pyinstaller --clean --noconfirm IoT_Sensor_Client.spec

# Build server
cd server_package
pyinstaller --clean --noconfirm IoT_Sensor_Server.spec
```

Built executables will be created in the `dist/` directory.

## 📖 Usage

### Server Configuration File (`server_package/config.json`)

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

### Client Configuration File (`client_package/config.json`)

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

**Important**: For `ed25519_pubkey_hex`, enter the value obtained by running `extract_server_pubkey.py` on the server.

### Sensor Information Registration

```sql
-- Register sensor information in sensor_info table
INSERT INTO sensor_info (device_id, sensor_type_id, sensor_name, alarm_min, alarm_max, sensor_min, sensor_max, resolution)
VALUES
('device001', 0, 'Temperature Sensor', 15.0, 35.0, -40.0, 125.0, 0.1),
('device001', 1, 'Water Temperature Sensor', 15.0, 35.0, 0.0, 100.0, 0.1),
('device001', 2, 'Dissolved Oxygen Sensor', 5.0, 15.0, 0.0, 60.0, 0.01);
```

### Execution

#### Development Mode
```bash
# Server
cd server_package
python server.py

# Client
cd client_package
python client.py
```

#### Executable Mode
```bash
# Windows Server
cd server_package\dist
IoT_Sensor_Server.exe

# Windows Client
cd client_package\dist
IoT_Sensor_Client.exe

# Linux Server
cd server_package/dist
./IoT_Sensor_Server

# Linux Client
cd client_package/dist
./IoT_Sensor_Client
```

## 📚 Documentation

For detailed technical documentation, please refer to:

- **[CODE_DOCUMENTATION.md](CODE_DOCUMENTATION.md)** - Complete code documentation
  - System architecture
  - Core module explanations
  - Detailed security protocol descriptions
  - Build and deployment guide

## 📁 Project Structure

```
livecon-iot/
├── client_package/              # Client package
│   ├── client.py               # Main client program
│   ├── config.json             # Client configuration file
│   ├── IoT_Sensor_Client.spec  # PyInstaller build configuration
│   ├── requirements.txt        # Python dependencies
│   └── node_module/            # Client modules
│       ├── ecdhe_crypto.py     # ECDHE encryption
│       ├── generate_packet.py  # Sensor packet generation
│       ├── geohash_encode.py   # Geohash encoding
│       └── security_utils.py   # Security utilities
│
├── server_package/              # Server package
│   ├── server.py               # Main server program
│   ├── config.json             # Server configuration file
│   ├── IoT_Sensor_Server.spec  # PyInstaller build configuration
│   ├── requirements.txt        # Python dependencies
│   ├── extract_server_pubkey.py # Server public key extraction utility
│   └── server_module/          # Server modules
│       ├── crypto_manager.py       # Encryption session management
│       ├── key_exchange_handler.py # Key exchange handler
│       ├── client_manager.py       # Client management
│       ├── packet_parser.py        # Packet parser
│       ├── server_core.py          # Server socket management
│       ├── connection_manager.py   # Connection state management
│       ├── alarm_manager.py        # Alarm management
│       ├── sensor_monitor.py       # Sensor monitoring
│       ├── database_manager.py     # Database management
│       └── security_utils.py       # Security utilities
│
├── database/                    # Database scripts
│   └── schema.sql              # Database schema
│
├── CODE_DOCUMENTATION.md        # Complete code documentation
├── README.md                    # This file
└── LICENSE                      # License file
```

## 🔧 Troubleshooting

### Connection Failure

**Symptom**: Client cannot connect to server

**Solution**:
1. Verify server IP address and port
2. Check firewall settings
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="LIVECON Server" dir=in action=allow protocol=TCP localport=12351

   # Linux (iptables)
   sudo iptables -A INPUT -p tcp --dport 12351 -j ACCEPT
   ```
3. Verify server is running
   ```bash
   # Windows
   netstat -an | findstr 12351

   # Linux
   netstat -an | grep 12351
   ```

### Key Exchange Failure

**Symptom**: "Server signature verification failed" or "MITM attack detected"

**Solution**:
1. Extract server public key again
   ```bash
   cd server_package
   python extract_server_pubkey.py
   ```
2. Copy the output public key exactly to `ed25519_pubkey_hex` in client `config.json`
3. Restart client

### Replay Attack Detected

**Symptom**: "Replay attack detected"

**Solution**:
1. Restart client (establish new ECDHE session)
2. Check if packet duplication is occurring on the network

### Database Connection Failure

**Symptom**: "Database connection error"

**Solution**:
1. Verify MySQL/MariaDB service is running
   ```bash
   # Windows
   net start MySQL

   # Linux
   sudo systemctl status mysql
   ```
2. Verify database connection information in server `config.json`
3. Check database user privileges
   ```sql
   GRANT ALL PRIVILEGES ON sensor_db.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Sensor Data Not Being Saved

**Symptom**: Sensor data is not being saved to database

**Solution**:
1. Check if sensor information is registered in `sensor_info` table
   ```sql
   SELECT * FROM sensor_info WHERE device_id = 'device001';
   ```
2. If not registered, register sensor information (see [Usage](#-usage))

## 🔐 Security Recommendations

1. **Enable Public Key Pinning**: Always set the server public key in client `config.json`.
2. **Strong Database Password**: Set a strong password for the database user.
3. **Firewall Configuration**: Restrict server port access to trusted IPs only.
4. **Regular Updates**: Keep the cryptography library up to date.
5. **Log Monitoring**: Regularly check alarm logs.

## 🎯 Future Plans

- [ ] Web-based dashboard development
- [ ] Extended support for various sensor types
- [ ] Clustering support (server high availability)
- [ ] REST API provision
- [ ] Mobile app development

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Libraries

This project uses the following open-source libraries:

- **cryptography** (Apache License 2.0 / BSD) - Cryptographic operations
- **PyMySQL** (MIT License) - MySQL database connectivity
- **PyInstaller** (GPL 2.0 with exception) - Executable building
- **Pillow** (HPND License) - Image processing

---

**© 2025 LIVECON IoT Team. Released under MIT License.**
