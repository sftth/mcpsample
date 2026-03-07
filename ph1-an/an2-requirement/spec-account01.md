# EC2 계정 및 접속 정보

## EC2 인스턴스 정보

### 서버 목록

#### Web1
  - IP: 13.208.128.117
  - Account: ec2-user
  - PEM: /home/ec2-user/.ssh/jacob.park-keypair.pem

#### Web2
  - IP: 15.168.175.64
  - Account: ec2-user
  - PEM: /home/ec2-user/.ssh/jacob.park-keypair.pem

## 사전 준비

### SSH 접속 설정

[예시]
  ```bash
  # PEM 키 권한 설정
  chmod 400 /home/ec2-user/.ssh/jacob.park-keypair.pem

  # EC2 인스턴스 접속
  ssh -i /home/ec2-user/.ssh/jacob.park-keypair.pem ec2-user@13.208.128.117
  ```

## 접속 정보 요약

  - User: ec2-user
  - PEM 키: /home/ec2-user/.ssh/jacob.park-keypair.pem
  - 서버 수: 2대
  - IP 목록: 13.208.128.117, 15.168.175.64

## 메타데이터

### ip
  - Type: infrastructure
  - Service: ec2
  - Owner: jacob.park

### ssh_user
  - Type: infrastructure
  - Service: ec2
  - Owner: jacob.park

### pem_path
  - Type: infrastructure
  - Service: ec2
  - Owner: jacob.park
