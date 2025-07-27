# NiFi CDC Flow 사용 가이드

## 사전 준비

1. Python 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 설정:
```bash
cp .env.example .env
# .env 파일을 열어 NiFi API URL과 인증 정보 설정
```

3. 데이터베이스 설정:
```bash
# datasources 디렉토리에 데이터베이스 연결 정보 작성
# 예: datasources/testdb1.properties, datasources/testdb2.properties
```

4. CDC 매핑 설정:
```bash
# mappings 디렉토리에 CDC 매핑 정보 작성
# 예: mappings/testmapping.properties
```

## CDC Flow 생성

다음 명령어로 CDC flow를 생성합니다:

```bash
python create_cdc_flow.py testmapping
```

### 명령어 옵션

- `mapping`: 사용할 매핑 파일명 (mappings 폴더 내의 .properties 파일)
- `--base-path`: 설정 파일들의 기본 경로 (기본값: 현재 디렉토리)
- `--log-level`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)

### 예시

```bash
# 기본 실행
python create_cdc_flow.py testmapping

# 디버그 모드로 실행
python create_cdc_flow.py testmapping --log-level DEBUG

# 다른 경로의 설정 파일 사용
python create_cdc_flow.py testmapping --base-path /path/to/config
```

## 설정 파일 예시

### datasources/testdb1.properties
```properties
db.type=oracle
db.host=192.168.3.13
db.port=1521
db.service.name=ORCL
db.username=scott
db.password=tiger
db.schema=scott
```

### mappings/testmapping.properties
```properties
mapping.name=Test Oracle to Oracle CDC
source.datasource=testdb1
target.datasource=testdb2
source.table=SCOTT.EMP_1
target.table=SCOTT.EMP_2
cdc.mode=incremental
cdc.column=LAST_UPDATE_TIME
cdc.incremental.from=2025-07-07 15:00:00
cdc.incremental.to=2025-07-07 16:00:00
```

## 생성되는 NiFi Flow 구조

1. **Process Group**: CDC 작업을 위한 프로세스 그룹
2. **Controller Services**: 
   - 소스 DB 연결 풀 (DBCPConnectionPool)
   - 타겟 DB 연결 풀 (DBCPConnectionPool)
3. **Processors**:
   - ExecuteSQL: 소스 데이터 추출 (CDC 조건 적용)
   - ConvertAvroToJSON: Avro를 JSON으로 변환
   - ConvertJSONToSQL: JSON을 SQL로 변환
   - PutSQL: 타겟 DB에 데이터 적재
   - LogAttribute: 에러 로깅
4. **Connections**:
   - Success 관계: 정상 데이터 흐름
   - Failure 관계: 에러 처리 흐름

## 트러블슈팅

### NiFi API 연결 실패
- .env 파일의 NIFI_API_BASE_URL이 올바른지 확인
- NiFi가 실행 중인지 확인
- 방화벽 설정 확인
- 인증 정보 (username/password) 확인

### 데이터베이스 연결 실패
- datasources/*.properties 파일의 DB 연결 정보 확인
- Oracle JDBC 드라이버가 NiFi에 설치되어 있는지 확인
- 네트워크 연결 상태 확인
- 데이터베이스 사용자 권한 확인

### CDC 프로세서 생성 실패
- NiFi 버전이 1.28인지 확인
- 필요한 프로세서들이 NiFi에 설치되어 있는지 확인
- Process Group 생성 권한 확인

### 테스트 실행
```bash
# 전체 테스트 실행
pytest

# 상세 출력과 함께 실행
pytest -vv

# 커버리지 확인
pytest --cov=src --cov-report=term-missing
```