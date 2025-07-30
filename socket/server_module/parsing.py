#parsing.py
from server_module import checksum
from server_module.geohash_decode import geohash_decode

def parse_packet(data: bytes):
    if len(data) < 32:
        raise ValueError("Data length is too short")
    
    if data[0] != ord('$'):
        raise ValueError("STX error!")
    
    data_id = int.from_bytes(data[1:3], 'big')
    length = int.from_bytes(data[3:6], 'big')

    temp_raw = int.from_bytes(data[6:8], 'big', signed = False)
    do_raw = int.from_bytes(data[8:10], 'big', signed = False)
    wtr_temp_raw = int.from_bytes(data[10:12], 'big', signed = False)

    temp = temp_raw / 10.0
    if (temp < -40.0 or temp > 125.0):
        raise ValueError("Temperature out of range (-40.0 to 125.0)")
    do = do_raw / 100.0
    if (do < 0.0 or do > 60.0):
        raise ValueError("DO out of range (0.0 to 60.0)")
    wtr_temp = wtr_temp_raw / 10.0
    if (wtr_temp < 0.0 or wtr_temp > 100.0):
        raise ValueError("Water temperature out of range (0.0 to 100.0)")
    loc = geohash_decode(data[12:22])
    

    year = int.from_bytes(data[22:24], 'big')
    if (year < 2000 or year > 2099):
        raise ValueError("Year out of range (2000 to 2099)")
    month = data[24]
    if (month < 1 or month > 12):
        raise ValueError("Month out of range (1 to 12)")
    day = data[25]
    if (day < 1 or day > 31):
        raise ValueError("Day out of range (1 to 31)")
    hour = data[26]
    if (hour < 0 or hour > 23):
        raise ValueError("Hour out of range (0 to 23)")
    minute = data[27]
    if (minute < 0 or minute > 59):
        raise ValueError("Minute out of range (0 to 59)")
    second = data[28]
    if (second < 0 or second > 59):
        raise ValueError("Second out of range (0 to 59)")
    
    chk = int.from_bytes(data[29:31], 'big')
    
    if (chk != int.from_bytes(checksum.checksum(data))):
        raise ValueError("Checksum error!") 
    
    if (data[31] != ord('\\')):
        raise ValueError("ETX error!")
    
    return {
        'ID': data_id,
        'LEN': length,
        'TEMP': temp,
        'DO': do,
        'WTR_TEMP': wtr_temp,
        'LOC': loc,
        'TIME': f'{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}',
        'CHK': chk
    }