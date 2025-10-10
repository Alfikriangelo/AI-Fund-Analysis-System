# 문제 해결 가이드

## 프론트엔드 TypeScript 에러

### 증상
```
Cannot find module 'react' or its corresponding type declarations.
Cannot find module 'axios' or its corresponding type declarations.
Cannot find module '@tanstack/react-query' or its corresponding type declarations.
```

### 원인
`node_modules`가 설치되지 않았거나 의존성이 누락되었습니다.

### 해결방법

#### Docker 사용 시 (권장)
```bash
# Docker 컨테이너가 자동으로 의존성을 설치합니다
docker-compose up --build
```

#### 로컬 개발 시
```bash
cd frontend
npm install
npm run dev
```

---

## 백엔드 Python 에러

### 증상
```
ModuleNotFoundError: No module named 'numpy'
ModuleNotFoundError: No module named 'docling'
```

### 해결방법

#### Docker 사용 시 (권장)
```bash
docker-compose up --build
```

#### 로컬 개발 시
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 일반적인 에러 해결

### 1. "Cannot connect to database"

**원인**: PostgreSQL이 실행되지 않았거나 연결 정보가 잘못되었습니다.

**해결**:
```bash
# Docker로 PostgreSQL 시작
docker-compose up postgres -d

# 연결 확인
docker-compose exec postgres psql -U funduser -d funddb
```

### 2. "OpenAI API key not found"

**원인**: `.env` 파일에 API 키가 설정되지 않았습니다.

**해결**:
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 추가
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. "Port already in use"

**원인**: 포트가 이미 사용 중입니다.

**해결**:
```bash
# 사용 중인 프로세스 확인 (Mac/Linux)
lsof -i :8000  # 백엔드
lsof -i :3000  # 프론트엔드

# 프로세스 종료
kill -9 <PID>

# 또는 Docker 컨테이너 재시작
docker-compose down
docker-compose up
```

### 4. Lint 경고는 무시해도 됩니다

프로젝트는 정상적으로 실행됩니다. Lint 경고는 다음과 같은 이유로 발생합니다:

- **Frontend**: `npm install` 전에 TypeScript가 모듈을 찾을 수 없음
- **Backend**: `# noqa` 주석으로 의도적으로 무시된 import (SQLAlchemy 모델 등록용)

---

## 실행 확인

### 모든 서비스가 정상 실행되었는지 확인

```bash
# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 헬스 체크
curl http://localhost:8000/health
curl http://localhost:3000
```

### 정상 출력 예시
```
NAME                COMMAND                  SERVICE             STATUS
fund-backend        "sh -c 'python app/d…"   backend             Up
fund-frontend       "npm run dev"            frontend            Up
fund-postgres       "docker-entrypoint.s…"   postgres            Up (healthy)
fund-redis          "docker-entrypoint.s…"   redis               Up (healthy)
```

---

## 추가 도움말

문제가 계속되면:

1. **로그 확인**: `docker-compose logs [service-name]`
2. **컨테이너 재시작**: `docker-compose restart [service-name]`
3. **완전 재시작**: `docker-compose down && docker-compose up --build`
4. **볼륨 삭제** (데이터 손실 주의): `docker-compose down -v`

---

## 정상 작동 확인

프로젝트가 정상적으로 실행되면:

✅ Frontend: http://localhost:3000 접속 가능  
✅ Backend API: http://localhost:8000/docs 접속 가능  
✅ Health Check: `curl http://localhost:8000/health` 응답 정상  
✅ Database: PostgreSQL 연결 가능  
✅ Redis: Redis 연결 가능  

모든 서비스가 정상이면 문서 업로드 및 채팅 기능을 테스트할 수 있습니다.
