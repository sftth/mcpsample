# 엔진 경로 생성
    - 계정 변경: sudo su
    - 경로 생성: mkdir /engn001
    - 권한 변경: chown midadm:midadm /engn001
    - 계정 복구: su - midadm

# 로그 경로 생성
    - 계정 변경: sudo su
    - 경로 생성: mkdir -p /logs001/apache/2.4.66/servers/webd-asc_80/logs
    - 권한 변경: chown -R midadm:midadm /logs001
    - 계정 원복: su - midadm

# 소스 경로 생성
    - 계정 변경: sudo su
    - 경로 생성: mkdir -p /sorc001/appadm/applications/htdocs
    - 권한 변경: chown -R midadm:midadm /sorc001
    - 계정 원복: su - midadm

# Apache 설치
    - 설치 경로: /engn001
    - apache-2.4.66.tar.gz를 "설치 경로"로 전송
    - "설치 경로"에서 apache-2.4.66.tar.gz 압축 해제

# setcap 설정
    - sudo setcap 'cap_net_bind_service=+ep' /engn001/apache/2.4.66/bin/httpd
    - getcap /engn001/apache/2.4.66/bin/httpd

# web 서버 시작
    - 경로: /engn001/apache/2.4.66/servers/webd-asc_80
    - "경로"의 start.sh 실행

# web 서버 기동 점검
    - 경로: /sorc001/appadm/applications/htdocs
    - "Test" 문자를 표출하는 index.html 생성 및 "경로"에 저장
    - curl 로 접속 테스트
