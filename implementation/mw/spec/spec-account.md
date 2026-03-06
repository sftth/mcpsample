# midadm 계정 생성

## midadm 정보
  - user: midadm
  - group: midadm
  - password: midadm

## 사전 준비
  - ec2-user 로 로그인 후, sudo su 명령어를 통해 root 권한으로 접속
  - midadm 계정을 아래와 같이 생성

[예시]
  ```
  # 1. midadm 그룹 생성
  [root@ip-172-31-24-123 ec2-user]# groupadd midadm
  # 2. midadm 사용자 생성
  [root@ip-172-31-24-123 ec2-user]# useradd -m -g midadm midadm
  # 3. 비밀번호 설정
  [root@ip-172-31-24-123 ec2-user]# passwd midadm
  Changing password for user midadm.
  New password:
  Retype new password:
  passwd: all authentication tokens updated successfully.
  ```

# midadm ssh 접속 설정
  - 아래 [예시]와 같이 midadm ssh 접속 설정

[예시]
  ```
  # midadm 사용자로 전환
  su - midadm

  # .ssh 디렉토리 생성 및 권한 설정
  mkdir .ssh
  chmod 700 .ssh

  # root 계정으로 변경 
  sudo su

  # /home/midadm으로 이동
  cd /home/midadm

  # ec2-user의 공개키를 가져와서 복사
  cat /home/ec2-user/.ssh/authorized_keys > /home/midadm/.ssh/authorized_keys

  # 파일 권한 설정
  chmod 600 .ssh/authorized_keys

  # 소유권 재확인
  chown midadm:midadm .ssh/authorized_keys
  ```

