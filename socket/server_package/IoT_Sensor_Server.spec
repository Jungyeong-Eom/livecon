# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=['.'],
    binaries=[],
    datas=[('server_module', 'server_module')],
    hiddenimports=['server_module', 'server_module.console_manager', 'server_module.console_interface', 'server_module.database_manager', 'server_module.crypto_manager', 'server_module.process_manager', 'server_module.server_core', 'server_module.client_manager', 'server_module.connection_manager', 'server_module.alarm_manager', 'server_module.sensor_monitor', 'server_module.packet_parser', 'pymysql', 'Crypto.PublicKey.RSA', 'Crypto.Cipher.PKCS1_OAEP'],
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
