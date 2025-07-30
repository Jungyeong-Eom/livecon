def geohash_decode(geohash: bytes):
    geohash = geohash.decode('ascii')
    base32_chars = '0123456789bcdefghjkmnpqrstuvwxyz'
    lon_range = [-180.0, 180.0]
    lat_range = [-90.0, 90.0]

    bits = ''
    for char in geohash:
        value = base32_chars.index(char)
        bits += f'{value:05b}'  # 5-bit binary

    lon_bits = bits[0::2]
    lat_bits = bits[1::2]

    for bit in lon_bits:
        mid = (lon_range[0] + lon_range[1]) / 2
        if bit == '1':
            lon_range[0] = mid
        else:
            lon_range[1] = mid

    for bit in lat_bits:
        mid = (lat_range[0] + lat_range[1]) / 2
        if bit == '1':
            lat_range[0] = mid
        else:
            lat_range[1] = mid

    # Step 4: Return midpoint of the final ranges
    lat = (lat_range[0] + lat_range[1]) / 2
    lon = (lon_range[0] + lon_range[1]) / 2

    return lat, lon