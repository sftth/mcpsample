## 기본정보
- 요구사항 아이디: req_20260306_001
- 프로젝트 명: 자산관리시스템 구축
- 발주기관: 한국자산관리개발원
- 수행사: LG CNS 컨소시엄
- 문서버전: Ver1.0
- 작성일자: 2026-03-07
- 작성자: Jacob
- 승인자: Jacob

## 비기능 요구사항
- 동시접속자: 5000
- RPS: 1000
- 피크 배수: 3.0
- 가용성: 99.9%
- 목표 응답시간(ms): 200

## 애플리케이션
- 타입: java_web
- 프레임워크: spring_boot
- WAR 파일: assetmanagement.war
- 컨텍스트 경로: /asset

## 인프라
- 클라우드: AWS
- OS: Amazon Linux 2
- 배포 방식: vm
- 서버 구성: AWS 기반 EC2
- Web Server 1 (Web1): IP 13.208.215.196, PEM /home/ec2-user/.ssh/jacob.park-keypair.pem, Account ec2-user
- Web Server 2 (Web2): IP 15.168.175.0, PEM /home/ec2-user/.ssh/jacob.park-keypair.pem, Account Ec2-user
- WAS 1 (WAS1): IP 13.208.215.196, PEM /home/ec2-user/.ssh/jacob.park-keypair.pem, Account ec2-user
- WAS 2 (WAS2): IP 15.168.175.0, PEM /home/ec2-user/.ssh/jacob.park-keypair.pem, Account Ec2-user
- Web Server: apache
- WAS: tomcat
- 연결방식: ajp
- Session Clustering: true
- 웹서버 대수: 2
- WAS 대수: 2
- 로드밸런서: AWS ALB
- SSL: true
- WAF: true
- IP 화이트리스트: false
- 기타: dev환경 필요 (web 1대, was 1대, spec 최소)

## 토폴로지
- 구성: apache
- 웹서버 대수: 2
- WAS 대수: 2
- 로드밸런서: AWS ALB

## 미들웨어
- Web Server: apache
- WAS: tomcat
- 연결방식: ajp
- session clustering: true

## 보안
- SSL: true
- WAF: true
- IP 화이트리스트: false

## 기타
- dev환경: 필요
- 개발환경 서버 구성: web 1대, was 1대
- 개발환경 서버 spec: 최소