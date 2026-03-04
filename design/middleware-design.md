# Middleware 설계서

## 문서 정보
- **프로젝트명**: A Project
- **작성일**: 2026-03-03
- **버전**: 2.0
- **작성자**: System Architecture Team
- **최종 수정일**: 2026-03-03

---

## 1. 개요

본 문서는 A Project 구축을  위한 Middleware 아키텍처 설계를 정의합니다. 요구사항정의서(요구사항정의서-20260225.docx)에 명시된 Outer Architecture 요구사항을 기반으로 Frontend 및 Backend Middleware의 상세 설계를 포함합니다.

### 1.1 설계 기준 문서
- **요구사항정의서**: 요구사항정의서-20260225.docx
- **구현 가이드**: implementation/mw/setup-midadm.md
- **참조 이미지**: file/img/요구사항정의서-20260225_page_001.png

---

## 2. 요구사항 요약

### 2.1 Middleware 요구사항
- **Frontend**: Apache 2.4 버전 사용
- **Backend**: Tomcat 사용
- **CI/CD**: GitLab (형상관리) + Jenkins (빌드/배포)
- **Monitoring**: Scouter를 통한 Backend 모니터링

### 2.2 인프라 요구사항
- **클라우드 환경**: AWS EC2
- **운영체제**: Amazon Linux 2023
- **관리 계정**: midadm (비 root 계정 운영)

---

## 3. 시스템 아키텍처

### 3.1 전체 구성도

```
[Client] 
   ↓
[Apache 2.4.66] (Frontend - Port 80)
   ↓ (mod_proxy / mod_jk)
[Tomcat] (Backend - Port 8080)
   ↓
[Application]
   ↓
[Scouter Agent] → [Scouter Server] → [Scouter Client]
```

### 3.2 인프라 정보

#### 3.2.1 EC2 서버 정보
- **IP 주소**: 13.208.245.251
- **OS**: Amazon Linux 2023
- **기본 사용자**: ec2-user
- **PEM 키**: jacob.park-keypair.pem (경로: /Users/summit/.ssh/)
- **관리 계정**: midadm

#### 3.2.2 midadm 계정 정보
- **사용자명**: midadm
- **그룹**: midadm
- **비밀번호**: midadm
- **홈 디렉토리**: /home/midadm
- **용도**: Middleware 운영 전용 계정 (비 root 권한)

---

## 4. 계정 관리

### 4.1 midadm 계정 생성 절차

#### 4.1.1 사전 준비
1. ec2-user로 EC2 인스턴스 접속
2. root 권한 획득
   ```bash
   sudo su
   ```

#### 4.1.2 계정 생성 단계

**1단계: midadm 그룹 생성**
```bash
[root@ip-172-31-24-123 ec2-user]# groupadd midadm
```

**2단계: midadm 사용자 생성**
```bash
[root@ip-172-31-24-123 ec2-user]# useradd -m -g midadm midadm
```
- `-m`: 홈 디렉토리 자동 생성
- `-g midadm`: 기본 그룹을 midadm으로 설정

**3단계: 비밀번호 설정**
```bash
[root@ip-172-31-24-123 ec2-user]# passwd midadm
Changing password for user midadm.
New password: midadm
Retype new password: midadm
passwd: all authentication tokens updated successfully.
```

#### 4.1.3 계정 검증
```bash
# 계정 정보 확인
id midadm

# 출력 예시:
# uid=1001(midadm) gid=1001(midadm) groups=1001(midadm)

# 계정 전환 테스트
su - midadm
```

### 4.2 sudo 권한 설정 (선택사항)

특정 작업을 위해 midadm에 제한적인 sudo 권한 부여:

```bash
# visudo 편집
sudo visudo

# 다음 라인 추가
midadm ALL=(ALL) NOPASSWD: /usr/sbin/setcap, /usr/bin/systemctl
```

---

## 5. Apache 2.4.66 설계

### 5.1 설치 사양
- **버전**: Apache 2.4.66
- **설치 방식**: Source 컴파일 설치
- **포트**: 80 (HTTP), 443 (HTTPS - 선택)
- **실행 계정**: midadm (비 root)

### 5.2 디렉토리 구조

#### 5.2.1 표준 디렉토리 레이아웃

```
/engn001/apache/2.4.66/          # 엔진 경로
├── bin/                          # 실행 파일
│   ├── httpd                     # Apache 메인 실행 파일
│   ├── apachectl                 # 제어 스크립트
│   └── ...
├── conf/                         # 설정 파일
│   ├── httpd.conf               # 메인 설정
│   ├── extra/                   # 추가 설정
│   └── ...
├── modules/                      # 모듈
├── htdocs/                      # 기본 문서 루트 (사용 안 함)
└── ...

/logs001/apache/2.4.66/servers/webd-asc_80/logs/  # 로그 경로
├── access_log                    # 접근 로그
├── error_log                     # 에러 로그
├── mod_jk.log                   # mod_jk 로그 (연동 시)
└── ...

/sorc001/appadm/applications/htdocs/  # 소스 경로 (DocumentRoot)
├── index.html                    # 메인 페이지
├── static/                       # 정적 리소스
│   ├── css/
│   ├── js/
│   └── images/
└── ...
```

#### 5.2.2 디렉토리 소유권 및 권한

```bash
# 엔진 경로
sudo mkdir -p /engn001/apache/2.4.66
sudo chown -R midadm:midadm /engn001
sudo chmod -R 755 /engn001

# 로그 경로
sudo mkdir -p /logs001/apache/2.4.66/servers/webd-asc_80/logs
sudo chown -R midadm:midadm /logs001
sudo chmod -R 755 /logs001

# 소스 경로
sudo mkdir -p /sorc001/appadm/applications/htdocs
sudo chown -R midadm:midadm /sorc001
sudo chmod -R 755 /sorc001
```

### 5.3 비 root 계정 80 포트 바인딩 설정

#### 5.3.1 setcap 설정

Apache를 midadm 계정으로 실행하면서 80 포트를 사용하기 위한 설정:

```bash
# setcap 설정 (root 권한 필요)
sudo setcap 'cap_net_bind_service=+ep' /engn001/apache/2.4.66/bin/httpd
```

**설명**:
- `cap_net_bind_service`: 1024 이하 포트 바인딩 권한
- `+ep`: Effective와 Permitted 플래그 설정

