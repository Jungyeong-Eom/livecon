# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=['.'],
    binaries=[],
    datas=[('server_module', 'server_module')],
    hiddenimports=['server_module', 'server_module.rsa_utils', 'server_module.parsing', 'server_module.sql_utils', 'server_module.checksum', 'server_module.geohash_decode', 'pymysql', 'Crypto.PublicKey.RSA', 'Crypto.Cipher.PKCS1_OAEP'],
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
)
