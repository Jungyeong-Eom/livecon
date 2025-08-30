class PacketParser:
    def __init__(self, console_manager=None):
        self.console_manager = console_manager
    
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
        else:
            # Silently ignore when console manager is absent (panel system priority)
            pass
    
    def _checksum(self, data: bytes):
        """Calculate checksum"""
        if len(data) < 32:
            raise ValueError("Data length is too short for checksum calculation")
        if data[0] != ord('$'):
            raise ValueError("STX error!")
        if data[-1] != ord('\\'):
            raise ValueError("ETX error!")
        chk = sum(data[1:-3])
        chk &= 0xFFFF  
        return chk.to_bytes(2, 'big')
    
    def _geohash_decode(self, geohash: bytes):
        """Geohash decoding"""
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

        lat = (lat_range[0] + lat_range[1]) / 2
        lon = (lon_range[0] + lon_range[1]) / 2
        return lat, lon
    
    def parse_packet(self, data: bytes):
        """Packet parsing"""
        try:
            if len(data) < 32:
                raise ValueError("Data length is too short")
            
            if data[0] != ord('$'):
                raise ValueError("STX error!")
            
            # Interpret data_id as device_id (number → device_xxx format)
            device_num = int.from_bytes(data[1:3], 'big')
            device_id = f"device{device_num:03d}"  # device001, device002 format
            
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
            loc = self._geohash_decode(data[12:22])
            

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
            
            if (chk != int.from_bytes(self._checksum(data))):
                raise ValueError("Checksum error!") 
            
            if (data[31] != ord('\\')):
                raise ValueError("ETX error!")
            
            return {
                'DEVICE_ID': device_id,
                'ID': device_num,  # Keep original numeric ID (compatibility)
                'LEN': length,
                'TEMP': temp,
                'DO': do,
                'WTR_TEMP': wtr_temp,
                'LOC': loc,
                'TIME': f'{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}',
                'CHK': chk
            }
            
        except Exception as e:
            self._log(f"Packet parsing error: {e}", "error")
            return None