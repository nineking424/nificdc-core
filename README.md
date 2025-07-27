# NiFi CDC Core

Apache NiFi 기반 Change Data Capture (CDC) 구현을 위한 코어 프로젝트입니다.

## 프로젝트 개요

이 프로젝트는 NiFi API를 활용하여 다양한 데이터베이스와 데이터 소스 간의 CDC를 구현합니다. 초기에는 Oracle to Oracle CDC에 집중하며, 추후 PostgreSQL, Kafka, S3 등 다양한 소스로 확장할 예정입니다.

## 주요 기능

- NiFi REST API를 통한 프로그래밍 방식의 CDC 파이프라인 생성
- 다양한 데이터베이스 지원 (Oracle, PostgreSQL 등)
- 설정 파일 기반의 유연한 매핑 구성
- 자동화된 프로세서 생성 및 연결 관리
- 포괄적인 테스트 커버리지 (100%)

## 시작하기

### 사전 요구사항

- Apache NiFi 1.28 (외부 배포)
- Python 3.6 이상
- 소스/타겟 데이터베이스 접근 권한

### 설치 및 설정

1. 저장소 클론
```bash
git clone <repository-url>
cd nificdc-core
```

2. Python 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 설정
```bash
cp .env.example .env
# .env 파일을 열어 NiFi API 접속 정보 입력
```

4. 데이터베이스 및 매핑 설정
- `datasources/` 디렉토리에 데이터베이스 연결 정보 설정
- `mappings/` 디렉토리에 CDC 매핑 정보 설정

## 사용 방법

### CDC Flow 생성

```bash
python create_cdc_flow.py <mapping_name>

# 예시
python create_cdc_flow.py testmapping
```

### 설정 파일 구조

#### 데이터소스 설정 (`datasources/*.properties`)
```properties
db.type=oracle
db.host=192.168.3.13
db.port=1521
db.service.name=ORCL
db.username=scott
db.password=tiger
```

#### 매핑 설정 (`mappings/*.properties`)
```properties
mapping.name=Test Oracle to Oracle CDC
source.datasource=testdb1
target.datasource=testdb2
source.table=SCOTT.EMP_1
target.table=SCOTT.EMP_2
cdc.column=LAST_UPDATE_TIME
```

## 테스트

### 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 상세 출력
pytest -vv
```

### 테스트 구조
- `tests/unit/`: 단위 테스트
- `tests/integration/`: 통합 테스트  
- `tests/fixtures/`: 테스트 데이터

## 아키텍처

### 핵심 모듈

1. **NiFi API Client** (`src/nifi_api_client.py`)
   - NiFi REST API 래퍼
   - 인증 및 세션 관리
   - 프로세서/연결 생성

2. **Config Parser** (`src/config_parser.py`)
   - Properties 파일 파싱
   - 환경 변수 관리
   - JDBC URL 생성

3. **CDC Flow Builder** (`src/cdc_flow_builder.py`)
   - CDC 파이프라인 오케스트레이션
   - 프로세서 템플릿 관리
   - 연결 구성

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'feat: Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 라이선스

[라이선스 정보 추가 예정]