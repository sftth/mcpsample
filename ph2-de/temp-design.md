## 기본 정보
- request_id: req_20260306_001
- project_name: ecommerce-platform
 
## 요구사항
- 동시접속자: 5000
- RPS: 1000
- 피크 배수: 3.0
- 가용성: 99.9%
- 목표 응답시간(ms): 200
 
## 애플리케이션
- 타입: java_web
- 프레임워크: spring_boot
- WAR 파일: ecommerce.war
- 컨텍스트 경로: /shop
 
## 인프라
- 배포 방식: vm
- 클라우드: AWS
- OS: Amazon Linux 2
 
## 토폴로지
- 구성: web-was-separated
- 웹서버 대수: 2
- WAS 대수: 2
- 로드밸런서: AWS ALB
 
## 미들웨어
- 웹서버: apache
- WAS: tomcat
- 연결방식: ajp
- session_clustering: true
 
## 보안
- SSL: true
- WAF: true
- IP 화이트리스트: false
 
## 기타
- dev 환경: 필요 (web 1대, WAS 1대, spec 최소)