# Ansible Playbook - midadm 계정 설정

이 Ansible playbook은 EC2 인스턴스에 midadm 계정을 자동으로 생성하고 설정합니다.

## 📋 사전 요구사항

### 1. Ansible 설치
```bash
# macOS
brew install ansible

# 또는 pip 사용
pip install ansible
```

### 2. SSH 키 권한 설정
```bash
chmod 400 /Users/summit/.ssh/jacob.park-keypair.pem
```

### 3. EC2 인스턴스 접근 확인
```bash
ssh -i /Users/summit/.ssh/jacob.park-keypair.pem ec2-user@56.155.32.25
```

## 📁 파일 구조

```
ansible/
├── inventory.ini          # 서버 인벤토리 파일
├── setup-midadm.yml       # midadm 계정 설정 playbook
└── README.md              # 이 파일
```

## 🔧 설정 파일

### inventory.ini
- EC2 서버 정보 (IP, 사용자, SSH 키)
- 필요시 IP 주소 수정 가능

### setup-midadm.yml
- midadm 그룹 생성
- midadm 사용자 생성 (홈 디렉토리 포함)
- 비밀번호 설정
- 계정 검증

## 🚀 실행 방법

### 1. 기본 실행
```bash
cd /Users/summit/IDE/workspace-ai/mcpsample/implementation/mw/ansible
ansible-playbook -i inventory.ini setup-midadm.yml
```

### 2. 상세 출력 (verbose)
```bash
ansible-playbook -i inventory.ini setup-midadm.yml -v
```

### 3. 더 상세한 출력
```bash
ansible-playbook -i inventory.ini setup-midadm.yml -vvv
```

### 4. Dry-run (실제 변경 없이 테스트)
```bash
ansible-playbook -i inventory.ini setup-midadm.yml --check
```

### 5. 특정 태스크만 실행
```bash
ansible-playbook -i inventory.ini setup-midadm.yml --start-at-task="Create midadm user with home directory"
```

## ✅ 실행 결과 확인

### 1. Playbook 실행 후 자동 검증
Playbook이 성공적으로 실행되면 다음 정보가 표시됩니다:
- 그룹 생성 결과
- 사용자 생성 결과
- 비밀번호 설정 결과
- 사용자 정보 (uid, gid, groups)

### 2. 수동 확인
```bash
# SSH로 접속하여 확인
ssh -i /Users/summit/.ssh/jacob.park-keypair.pem ec2-user@56.155.32.25

# midadm 사용자 확인
sudo id midadm

# midadm 그룹 확인
sudo getent group midadm

# 홈 디렉토리 확인
sudo ls -la /home/midadm

# midadm 계정으로 전환 테스트
sudo su - midadm
```

## 🔐 계정 정보

- **사용자명**: midadm
- **그룹명**: midadm
- **비밀번호**: midadm
- **홈 디렉토리**: /home/midadm
- **쉘**: /bin/bash

## 📝 변수 수정

비밀번호나 사용자명을 변경하려면 `setup-midadm.yml` 파일의 `vars` 섹션을 수정하세요:

```yaml
vars:
  midadm_user: midadm        # 사용자명 변경
  midadm_group: midadm       # 그룹명 변경
  midadm_password: midadm    # 비밀번호 변경
```

## 🔍 문제 해결

### 연결 실패
```bash
# SSH 연결 테스트
ansible ec2_servers -i inventory.ini -m ping
```

### 권한 오류
```bash
# SSH 키 권한 확인
ls -la /Users/summit/.ssh/jacob.park-keypair.pem
# 권한이 400이 아니면:
chmod 400 /Users/summit/.ssh/jacob.park-keypair.pem
```

### 이미 계정이 존재하는 경우
Playbook은 멱등성(idempotent)을 가지므로 여러 번 실행해도 안전합니다.
- 이미 존재하는 경우: "ok" 상태로 표시
- 새로 생성된 경우: "changed" 상태로 표시

## 📊 예상 출력

```
PLAY [Setup midadm account on EC2] *********************************************

TASK [Gathering Facts] *********************************************************
ok: [ec2-server]

TASK [Create midadm group] *****************************************************
changed: [ec2-server]

TASK [Display group creation result] *******************************************
ok: [ec2-server] => {
    "msg": "midadm group created successfully"
}

TASK [Create midadm user with home directory] **********************************
changed: [ec2-server]

TASK [Display user creation result] ********************************************
ok: [ec2-server] => {
    "msg": "midadm user created successfully"
}

TASK [Set password for midadm user] ********************************************
changed: [ec2-server]

TASK [Display password setting result] *****************************************
ok: [ec2-server] => {
    "msg": "Password set successfully for midadm user"
}

TASK [Verify midadm user exists] ***********************************************
ok: [ec2-server]

TASK [Display user verification] ***********************************************
ok: [ec2-server] => {
    "msg": "uid=1001(midadm) gid=1001(midadm) groups=1001(midadm)"
}

TASK [Display completion message] **********************************************
ok: [ec2-server] => {
    "msg": [
        "==========================================",
        "midadm account setup completed successfully",
        "User: midadm",
        "Group: midadm",
        "Home Directory: /home/midadm",
        "=========================================="
    ]
}

PLAY RECAP *********************************************************************
ec2-server                 : ok=10   changed=3    unreachable=0    failed=0
```

## 🎯 다음 단계

midadm 계정 생성 후:
1. Apache 설치를 위한 디렉토리 생성
2. Apache 소스 파일 전송
3. Apache 설치 및 설정

관련 파일: `install-apache.md`
