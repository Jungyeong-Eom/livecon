def binary_to_decimal(binary_str):
    decimal = 0
    for i, digit in enumerate(reversed(binary_str)):
        decimal += int(digit) * (2 ** i)
    return decimal

def geohash_encode(lat, lon, precision=10):
    base32_chars = '0123456789bcdefghjkmnpqrstuvwxyz'
    
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Latitude must be between -90 and 90, and longitude between -180 and 180.")
    if not (1 <= precision <= 10):
        raise ValueError("Precision must be between 1 and 16.")

    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    geohash = []
    bit = 0
    ch = 0
    is_lon = True

    while len(geohash) < precision:
        if is_lon:
            mid = (lon_range[0] + lon_range[1]) / 2
            if lon >= mid:
                ch = (ch << 1) | 1
                lon_range[0] = mid
            else:
                ch = (ch << 1)
                lon_range[1] = mid
        else:
            mid = (lat_range[0] + lat_range[1]) / 2
            if lat >= mid:
                ch = (ch << 1) | 1
                lat_range[0] = mid
            else:
                ch = (ch << 1)
                lat_range[1] = mid
        is_lon = not is_lon

        bit += 1
        if bit == 5:  # 5비트가 쌓이면 base32 변환
            geohash.append(base32_chars[ch])
            bit = 0
            ch = 0

    return ''.join(geohash)
