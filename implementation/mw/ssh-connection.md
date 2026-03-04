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


