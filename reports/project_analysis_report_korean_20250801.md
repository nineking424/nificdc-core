# NiFi CDC Core 프로젝트 분석 보고서

## 요약

NiFi CDC Core 프로젝트는 Apache NiFi의 REST API를 활용하여 Change Data Capture (CDC) 파이프라인을 생성하고 관리하는 Python 기반 구현체입니다. 커스텀 NiFi 프로세서(NAR 파일)를 개발하는 대신, 이 프로젝트는 NiFi의 내장 프로세서들을 프로그래밍 방식으로 조율하여 CDC 기능을 구현합니다. 초기에는 Oracle 간 데이터베이스 복제에 중점을 두고 있으며, 향후 다양한 데이터베이스와 데이터 소스로 확장할 계획입니다.

## 프로젝트 아키텍처

### 기술 스택
- **프로그래밍 언어**: Python 3.6+
- **주요 의존성**:
  - `requests` (2.31.0) - NiFi API 통신을 위한 HTTP 라이브러리
  - `python-dotenv` (1.0.0) - 환경 변수 관리
  - `configparser` (6.0.0) - 설정 파일 파싱
- **테스트 프레임워크**: 포괄적인 커버리지 도구를 갖춘 pytest
- **외부 요구사항**: Apache NiFi 1.28 (별도 배포)

### 핵심 컴포넌트

#### 1. NiFi API 클라이언트 (`src/nifi_api_client.py`)
- NiFi REST API에 대한 Python 래퍼 제공
- Bearer 토큰 지원과 함께 사용자명/비밀번호를 통한 인증 처리
- 주요 기능:
  - 프로세스 그룹 생성 및 관리
  - 설정 가능한 속성을 가진 프로세서 인스턴스화
  - 컨트롤러 서비스 생성 (예: DBCPConnectionPool)
  - 프로세서 간 연결 설정
  - 프로세서 생명주기 관리 (시작/중지)

#### 2. 설정 파서 (`src/config_parser.py`)
- 환경 및 설정 파일 파싱 관리
- 데이터소스 및 매핑 구성을 위한 `.properties` 파일 읽기
- 데이터베이스 속성을 기반으로 JDBC URL 동적 생성
- `.env` 파일을 통한 환경 변수 로딩 지원

#### 3. CDC 플로우 빌더 (`src/cdc_flow_builder.py`)
- 완전한 CDC 파이프라인 생성 조율
- 각 CDC 플로우를 위한 전용 프로세스 그룹 생성
- 다음 NiFi 프로세서들을 인스턴스화하고 구성:
  - **ExecuteSQL**: CDC 조건을 적용하여 소스 데이터베이스에서 데이터 추출
  - **ConvertRecord**: Avro를 JSON 형식으로 변환
  - **ConvertJSONToSQL**: JSON을 SQL INSERT 문으로 변환
  - **PutSQL**: 대상 데이터베이스에 데이터 적재
  - **LogAttribute**: 오류 로깅 처리
- 적절한 오류 라우팅과 함께 프로세서 간 연결 설정

### 설정 구조

#### 환경 설정 (`.env`)
```
NIFI_API_BASE_URL=http://nifi-host:8080/nifi-api
NIFI_API_USERNAME=admin
NIFI_API_PASSWORD=password
NIFI_ROOT_PROCESS_GROUP_ID=root
NIFI_CDC_PROCESS_GROUP_NAME=CDC-Flows
```

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
cdc.incremental.from=2025-07-07 15:00:00
cdc.incremental.to=2025-07-07 16:00:00
```

## 주요 기능

### 1. API 중심 접근법
- 커스텀 NiFi 프로세서 개발 불필요
- REST API를 통해 NiFi의 내장 프로세서 활용
- 배포 및 유지보수 단순화

### 2. 설정 기반 CDC
- 속성 파일이 데이터 소스와 매핑 정의
- 타임스탬프 컬럼 기반 증분 CDC 지원
- 유연한 배치 크기 구성

### 3. 포괄적인 테스팅
- 100% 테스트 커버리지 요구사항
- 모의 의존성을 가진 단위 테스트
- 엔드투엔드 검증을 위한 통합 테스트
- 테스트 주도 개발(TDD) 방법론 적용

### 4. 오류 처리
- 각 프로세서에 대한 전용 오류 라우팅
- LogAttribute 프로세서를 통한 중앙화된 오류 로깅
- NiFi의 내장 기능을 통한 자동 재시도 메커니즘

## 개발 워크플로우

### 1. 설정
```bash
pip install -r requirements.txt
cp .env.example .env
# 환경 변수 구성
```

### 2. CDC 플로우 생성
```bash
python create_cdc_flow.py <mapping_name>
```

### 3. 테스팅
```bash
pytest --cov=src --cov-report=html
```

## 강점

1. **깔끔한 아키텍처**: 모듈화된 설계로 관심사의 명확한 분리
2. **API 우선 접근법**: 커스텀 NiFi 프로세서 개발의 복잡성 회피
3. **포괄적인 테스팅**: TDD 방법론을 통한 100% 코드 커버리지
4. **구성의 유연성**: 새로운 데이터 소스와 매핑 추가 용이
5. **프로덕션 준비된 오류 처리**: 적절한 오류 라우팅과 로깅

## 개선 가능 영역

1. **인증**: 현재 기본 인증 지원; 인증서 기반 인증 추가 가능
2. **데이터베이스 지원**: Oracle만 완전히 구현됨; PostgreSQL 등은 계획 중
3. **CDC 전략**: 현재 타임스탬프 기반; 지원되는 데이터베이스에 로그 기반 CDC 추가 가능
4. **모니터링**: 메트릭 수집 및 알림 기능 추가 가능
5. **플로우 템플릿**: 일반적인 CDC 패턴을 위한 재사용 가능한 템플릿 생성 가능

## 보안 고려사항

1. **자격 증명 관리**: 속성 파일에 평문으로 저장된 비밀번호
2. **API 보안**: NiFi의 보안 구성에 의존
3. **네트워크 보안**: 데이터베이스 연결을 위한 내장 암호화 없음

## 확장성 고려사항

1. **NiFi 클러스터링**: NiFi 클러스터를 지원하는 설계
2. **배치 처리**: 성능 튜닝을 위한 구성 가능한 배치 크기
3. **연결 풀링**: 효율적인 데이터베이스 연결을 위한 DBCPConnectionPool 사용
4. **백프레셔**: 적절한 임계값으로 구성 (1GB/10000 객체)

## 향후 로드맵

CLAUDE.md 문서를 기반으로 계획된 확장 사항:
1. 다중 데이터베이스 지원 (PostgreSQL, MySQL 등)
2. 추가 데이터 소스 (FTP, S3, Kafka, RabbitMQ, Redis)
3. 고급 CDC 전략 (로그 기반 복제)
4. 성능 모니터링 및 알림
5. 플로우 템플릿 라이브러리

## 결론

NiFi CDC Core 프로젝트는 CDC 파이프라인 구현에 대한 실용적인 접근법을 제시합니다. REST API를 통해 NiFi의 기존 기능을 활용함으로써, 이 프로젝트는 커스텀 프로세서 개발의 복잡성을 피하면서도 유연성과 확장성을 유지합니다. 테스팅과 구성 중심 설계에 대한 강한 강조는 신뢰성과 유지보수성이 중요한 프로덕션 환경에 적합하도록 만듭니다.