#### 5.3.2 설정 검증

```bash
# setcap 설정 확인
getcap /engn001/apache/2.4.66/bin/httpd

# 출력 예시:
# /engn001/apache/2.4.66/bin/httpd = cap_net_bind_service+ep
```

#### 5.3.3 주의사항

- Apache 바이너리를 재설치하거나 업데이트하면 setcap 설정이 초기화됨
- 업데이트 후 반드시 setcap 재설정 필요
- 보안상 필요한 최소 권한만 부여

### 5.4 설치 절차

#### 5.4.1 사전 준비

**필수 패키지 설치**:
```bash
sudo yum update -y
sudo yum install -y gcc make apr-devel apr-util-devel pcre-devel openssl-devel
```

#### 5.4.2 Apache 설치

**1단계: 소스 파일 전송**
```bash
# 로컬에서 EC2로 파일 전송
scp -i /Users/summit/.ssh/jacob.park-keypair.pem \
    apache-2.4.66.tar.gz \
    ec2-user@13.208.245.251:/tmp/
```

**2단계: 압축 해제 및 컴파일**
```bash
# midadm 계정으로 전환
su - midadm

# 작업 디렉토리로 이동
cd /tmp

# 압축 해제
tar -xzf apache-2.4.66.tar.gz
cd httpd-2.4.66

# 컴파일 설정
./configure \
    --prefix=/engn001/apache/2.4.66 \
    --enable-so \
    --enable-ssl \
    --enable-proxy \
    --enable-proxy-http \
    --enable-proxy-ajp \
    --enable-rewrite \
    --enable-deflate \
    --enable-headers \
    --with-mpm=worker

# 컴파일 및 설치
make
make install
```

**3단계: 권한 설정**
```bash
# root로 전환하여 setcap 설정
sudo setcap 'cap_net_bind_service=+ep' /engn001/apache/2.4.66/bin/httpd

# 검증
getcap /engn001/apache/2.4.66/bin/httpd
```

### 5.5 주요 설정

#### 5.5.1 httpd.conf 기본 설정

```apache
# 서버 기본 설정
ServerRoot "/engn001/apache/2.4.66"
Listen 80
ServerAdmin admin@example.com
ServerName 13.208.245.251:80

# 사용자 및 그룹 (midadm 계정)
User midadm
Group midadm

# 로그 설정
ErrorLog "/logs001/apache/2.4.66/servers/webd-asc_80/logs/error_log"
CustomLog "/logs001/apache/2.4.66/servers/webd-asc_80/logs/access_log" combined

# 로그 레벨
LogLevel warn

# DocumentRoot
DocumentRoot "/sorc001/appadm/applications/htdocs"

# 디렉토리 권한
<Directory "/sorc001/appadm/applications/htdocs">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

# 기본 파일
<IfModule dir_module>
    DirectoryIndex index.html index.htm
</IfModule>

# 서버 정보 숨김 (보안)
ServerTokens Prod
ServerSignature Off
```

#### 5.5.2 Tomcat 연동 설정 (mod_proxy)

```apache
# mod_proxy 모듈 로드
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so

# 프록시 설정
<IfModule mod_proxy.c>
    ProxyRequests Off
    ProxyPreserveHost On
    
    <Proxy *>
        Require all granted
    </Proxy>
    
    # API 요청을 Tomcat으로 전달
    ProxyPass /api http://localhost:8080/api
    ProxyPassReverse /api http://localhost:8080/api
    
    # 애플리케이션 전체를 Tomcat으로 전달 (선택)
    # ProxyPass / http://localhost:8080/
    # ProxyPassReverse / http://localhost:8080/
</IfModule>
```

#### 5.5.3 성능 최적화 설정

```apache
# MPM Worker 설정
<IfModule mpm_worker_module>
    StartServers             2
    MinSpareThreads         25
    MaxSpareThreads         75
    ThreadsPerChild         25
    MaxRequestWorkers      150
    MaxConnectionsPerChild   0
</IfModule>

# KeepAlive 설정
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5

# 압축 설정
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript
</IfModule>
```

---

## 6. Tomcat 설계

### 6.1 설치 사양
- **버전**: Tomcat 9.0.x (권장)
- **설치 경로**: /engn001/tomcat/9.0.x
- **포트**: 8080 (HTTP), 8009 (AJP), 8005 (Shutdown)
- **실행 계정**: midadm

### 6.2 디렉토리 구조

```
/engn001/tomcat/9.0.x/           # 엔진 경로
├── bin/                          # 실행 스크립트
│   ├── startup.sh
│   ├── shutdown.sh
│   ├── catalina.sh
│   └── ...
├── conf/                         # 설정 파일
│   ├── server.xml
│   ├── web.xml
│   ├── context.xml
│   └── ...
├── webapps/                      # 애플리케이션 배포
│   ├── ROOT/
│   ├── manager/
│   └── [your-app]/
├── lib/                          # 라이브러리
├── temp/                         # 임시 파일
└── work/                         # 작업 디렉토리

/logs001/tomcat/9.0.x/servers/was-asc_8080/logs/  # 로그 경로
├── catalina.out                  # 표준 출력 로그
├── catalina.YYYY-MM-DD.log      # Catalina 로그
├── localhost.YYYY-MM-DD.log     # 호스트 로그
├── localhost_access_log.txt     # 접근 로그
└── ...
```

### 6.3 설치 절차

#### 6.3.1 Tomcat 다운로드 및 설치

```bash
# midadm 계정으로 작업
su - midadm

# Tomcat 다운로드
cd /tmp
wget https://dlcdn.apache.org/tomcat/tomcat-9/v9.0.x/bin/apache-tomcat-9.0.x.tar.gz

# 압축 해제
tar -xzf apache-tomcat-9.0.x.tar.gz

# 설치 디렉토리로 이동
sudo mv apache-tomcat-9.0.x /engn001/tomcat/9.0.x
sudo chown -R midadm:midadm /engn001/tomcat

# 실행 권한 부여
chmod +x /engn001/tomcat/9.0.x/bin/*.sh
```

#### 6.3.2 로그 디렉토리 설정

