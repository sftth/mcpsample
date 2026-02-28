# A Project 요구사항 정의서

## 1. 개요

본 문서는 A Project 구축을 위한 Outer Architect에 관한 요구사항을 정의한 파일입니다.

## 2. 요구사항

### A. CI/CD

#### i. GitLab을 형상으로 사용한다

- 소스 코드 버전 관리 시스템으로 GitLab을 사용
- 형상 관리 및 협업 도구로 활용

#### ii. Jenkins를 사용하여 빌드,배포한다

- CI/CD 파이프라인 구축을 위해 Jenkins 사용
- 자동화된 빌드 및 배포 프로세스 구현

### B. Middleware

#### i. Frontend는 Apache 2.4 버전을 사용한다

- 웹 서버로 Apache HTTP Server 2.4 버전 사용
- 정적 파일 서빙 및 리버스 프록시 기능 활용

#### ii. Backend는 Tomcat을 사용한다

- Java 애플리케이션 서버로 Apache Tomcat 사용
- 서블릿 컨테이너 및 JSP 엔진 제공

### C. Monitoring

#### i. 모니터링은 Scouter를 통해 Backend 모니터링을 수행한다

- APM(Application Performance Monitoring) 도구로 Scouter 사용
- Backend 애플리케이션의 성능 모니터링 및 분석
- 실시간 모니터링 및 성능 지표 수집

---

## 기술 스택 요약

| 구분 | 기술 | 버전/설명 |
|------|------|-----------|
| 형상관리 | GitLab | 소스 코드 버전 관리 |
| CI/CD | Jenkins | 빌드 및 배포 자동화 |
| Frontend 서버 | Apache HTTP Server | 2.4 |
| Backend 서버 | Apache Tomcat | - |
| 모니터링 | Scouter | Backend APM |

## 아키텍처 구성도

```
[GitLab] 
    ↓
[Jenkins CI/CD]
    ↓
┌─────────────────────────────────┐
│  Frontend (Apache 2.4)          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  Backend (Tomcat)               │
│  ← [Scouter Monitoring]         │
└─────────────────────────────────┘
```

## 구현 고려사항

### CI/CD
- GitLab과 Jenkins 연동 설정
- 자동 빌드 트리거 구성
- 배포 파이프라인 정의

### Middleware
- Apache와 Tomcat 연동 (mod_jk 또는 mod_proxy_ajp)
- 로드 밸런싱 및 세션 클러스터링 고려
- SSL/TLS 인증서 설정

### Monitoring
- Scouter Agent 설치 및 구성
- Collector 서버 설정
- 모니터링 대시보드 구성
- 알림 및 임계값 설정
