# 🚀 Quick Start Guide - Ansible로 midadm 계정 설정

## Step 1: Ansible 설치

### macOS (Homebrew 사용)
```bash
brew install ansible
```

### Python pip 사용
```bash
pip3 install ansible
```

### 설치 확인
```bash
ansible --version
```

## Step 2: SSH 키 권한 설정
```bash
chmod 400 /Users/summit/.ssh/jacob.park-keypair.pem
```

## Step 3: 연결 테스트
```bash
cd /Users/summit/IDE/workspace-ai/mcpsample/implementation/mw/ansible
ansible ec2_servers -i inventory.ini -m ping
```

**예상 출력:**
```
ec2-server | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

## Step 4: Playbook 실행
```bash
ansible-playbook -i inventory.ini setup-midadm.yml
```

## Step 5: 결과 확인
```bash
ssh -i /Users/summit/.ssh/jacob.park-keypair.pem ec2-user@56.155.32.25 "sudo id midadm"
```

---

## 🔧 Ansible 없이 수동 실행 (대안)

Ansible을 설치하지 않고 수동으로 실행하려면:

```bash
ssh -i /Users/summit/.ssh/jacob.park-keypair.pem ec2-user@56.155.32.25 << 'EOF'
sudo groupadd midadm
sudo useradd -m -g midadm midadm
echo "midadm:midadm" | sudo chpasswd
sudo id midadm
echo "midadm account created successfully"
EOF
```

---

## 📋 전체 명령어 요약

```bash
# 1. Ansible 설치
brew install ansible

# 2. 작업 디렉토리로 이동
cd /Users/summit/IDE/workspace-ai/mcpsample/implementation/mw/ansible

# 3. 연결 테스트
ansible ec2_servers -i inventory.ini -m ping

# 4. Playbook 실행
ansible-playbook -i inventory.ini setup-midadm.yml

# 5. 결과 확인
ssh -i /Users/summit/.ssh/jacob.park-keypair.pem ec2-user@56.155.32.25 "sudo id midadm"
```

---

## ⚠️ 문제 해결

### "command not found: ansible"
```bash
# Homebrew로 설치
brew install ansible

# 또는 pip로 설치
pip3 install ansible
```

### "Permission denied (publickey)"
```bash
# SSH 키 권한 확인 및 수정
chmod 400 /Users/summit/.ssh/jacob.park-keypair.pem
```

### "Host key verification failed"
```bash
# known_hosts에 호스트 추가
ssh-keyscan -H 56.155.32.25 >> ~/.ssh/known_hosts
```

### 연결 테스트 실패
```bash
# 직접 SSH 연결 테스트
ssh -i /Users/summit/.ssh/jacob.park-keypair.pem ec2-user@56.155.32.25 "echo 'Connection successful'"
```

---

## 📊 성공 시 출력 예시

```
PLAY [Setup midadm account on EC2] *********************************************

TASK [Gathering Facts] *********************************************************
ok: [ec2-server]

TASK [Create midadm group] *****************************************************
changed: [ec2-server]

TASK [Create midadm user with home directory] **********************************
changed: [ec2-server]

TASK [Set password for midadm user] ********************************************
changed: [ec2-server]

TASK [Verify midadm user exists] ***********************************************
ok: [ec2-server]

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

---

## 🎯 다음 단계

midadm 계정 생성 완료 후:
1. Apache 설치 디렉토리 생성 (`install-apache.md` 참조)
2. Apache 소스 파일 전송
3. Apache 설치 및 설정