```bash
# 로그 디렉토리 생성
sudo mkdir -p /logs001/tomcat/9.0.x/servers/was-asc_8080/logs
sudo chown -R midadm:midadm /logs001/tomcat

# 심볼릭 링크 생성 (선택)
ln -s /logs001/tomcat/9.0.x/servers/was-asc_8080/logs /engn001/tomcat/9.0.x/logs
```

### 6.4 주요 설정

#### 6.4.1 server.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Server port="8005" shutdown="SHUTDOWN">
  
  <!-- 리스너 설정 -->
  <Listener className="org.apache.catalina.startup.VersionLoggerListener" />
  <Listener className="org.apache.catalina.core.AprLifecycleListener" SSLEngine="on" />
  <Listener className="org.apache.catalina.core.JreMemoryLeakPreventionListener" />
  <Listener className="org.apache.catalina.mbeans.GlobalResourcesLifecycleListener" />
  <Listener className="org.apache.catalina.core.ThreadLocalLeakPreventionListener" />

  <!-- 글로벌 리소스 -->
  <GlobalNamingResources>
    <Resource name="UserDatabase" auth="Container"
              type="org.apache.catalina.UserDatabase"
              description="User database that can be updated and saved"
              factory="org.apache.catalina.users.MemoryUserDatabaseFactory"
              pathname="conf/tomcat-users.xml" />
  </GlobalNamingResources>

  <!-- 서비스 정의 -->
  <Service name="Catalina">

    <!-- HTTP Connector -->
    <Connector port="8080" protocol="HTTP/1.1"
               connectionTimeout="20000"
               redirectPort="8443"
               maxThreads="200"
               minSpareThreads="10"
               acceptCount="100"
               enableLookups="false"
               compression="on"
               compressionMinSize="2048"
               noCompressionUserAgents="gozilla, traviata"
               compressibleMimeType="text/html,text/xml,text/plain,text/css,text/javascript,application/javascript,application/json" />

    <!-- AJP Connector (Apache 연동용) -->
    <Connector port="8009" protocol="AJP/1.3"
               redirectPort="8443"
               secretRequired="false" />

    <!-- 엔진 설정 -->
    <Engine name="Catalina" defaultHost="localhost">

      <Realm className="org.apache.catalina.realm.LockOutRealm">
        <Realm className="org.apache.catalina.realm.UserDatabaseRealm"
               resourceName="UserDatabase"/>
      </Realm>

      <!-- 호스트 설정 -->
      <Host name="localhost" appBase="webapps"
            unpackWARs="true" autoDeploy="true">

        <!-- 접근 로그 -->
        <Valve className="org.apache.catalina.valves.AccessLogValve"
               directory="/logs001/tomcat/9.0.x/servers/was-asc_8080/logs"
               prefix="localhost_access_log" suffix=".txt"
               pattern="%h %l %u %t &quot;%r&quot; %s %b" />

      </Host>
    </Engine>
  </Service>
</Server>
```

#### 6.4.2 catalina.sh (JVM 옵션)

```bash
# JAVA_OPTS 설정
JAVA_OPTS="$JAVA_OPTS -Djava.awt.headless=true"
JAVA_OPTS="$JAVA_OPTS -Dfile.encoding=UTF-8"
JAVA_OPTS="$JAVA_OPTS -server"

# 메모리 설정
JAVA_OPTS="$JAVA_OPTS -Xms2048m -Xmx2048m"
JAVA_OPTS="$JAVA_OPTS -XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=512m"

# GC 설정
JAVA_OPTS="$JAVA_OPTS -XX:+UseG1GC"
JAVA_OPTS="$JAVA_OPTS -XX:MaxGCPauseMillis=200"
JAVA_OPTS="$JAVA_OPTS -XX:+PrintGCDetails"
JAVA_OPTS="$JAVA_OPTS -XX:+PrintGCDateStamps"
JAVA_OPTS="$JAVA_OPTS -Xloggc:/logs001/tomcat/9.0.x/servers/was-asc_8080/logs/gc.log"

# HeapDump 설정
JAVA_OPTS="$JAVA_OPTS -XX:+HeapDumpOnOutOfMemoryError"
JAVA_OPTS="$JAVA_OPTS -XX:HeapDumpPath=/logs001/tomcat/9.0.x/servers/was-asc_8080/logs/heapdump"

# Scouter Agent 설정 (모니터링)
JAVA_OPTS="$JAVA_OPTS -javaagent:/engn001/scouter/agent.java/scouter.agent.jar"
JAVA_OPTS="$JAVA_OPTS -Dscouter.config=/engn001/scouter/agent.java/conf/scouter.conf"
JAVA_OPTS="$JAVA_OPTS -Dobj_name=was-asc_8080"

# 로그 디렉토리 설정
CATALINA_OUT=/logs001/tomcat/9.0.x/servers/was-asc_8080/logs/catalina.out
```

---

## 7. Apache-Tomcat 연동

### 7.1 연동 방식 비교

| 구분 | mod_proxy | mod_jk |
|------|-----------|--------|
| 프로토콜 | HTTP | AJP |
| 설정 복잡도 | 간단 | 중간 |
| 성능 | 보통 | 우수 |
| 세션 클러스터링 | 제한적 | 우수 |
| 권장 사용 | 단순 구성 | 프로덕션 환경 |

### 7.2 mod_proxy 연동 (권장 - 간단한 구성)

#### 7.2.1 Apache 설정

```apache
# httpd.conf에 추가

# 모듈 로드
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so

# 프록시 설정
<IfModule mod_proxy.c>
    ProxyRequests Off
    ProxyPreserveHost On
    ProxyTimeout 300
    
    <Proxy *>
        Require all granted
    </Proxy>
    
    # API 요청 프록시
    ProxyPass /api http://localhost:8080/api retry=0 timeout=300
    ProxyPassReverse /api http://localhost:8080/api
    
    # 정적 리소스는 Apache에서 직접 처리
    ProxyPass /static !
    
    # 나머지 요청은 Tomcat으로
    ProxyPass / http://localhost:8080/ retry=0 timeout=300
    ProxyPassReverse / http://localhost:8080/
</IfModule>
```

### 7.3 mod_jk 연동 (고급 - 프로덕션 환경)

#### 7.3.1 mod_jk 설치

```bash
# mod_jk 다운로드
cd /tmp
wget https://dlcdn.apache.org/tomcat/tomcat-connectors/jk/tomcat-connectors-1.2.x-src.tar.gz

