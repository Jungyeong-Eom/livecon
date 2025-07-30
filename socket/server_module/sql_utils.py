import pymysql

def connect_to_database(
    host_arg='localhost', 
    port_arg=3306, 
    user_arg='root', 
    password_arg='fnqwha2001', 
    db_arg='livecon_db', 
    charset_arg='utf8mb4'
):
    try:
        conn = pymysql.connect(
            host=host_arg,
            port=port_arg,
            user=user_arg,
            password=password_arg,
            database=db_arg,
            charset=charset_arg,
            cursorclass=pymysql.cursors.DictCursor  # 결과를 딕셔너리 형태로 반환
        )
        cursor = conn.cursor()
        return conn, cursor
    except pymysql.MySQLError as e:
        print(f"데이터베이스 연결 실패: {e}")
        return None, None

def database_query(query, params=None):
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return None

    try:
        cursor.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
        else:
            result = cursor.rowcount  # 영향받은 행 수 반환
        conn.commit()
        return result
    except pymysql.MySQLError as e:
        print(f"쿼리 실행 실패: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
def select_query(query, params=None):
    """
    SELECT 쿼리를 실행하고 결과를 반환
    :param query: SQL SELECT 쿼리
    :param params: 파라미터 튜플 (예: (id,))
    :return: 조회 결과 (리스트[딕셔너리])
    """
    conn, cursor = connect_to_database()
    if conn is None or cursor is None:
        return None
    try:
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    except pymysql.MySQLError as e:
        print(f"쿼리 실행 실패: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
        
def insert_sensor_results(parsed):
    """
    파싱된 센서 데이터를 데이터베이스에 저장
    :param parsed: 파싱된 센서 데이터 딕셔너리
    :return: INSERT 쿼리 문자열과 파라미터들
    """
    # 여러 센서 값을 개별 레코드로 저장
    queries = []
    
    # 온도 데이터
    temp_query = """
    INSERT INTO sensor_result
    (sensor_id, value_type_id, sensor_value, location, measured_at)
    VALUES (%s, %s, %s, %s, %s)
    """
    temp_params = (
        parsed['ID'],
        1,  # 온도 타입 ID
        parsed['TEMP'],
        f"{parsed['LOC'][0]:.6f},{parsed['LOC'][1]:.6f}",
        parsed['TIME']
    )
    
    # 용존산소 데이터  
    do_query = """
    INSERT INTO sensor_result
    (sensor_id, value_type_id, sensor_value, location, measured_at)
    VALUES (%s, %s, %s, %s, %s)
    """
    do_params = (
        parsed['ID'],
        2,  # 용존산소 타입 ID
        parsed['DO'],
        f"{parsed['LOC'][0]:.6f},{parsed['LOC'][1]:.6f}",
        parsed['TIME']
    )
    
    # 수온 데이터
    wtr_query = """
    INSERT INTO sensor_result
    (sensor_id, value_type_id, sensor_value, location, measured_at)
    VALUES (%s, %s, %s, %s, %s)
    """
    wtr_params = (
        parsed['ID'],
        3,  # 수온 타입 ID
        parsed['WTR_TEMP'],
        f"{parsed['LOC'][0]:.6f},{parsed['LOC'][1]:.6f}",
        parsed['TIME']
    )
    
    # 모든 쿼리 실행
    try:
        temp_result = database_query(temp_query, temp_params)
        do_result = database_query(do_query, do_params)
        wtr_result = database_query(wtr_query, wtr_params)
        
        # 모든 쿼리가 성공하면 성공으로 간주
        if temp_result is not None and do_result is not None and wtr_result is not None:
            return True
        else:
            return None
    except Exception as e:
        print(f"센서 데이터 저장 중 오류: {e}")
        return None