# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['client.py'],
    pathex=['.'],
    binaries=[],
    datas=[('node_module', 'node_module')],
    hiddenimports=['node_module', 'node_module.ecdhe_crypto', 'node_module.generate_packet', 'node_module.geohash_encode', 'node_module.security_utils', 'cryptography.hazmat.primitives.asymmetric.x25519', 'cryptography.hazmat.primitives.asymmetric.ed25519', 'cryptography.hazmat.primitives.ciphers.aead', 'cryptography.hazmat.primitives.serialization', 'cryptography.hazmat.primitives.hashes', 'cryptography.hazmat.primitives.kdf.hkdf'],
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
    name='IoT_Sensor_Client',
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
    icon=['C:\\git_repo\\socket\\client_package\\client_icon.ico'],
)