# 압축 해제 및 컴파일
tar -xzf tomcat-connectors-1.2.x-src.tar.gz
cd tomcat-connectors-1.2.x-src/native

./configure --with-apxs=/engn001/apache/2.4.66/bin/apxs
make
sudo make install
```

#### 7.3.2 workers.properties

```properties
# /engn001/apache/2.4.66/conf/workers.properties

# Worker 리스트
worker.list=worker1

# Worker 설정
worker.worker1.type=ajp13
worker.worker1.host=localhost
worker.worker1.port=8009
worker.worker1.lbfactor=1
worker.worker1.connection_pool_size=200
worker.worker1.connection_pool_timeout=600
```

#### 7.3.3 Apache httpd.conf

```apache
# mod_jk 모듈 로드
LoadModule jk_module modules/mod_jk.so

# mod_jk 설정
JkWorkersFile /engn001/apache/2.4.66/conf/workers.properties
JkLogFile /logs001/apache/2.4.66/servers/webd-asc_80/logs/mod_jk.log
JkLogLevel info
JkLogStampFormat "[%a %b %d %H:%M:%S %Y]"

# URL 매핑
JkMount /api/* worker1
JkMount /*.jsp worker1
JkMount /servlet/* worker1

# 정적 리소스 제외
JkUnMount /static/* worker1
```

---

## 8. 모니터링 설계 (Scouter)

### 8.1 Scouter 아키텍처

```
[Tomcat + Scouter Agent] → [Scouter Server] → [Scouter Client]
                                    ↓
                            [Data Storage]
```

### 8.2 Scouter 설치

#### 8.2.1 Scouter Server 설치

```bash
# Scouter 다운로드
cd /tmp
wget https://github.com/scouter-project/scouter/releases/download/v2.x.x/scouter-all-2.x.x.tar.gz

# 압축 해제
tar -xzf scouter-all-2.x.x.tar.gz

# 설치
sudo mv scouter /engn001/
sudo chown -R midadm:midadm /engn001/scouter
```

#### 8.2.2 Scouter Server 설정

```properties
# /engn001/scouter/server/conf/scouter.conf

# 네트워크 설정
net_tcp_listen_port=6100
net_udp_listen_port=6100
net_http_port=6180

# 데이터 보관 설정
mgr_purge_profile_keep_days=10
mgr_purge_xlog_keep_days=30
mgr_purge_counter_keep_days=70

# 로그 설정
log_dir=/logs001/scouter/server
log_rotation_enabled=true
log_keep_days=30
```

#### 8.2.3 Scouter Agent 설정

```properties
# /engn001/scouter/agent.java/conf/scouter.conf

# 서버 연결 설정
net_collector_ip=127.0.0.1
net_collector_udp_port=6100
net_collector_tcp_port=6100

# 객체 설정
obj_name=was-asc_8080
obj_type=tomcat

# 프로파일링 설정
profile_http_querystring_enabled=true
profile_http_header_enabled=true
profile_spring_controller_enabled=true
profile_sql_escape_enabled=true

# 알림 설정
alert_perm_warning_pct=90
alert_message_length=3000
```

### 8.3 Scouter 실행

#### 8.3.1 Scouter Server 시작

```bash
# midadm 계정으로 실행
cd /engn001/scouter/server
./startup.sh

# 로그 확인
tail -f /logs001/scouter/server/scouter.log
```

#### 8.3.2 Tomcat에 Agent 적용

catalina.sh에 이미 설정되어 있음:
```bash
JAVA_OPTS="$JAVA_OPTS -javaagent:/engn001/scouter/agent.java/scouter.agent.jar"
JAVA_OPTS="$JAVA_OPTS -Dscouter.config=/engn001/scouter/agent.java/conf/scouter.conf"
JAVA_OPTS="$JAVA_OPTS -Dobj_name=was-asc_8080"
```

### 8.4 모니터링 항목

#### 8.4.1 시스템 메트릭
- CPU 사용률
- 메모리 사용률 (Heap, Non-Heap)
- GC 횟수 및 시간
- Thread 수

#### 8.4.2 애플리케이션 메트릭
- TPS (Transaction Per Second)
- 응답 시간 (평균, 최대)
- 활성 서비스 수
- SQL 실행 시간

#### 8.4.3 알림 설정
- CPU 사용률 90% 이상
- 메모리 사용률 90% 이상
- 응답 시간 3초 이상
- 에러율 5% 이상

---

## 9. CI/CD 파이프라인

### 9.1 GitLab 형상관리

#### 9.1.1 Repository 구조

```
project-root/
├── src/                          # 소스 코드
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   │   └── webapp/
│   └── test/
├── config/                       # 설정 파일
│   ├── dev/
│   ├── staging/
│   └── prod/
├── scripts/                      # 배포 스크립트
│   ├── deploy.sh
│   └── rollback.sh
├── Jenkinsfile                   # Jenkins 파이프라인
├── pom.xml                       # Maven 설정
└── README.md
```

### 9.2 Jenkins 파이프라인

#### 9.2.1 Jenkinsfile

```groovy
pipeline {
    agent any
    
    environment {
        DEPLOY_SERVER = '13.208.245.251'
        DEPLOY_USER = 'midadm'
        TOMCAT_HOME = '/engn001/tomcat/9.0.x'
        APP_NAME = 'myapp'
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'gitlab-credentials',
                    url: 'https://gitlab.example.com/project.git'
            }
        }
        
        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }
        
        stage('Test') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    junit '**/target/surefire-reports/*.xml'
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    // WAR 파일 전송
                    sh """
                        scp -i ~/.ssh/jacob.park-keypair.pem \
                            target/${APP_NAME}.war \
                            ${DEPLOY_USER}@${DEPLOY_SERVER}:${TOMCAT_HOME}/webapps/
                    """
                    
                    // Tomcat 재시작
                    sh """
                        ssh -i ~/.ssh/jacob.park-keypair.pem \
                            ${DEPLOY_USER}@${DEPLOY_SERVER} \
                            '${TOMCAT_HOME}/bin/shutdown.sh && \
                             sleep 10 && \
                             ${TOMCAT_HOME}/bin/startup.sh'
                    """
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    sleep 30
                    sh """
                        curl -f http://${DEPLOY_SERVER}:8080/${APP_NAME}/health || exit 1
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed!'
            // 롤백 스크립트 실행
            sh """
                ssh -i ~/.ssh/jacob.park-keypair.pem \
                    ${DEPLOY_USER}@${DEPLOY_SERVER} \
                    '/sorc001/scripts/rollback.sh'
            """
        }
    }
}
```

#### 9.2.2 배포 스크립트

```bash
#!/bin/bash
# /sorc001/scripts/deploy.sh

APP_NAME="myapp"
TOMCAT_HOME="/engn001/tomcat/9.0.x"
BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"

# 백업
mkdir -p $BACKUP_DIR
cp $TOMCAT_HOME/webapps/${APP_NAME}.war $BACKUP_DIR/

# Tomcat 중지
$TOMCAT_HOME/bin/shutdown.sh
sleep 10

# 기존 애플리케이션 삭제
rm -rf $TOMCAT_HOME/webapps/${APP_NAME}
rm -f $TOMCAT_HOME/webapps/${APP_NAME}.war

# 새 애플리케이션 배포
cp /tmp/${APP_NAME}.war $TOMCAT_HOME/webapps/

# Tomcat 시작
$TOMCAT_HOME/bin/startup.sh

# 로그 확인
tail -f /logs001/tomcat/9.0.x/servers/was-asc_8080/logs/catalina.out
```

---

## 10. 보안 설계

### 10.1 Apache 보안 설정

```apache
# httpd.conf 보안 설정

# 서버 정보 숨김
ServerTokens Prod
ServerSignature Off

# 디렉토리 리스팅 비활성화
<Directory />
    Options -Indexes
    AllowOverride None
    Require all denied
</Directory>

# HTTP 메서드 제한
<LimitExcept GET POST HEAD>
    Require all denied
</LimitExcept>

# 보안 헤더
Header always set X-Frame-Options "SAMEORIGIN"
Header always set X-Content-Type-Options "nosniff"
Header always set X-XSS-Protection "1; mode=block"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

# 파일 업로드 크기 제한
LimitRequestBody 10485760

# Timeout 설정
Timeout 60
```

### 10.2 Tomcat 보안 설정

#### 10.2.1 server.xml

```xml
<!-- 불필요한 커넥터 제거 -->
<!-- Shutdown 포트 변경 -->
<Server port="8005" shutdown="SHUTDOWN_CUSTOM">

<!-- 에러 페이지에서 버전 정보 숨김 -->
<Connector port="8080" protocol="HTTP/1.1"
           server="Apache"
           xpoweredBy="false" />
```

#### 10.2.2 web.xml

```xml
<!-- 세션 타임아웃 -->
<session-config>
    <session-timeout>30</session-timeout>
    <cookie-config>
        <http-only>true</http-only>
        <secure>true</secure>
    </cookie-config>
</session-config>

<!-- 에러 페이지 -->
<error-page>
    <error-code>404</error-code>
    <location>/error/404.html</location>
</error-page>
<error-page>
    <error-code>500</error-code>
    <location>/error/500.html</location>
</error-page>
```

### 10.3 방화벽 설정

```bash
# firewalld 설정
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=6100/tcp  # Scouter
sudo firewall-cmd --reload

# 방화벽 규칙 확인
sudo firewall-cmd --list-all
```

### 10.4 SSL/TLS 설정 (HTTPS)

#### 10.4.1 인증서 생성 (자체 서명)

```bash
# 개발/테스트용 자체 서명 인증서
openssl req -new -x509 -days 365 -nodes \
    -out /engn001/apache/2.4.66/conf/server.crt \
    -keyout /engn001/apache/2.4.66/conf/server.key
```

#### 10.4.2 Apache SSL 설정

```apache
# httpd-ssl.conf

Listen 443

<VirtualHost *:443>
    ServerName 13.208.245.251:443
    
    SSLEngine on
    SSLCertificateFile /engn001/apache/2.4.66/conf/server.crt
    SSLCertificateKeyFile /engn001/apache/2.4.66/conf/server.key
    
    # SSL 프로토콜 설정
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5
    
    DocumentRoot "/sorc001/appadm/applications/htdocs"
    
    <Directory "/sorc001/appadm/applications/htdocs">
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

---

## 11. 백업 및 복구

### 11.1 백업 전략

#### 11.1.1 백업 대상
- **설정 파일**: Apache, Tomcat 설정
- **애플리케이션**: WAR/JAR 파일
- **로그**: 최근 30일 로그
- **데이터**: 애플리케이션 데이터 (별도 DB 백업)

#### 11.1.2 백업 주기
- **일일 백업**: 설정 파일, 애플리케이션
- **주간 백업**: 전체 시스템 백업
- **월간 백업**: 장기 보관용 백업

### 11.2 백업 스크립트

```bash
#!/bin/bash
# /sorc001/scripts/backup.sh

BACKUP_BASE="/backup"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/${BACKUP_DATE}"

# 백업 디렉토리 생성
mkdir -p ${BACKUP_DIR}

# Apache 설정 백업
tar -czf ${BACKUP_DIR}/apache-conf.tar.gz \
    /engn001/apache/2.4.66/conf/

# Tomcat 설정 백업
tar -czf ${BACKUP_DIR}/tomcat-conf.tar.gz \
    /engn001/tomcat/9.0.x/conf/

# 애플리케이션 백업
tar -czf ${BACKUP_DIR}/webapps.tar.gz \
    /engn001/tomcat/9.0.x/webapps/

# 로그 백업 (최근 7일)
find /logs001 -name "*.log" -mtime -7 -exec tar -czf ${BACKUP_DIR}/logs.tar.gz {} +

# 오래된 백업 삭제 (30일 이상)
find ${BACKUP_BASE} -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: ${BACKUP_DIR}"
```

### 11.3 복구 절차

```bash
#!/bin/bash
# /sorc001/scripts/restore.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

# Tomcat 중지
/engn001/tomcat/9.0.x/bin/shutdown.sh
sleep 10

# Apache 중지
/engn001/apache/2.4.66/bin/apachectl stop

# 설정 복구
tar -xzf ${BACKUP_DIR}/apache-conf.tar.gz -C /
tar -xzf ${BACKUP_DIR}/tomcat-conf.tar.gz -C /

# 애플리케이션 복구
tar -xzf ${BACKUP_DIR}/webapps.tar.gz -C /

# 서비스 시작
/engn001/apache/2.4.66/bin/apachectl start
/engn001/tomcat/9.0.x/bin/startup.sh

echo "Restore completed from: ${BACKUP_DIR}"
```

### 11.4 Cron 설정

```bash
# crontab -e (midadm 계정)

# 매일 새벽 2시 백업
0 2 * * * /sorc001/scripts/backup.sh >> /logs001/backup/backup.log 2>&1

# 매주 일요일 새벽 3시 전체 백업
0 3 * * 0 /sorc001/scripts/full-backup.sh >> /logs001/backup/full-backup.log 2>&1
```

---

## 12. 성능 튜닝

### 12.1 Apache 성능 최적화

#### 12.1.1 MPM Worker 튜닝

```apache
<IfModule mpm_worker_module>
    # 서버 시작 시 프로세스 수
    StartServers             3
    
    # 최소/최대 유휴 스레드
    MinSpareThreads         75
    MaxSpareThreads        250
    
    # 자식 프로세스당 스레드 수
    ThreadsPerChild         25
    
    # 최대 동시 요청 수
    MaxRequestWorkers      400
    
    # 자식 프로세스 재시작 주기 (메모리 누수 방지)
    MaxConnectionsPerChild 10000
</IfModule>
```

#### 12.1.2 캐싱 설정

```apache
# mod_cache 활성화
LoadModule cache_module modules/mod_cache.so
LoadModule cache_disk_module modules/mod_cache_disk.so

<IfModule mod_cache.c>
    CacheEnable disk /
    CacheRoot /var/cache/apache2/mod_cache_disk
    CacheDefaultExpire 3600
    CacheMaxExpire 86400
    CacheIgnoreHeaders Set-Cookie
</IfModule>

# 정적 리소스 캐싱
<FilesMatch "\.(jpg|jpeg|png|gif|css|js|ico)$">
    Header set Cache-Control "max-age=2592000, public"
</FilesMatch>
```

### 12.2 Tomcat 성능 최적화

#### 12.2.1 Connector 튜닝

```xml
<Connector port="8080" protocol="HTTP/1.1"
           connectionTimeout="20000"
           maxThreads="400"
           minSpareThreads="25"
           maxSpareThreads="75"
           acceptCount="200"
           enableLookups="false"
           disableUploadTimeout="true"
           compression="on"
           compressionMinSize="2048"
           noCompressionUserAgents="gozilla, traviata"
           compressibleMimeType="text/html,text/xml,text/plain,text/css,text/javascript,application/javascript,application/json" />
```

#### 12.2.2 JVM 튜닝

```bash
# catalina.sh

# 힙 메모리 (서버 메모리의 50-70%)
JAVA_OPTS="$JAVA_OPTS -Xms4096m -Xmx4096m"

# Metaspace (클래스 메타데이터)
JAVA_OPTS="$JAVA_OPTS -XX:MetaspaceSize=512m -XX:MaxMetaspaceSize=1024m"

# G1GC 사용 (Java 9+)
JAVA_OPTS="$JAVA_OPTS -XX:+UseG1GC"
JAVA_OPTS="$JAVA_OPTS -XX:MaxGCPauseMillis=200"
JAVA_OPTS="$JAVA_OPTS -XX:ParallelGCThreads=8"
JAVA_OPTS="$JAVA_OPTS -XX:ConcGCThreads=2"
JAVA_OPTS="$JAVA_OPTS -XX:InitiatingHeapOccupancyPercent=45"

# GC 로깅
JAVA_OPTS="$JAVA_OPTS -Xlog:gc*:file=/logs001/tomcat/9.0.x/servers/was-asc_8080/logs/gc.log:time,uptime,level,tags"
JAVA_OPTS="$JAVA_OPTS -XX:+UseGCLogFileRotation"
JAVA_OPTS="$JAVA_OPTS -XX:NumberOfGCLogFiles=10"
JAVA_OPTS="$JAVA_OPTS -XX:GCLogFileSize=100M"

# 성능 모니터링
JAVA_OPTS="$JAVA_OPTS -XX:+PrintGCDetails"
JAVA_OPTS="$JAVA_OPTS -XX:+PrintGCDateStamps"
JAVA_OPTS="$JAVA_OPTS -XX:+PrintHeapAtGC"
JAVA_OPTS="$JAVA_OPTS -XX:+PrintTenuringDistribution"

# OOM 시 힙 덤프
JAVA_OPTS="$JAVA_OPTS -XX:+HeapDumpOnOutOfMemoryError"
JAVA_OPTS="$JAVA_OPTS -XX:HeapDumpPath=/logs001/tomcat/9.0.x/servers/was-asc_8080/logs/heapdump"

# JMX 모니터링 (선택)
JAVA_OPTS="$JAVA_OPTS -Dcom.sun.management.jmxremote"
JAVA_OPTS="$JAVA_OPTS -Dcom.sun.management.jmxremote.port=9999"
JAVA_OPTS="$JAVA_OPTS -Dcom.sun.management.jmxremote.ssl=false"
JAVA_OPTS="$JAVA_OPTS -Dcom.sun.management.jmxremote.authenticate=false"
```

### 12.3 OS 레벨 튜닝

#### 12.3.1 파일 디스크립터 제한

```bash
# /etc/security/limits.conf

midadm soft nofile 65536
midadm hard nofile 65536
midadm soft nproc 4096
midadm hard nproc 4096
```

#### 12.3.2 커널 파라미터

```bash
# /etc/sysctl.conf

# TCP 설정
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_tw_reuse = 1
net.core.somaxconn = 4096
net.core.netdev_max_backlog = 5000

# 메모리 설정
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 적용
sudo sysctl -p
```

---

## 13. 운영 가이드

### 13.1 서비스 시작/중지

#### 13.1.1 Apache 운영

```bash
# midadm 계정으로 실행

# 시작
/engn001/apache/2.4.66/bin/apachectl start

# 중지
/engn001/apache/2.4.66/bin/apachectl stop

# 재시작
/engn001/apache/2.4.66/bin/apachectl restart

# Graceful 재시작 (연결 유지)
/engn001/apache/2.4.66/bin/apachectl graceful

# 설정 검증
/engn001/apache/2.4.66/bin/apachectl configtest

# 상태 확인
/engn001/apache/2.4.66/bin/apachectl status

# 프로세스 확인
ps -ef | grep httpd
```

#### 13.1.2 Tomcat 운영

```bash
# midadm 계정으로 실행

# 시작
/engn001/tomcat/9.0.x/bin/startup.sh

# 중지
/engn001/tomcat/9.0.x/bin/shutdown.sh

# 강제 종료 (shutdown이 안 될 때)
ps -ef | grep tomcat | grep -v grep | awk '{print $2}' | xargs kill -9

# 로그 실시간 확인
tail -f /logs001/tomcat/9.0.x/servers/was-asc_8080/logs/catalina.out

# 프로세스 확인
ps -ef | grep tomcat
```

### 13.2 로그 관리

#### 13.2.1 로그 확인

```bash
# Apache 접근 로그
tail -f /logs001/apache/2.4.66/servers/webd-asc_80/logs/access_log

# Apache 에러 로그
tail -f /logs001/apache/2.4.66/servers/webd-asc_80/logs/error_log

# Tomcat 로그
tail -f /logs001/tomcat/9.0.x/servers/was-asc_8080/logs/catalina.out

# 특정 에러 검색
grep "ERROR" /logs001/tomcat/9.0.x/servers/was-asc_8080/logs/catalina.out

# 최근 100줄 확인
tail -100 /logs001/apache/2.4.66/servers/webd-asc_80/logs/error_log
```

#### 13.2.2 로그 로테이션

```bash
# /etc/logrotate.d/apache

/logs001/apache/2.4.66/servers/webd-asc_80/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 midadm midadm
    sharedscripts
    postrotate
        /engn001/apache/2.4.66/bin/apachectl graceful > /dev/null 2>&1 || true
    endscript
}
```

```bash
# /etc/logrotate.d/tomcat

/logs001/tomcat/9.0.x/servers/was-asc_8080/logs/catalina.out {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 midadm midadm
    copytruncate
}
```

### 13.3 모니터링

#### 13.3.1 시스템 리소스 확인

```bash
# CPU 사용률
top -u midadm

# 메모리 사용률
free -h

# 디스크 사용률
df -h

# 네트워크 연결 상태
netstat -tulpn | grep -E '80|8080|8009'

# 프로세스별 메모리 사용
ps aux --sort=-%mem | head -10
```

#### 13.3.2 애플리케이션 상태 확인

```bash
# Apache 상태
curl http://localhost/server-status

# Tomcat 상태 (Manager 앱 필요)
curl http://localhost:8080/manager/status

# 헬스 체크
curl http://localhost:8080/health
```

### 13.4 일상 점검 체크리스트

#### 13.4.1 일일 점검
- [ ] 서비스 프로세스 정상 동작 확인
- [ ] 로그 에러 확인
- [ ] 디스크 사용률 확인 (80% 이하)
- [ ] CPU/메모리 사용률 확인
- [ ] 백업 정상 수행 확인

#### 13.4.2 주간 점검
- [ ] 로그 파일 정리
- [ ] 성능 지표 분석 (Scouter)
- [ ] 보안 패치 확인
- [ ] 백업 파일 검증

#### 13.4.3 월간 점검
- [ ] 전체 시스템 백업
- [ ] 성능 튜닝 검토
- [ ] 용량 계획 검토
- [ ] 보안 감사

---

## 14. 트러블슈팅

### 14.1 Apache 문제 해결

#### 14.1.1 80 포트 바인딩 실패

**증상**:
```
(13)Permission denied: AH00072: make_sock: could not bind to address [::]:80
```

**원인**: setcap 설정 누락 또는 초기화

**해결**:
```bash
# setcap 재설정
sudo setcap 'cap_net_bind_service=+ep' /engn001/apache/2.4.66/bin/httpd

# 검증
getcap /engn001/apache/2.4.66/bin/httpd

# Apache 재시작
/engn001/apache/2.4.66/bin/apachectl restart
```

#### 14.1.2 설정 파일 오류

**증상**:
```
Syntax error on line XX of /engn001/apache/2.4.66/conf/httpd.conf
```

**해결**:
```bash
# 설정 검증
/engn001/apache/2.4.66/bin/apachectl configtest

# 백업에서 복구
cp /backup/latest/apache-conf.tar.gz /tmp/
tar -xzf /tmp/apache-conf.tar.gz -C /
```

#### 14.1.3 프록시 연결 실패

**증상**: 502 Bad Gateway

**원인**: Tomcat 미실행 또는 포트 불일치

**해결**:
```bash
# Tomcat 상태 확인
ps -ef | grep tomcat

# 포트 확인
netstat -tulpn | grep 8080

# Tomcat 시작
/engn001/tomcat/9.0.x/bin/startup.sh

# 로그 확인
tail -f /logs001/apache/2.4.66/servers/webd-asc_80/logs/error_log
```

### 14.2 Tomcat 문제 해결

#### 14.2.1 OutOfMemoryError

**증상**:
```
java.lang.OutOfMemoryError: Java heap space
```

**원인**: JVM 힙 메모리 부족

**해결**:
```bash
# catalina.sh 수정
vi /engn001/tomcat/9.0.x/bin/catalina.sh

# 메모리 증가
JAVA_OPTS="$JAVA_OPTS -Xms4096m -Xmx4096m"

# Tomcat 재시작
/engn001/tomcat/9.0.x/bin/shutdown.sh
/engn001/tomcat/9.0.x/bin/startup.sh

# 힙 덤프 분석
jhat /logs001/tomcat/9.0.x/servers/was-asc_8080/logs/heapdump/java_pid*.hprof
```

#### 14.2.2 포트 충돌

**증상**:
```
Address already in use
```

**원인**: 다른 프로세스가 포트 사용 중

**해결**:
```bash
# 포트 사용 프로세스 확인
lsof -i :8080

# 프로세스 종료
kill -9 <PID>

# Tomcat 재시작
/engn001/tomcat/9.0.x/bin/startup.sh
```

#### 14.2.3 애플리케이션 배포 실패

**증상**: WAR 파일이 자동 배포되지 않음

**원인**: 권한 문제 또는 디스크 공간 부족

**해결**:
```bash
# 디스크 공간 확인
df -h

# 권한 확인
ls -la /engn001/tomcat/9.0.x/webapps/

# 권한 수정
chown -R midadm:midadm /engn001/tomcat/9.0.x/webapps/

# 수동 배포
cp /tmp/myapp.war /engn001/tomcat/9.0.x/webapps/
```

### 14.3 성능 문제 해결

#### 14.3.1 응답 속도 저하

**진단**:
```bash
# CPU 사용률 확인
top -u midadm

# 스레드 덤프 생성
jstack <tomcat_pid> > /tmp/thread_dump.txt

# GC 로그 분석
tail -f /logs001/tomcat/9.0.x/servers/was-asc_8080/logs/gc.log
```

**해결**:
- GC 튜닝
- 데이터베이스 쿼리 최적화
- 캐싱 적용
- 스레드 풀 조정

#### 14.3.2 메모리 누수

**진단**:
```bash
# 힙 덤프 생성
jmap -dump:format=b,file=/tmp/heap_dump.hprof <tomcat_pid>

# 메모리 사용 추이 확인 (Scouter)
```

**해결**:
- 힙 덤프 분석 (Eclipse MAT)
- 불필요한 객체 참조 제거
- 캐시 크기 제한
- 세션 타임아웃 조정

---

## 15. 부록

### 15.1 참고 문서

#### 15.1.1 공식 문서
- **Apache HTTP Server**: https://httpd.apache.org/docs/2.4/
- **Apache Tomcat**: https://tomcat.apache.org/tomcat-9.0-doc/
- **Scouter**: https://github.com/scouter-project/scouter
- **Jenkins**: https://www.jenkins.io/doc/
- **GitLab**: https://docs.gitlab.com/

#### 15.1.2 내부 문서
- 요구사항정의서: file/img/요구사항정의서-20260225_page_001.png
- 계정 설정 가이드: implementation/mw/setup-midadm.md
- Apache 설치 가이드: implementation/mw/install-apache.md

### 15.2 주요 경로 요약

| 구분 | 경로 | 설명 |
|------|------|------|
| Apache 엔진 | /engn001/apache/2.4.66 | Apache 설치 경로 |
| Apache 로그 | /logs001/apache/2.4.66/servers/webd-asc_80/logs | Apache 로그 |
| Apache 소스 | /sorc001/appadm/applications/htdocs | DocumentRoot |
| Tomcat 엔진 | /engn001/tomcat/9.0.x | Tomcat 설치 경로 |
| Tomcat 로그 | /logs001/tomcat/9.0.x/servers/was-asc_8080/logs | Tomcat 로그 |
| Scouter | /engn001/scouter | Scouter 설치 경로 |
| 백업 | /backup | 백업 파일 저장 |
| 스크립트 | /sorc001/scripts | 운영 스크립트 |

### 15.3 주요 포트 요약

| 서비스 | 포트 | 프로토콜 | 용도 |
|--------|------|----------|------|
| Apache | 80 | HTTP | 웹 서비스 |
| Apache | 443 | HTTPS | 보안 웹 서비스 |
| Tomcat | 8080 | HTTP | 애플리케이션 서버 |
| Tomcat | 8009 | AJP | Apache 연동 |
| Tomcat | 8005 | TCP | Shutdown |
| Scouter | 6100 | TCP/UDP | 모니터링 |
| Scouter | 6180 | HTTP | 웹 콘솔 |
| JMX | 9999 | TCP | JMX 모니터링 |

### 15.4 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2026-03-03 | System Team | 초안 작성 |
| 2.0 | 2026-03-03 | System Team | midadm 계정 설정 및 setcap 상세 추가 |

### 15.5 용어 정리

| 용어 | 설명 |
|------|------|
| **midadm** | Middleware 관리 전용 계정 (비 root) |
| **setcap** | 실행 파일에 특정 권한(capability) 부여 |
| **cap_net_bind_service** | 1024 이하 포트 바인딩 권한 |
| **MPM** | Multi-Processing Module (Apache 처리 방식) |
| **AJP** | Apache JServ Protocol (Apache-Tomcat 연동) |
| **mod_proxy** | Apache 프록시 모듈 |
| **mod_jk** | Apache-Tomcat 연동 모듈 |
| **Scouter** | APM (Application Performance Monitoring) 도구 |
| **JVM** | Java Virtual Machine |
| **GC** | Garbage Collection |
| **Heap Dump** | JVM 메모리 스냅샷 |
| **Thread Dump** | 스레드 상태 스냅샷 |

---

## 16. 결론

본 설계서는 A Project의 Middleware 아키텍처를 정의하며, 다음과 같은 특징을 가집니다:

### 16.1 주요 특징

1. **보안 강화**
   - 비 root 계정(midadm) 운영
   - setcap을 통한 최소 권한 부여
   - 보안 헤더 및 방화벽 설정

2. **표준화된 구조**
   - 엔진(/engn001), 로그(/logs001), 소스(/sorc001) 경로 분리
   - 일관된 디렉토리 네이밍 규칙
   - 명확한 권한 관리

3. **운영 효율성**
   - 자동화된 백업/복구
   - CI/CD 파이프라인 구축
   - 실시간 모니터링 (Scouter)

4. **성능 최적화**
   - Apache MPM Worker 튜닝
   - Tomcat 커넥터 최적화
   - JVM GC 튜닝

5. **확장성**
   - 로드 밸런싱 지원 가능
   - 클러스터링 구성 가능
   - 수평 확장 용이

### 16.2 향후 개선 사항

1. **고가용성 (HA)**
   - Apache/Tomcat 이중화
   - 로드 밸런서 도입
   - 세션 클러스터링

2. **컨테이너화**
   - Docker 기반 배포
   - Kubernetes 오케스트레이션
   - 마이크로서비스 아키텍처

3. **모니터링 강화**
   - ELK Stack 도입
   - Prometheus + Grafana
   - 알림 자동화

4. **보안 강화**
   - WAF (Web Application Firewall)
   - SSL/TLS 인증서 자동 갱신
   - 침입 탐지 시스템 (IDS)

이 설계를 기반으로 안정적이고 확장 가능한 Middleware 환경을 구축할 수 있으며, 지속적인 개선을 통해 더욱 견고한 시스템으로 발전시킬 수 있습니다.

---

**문서 끝**
