# EC2 정보
	- IP: 13.208.245.251
	- PEM: /Users/summit/.ssh/jacob.park-keypair.pem
	- User: ec2-user

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


