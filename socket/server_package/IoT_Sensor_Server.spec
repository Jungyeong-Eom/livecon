# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=['.'],
    binaries=[],
    datas=[('server_module', 'server_module')],
    hiddenimports=['server_module', 'server_module.console_manager', 'server_module.console_interface', 'server_module.database_manager', 'server_module.crypto_manager', 'server_module.process_manager', 'server_module.server_core', 'server_module.client_manager', 'server_module.connection_manager', 'server_module.alarm_manager', 'server_module.sensor_monitor', 'server_module.packet_parser', 'server_module.key_exchange_handler', 'server_module.security_utils', 'cryptography.hazmat.primitives.asymmetric.x25519', 'cryptography.hazmat.primitives.asymmetric.ed25519', 'cryptography.hazmat.primitives.ciphers.aead', 'cryptography.hazmat.primitives.serialization', 'cryptography.hazmat.primitives.hashes', 'cryptography.hazmat.primitives.kdf.hkdf', 'pymysql'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='IoT_Sensor_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\git_repo\\socket\\server_package\\server_icon.ico'],
)
