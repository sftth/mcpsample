#!/usr/bin/env python3
"""
Setup midadm user on EC2 server via SSH
Alternative to Ansible for Windows environments
"""

import paramiko
import sys
from pathlib import Path

# Server configuration
SERVER_IP = "13.208.161.214"
SSH_USER = "ec2-user"
SSH_KEY_PATH = r"C:\Users\74469\.ssh\jacob.park-keypair.pem"

# midadm configuration
MIDADM_USER = "midadm"
MIDADM_GROUP = "midadm"
MIDADM_PASSWORD = "midadm"

def execute_remote_command(ssh_client, command, use_sudo=True):
    """Execute a command on the remote server"""
    if use_sudo:
        command = f"sudo {command}"
    
    print(f"\n[Executing] {command}")
    stdin, stdout, stderr = ssh_client.exec_command(command)
    
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()
    
    if output:
        print(f"[Output] {output}")
    if error and exit_status != 0:
        print(f"[Error] {error}")
    
    return exit_status, output, error

def setup_midadm_account():
    """Setup midadm account on EC2 server"""
    
    print("=" * 60)
    print("Setting up midadm account on EC2 server")
    print(f"Server: {SERVER_IP}")
    print("=" * 60)
    
    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to server
        print(f"\n[Connecting] to {SERVER_IP} as {SSH_USER}...")
        
        # Try to load the private key
        try:
            private_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
        except FileNotFoundError:
            print(f"[Error] SSH key not found at {SSH_KEY_PATH}")
            print("[Info] Please ensure the SSH key path is correct for your system")
            return False
        except Exception as e:
            print(f"[Error] Failed to load SSH key: {e}")
            return False
        
        ssh.connect(
            hostname=SERVER_IP,
            username=SSH_USER,
            pkey=private_key,
            timeout=10
        )
        print("[Success] Connected to server")
        
        # Step 1: Create midadm group
        print("\n" + "=" * 60)
        print("Step 1: Creating midadm group")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh, 
            f"groupadd {MIDADM_GROUP}"
        )
        if status == 0:
            print(f"[Success] Group '{MIDADM_GROUP}' created")
        elif "already exists" in error:
            print(f"[Info] Group '{MIDADM_GROUP}' already exists")
        else:
            print(f"[Warning] Group creation returned status {status}")
        
        # Step 2: Create midadm user
        print("\n" + "=" * 60)
        print("Step 2: Creating midadm user")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"useradd -m -g {MIDADM_GROUP} {MIDADM_USER}"
        )
        if status == 0:
            print(f"[Success] User '{MIDADM_USER}' created with home directory")
        elif "already exists" in error:
            print(f"[Info] User '{MIDADM_USER}' already exists")
        else:
            print(f"[Warning] User creation returned status {status}")
        
        # Step 3: Set password
        print("\n" + "=" * 60)
        print("Step 3: Setting password for midadm user")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"bash -c \"echo '{MIDADM_USER}:{MIDADM_PASSWORD}' | chpasswd\""
        )
        if status == 0:
            print(f"[Success] Password set for user '{MIDADM_USER}'")
        else:
            print(f"[Warning] Password setting returned status {status}")
        
        # Step 4: Verify user creation
        print("\n" + "=" * 60)
        print("Step 4: Verifying midadm user")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"id {MIDADM_USER}",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] User verification: {output}")
        
        # Step 5: Check home directory
        print("\n" + "=" * 60)
        print("Step 5: Checking home directory")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"ls -ld /home/{MIDADM_USER}",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] Home directory: {output}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("SETUP COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"User: {MIDADM_USER}")
        print(f"Group: {MIDADM_GROUP}")
        print(f"Home Directory: /home/{MIDADM_USER}")
        print(f"Password: {MIDADM_PASSWORD}")
        print("=" * 60)
        
        return True
        
    except paramiko.AuthenticationException:
        print("[Error] Authentication failed. Please check your SSH key.")
        return False
    except paramiko.SSHException as e:
        print(f"[Error] SSH connection failed: {e}")
        return False
    except Exception as e:
        print(f"[Error] Unexpected error: {e}")
        return False
    finally:
        ssh.close()
        print("\n[Disconnected] from server")

if __name__ == "__main__":
    success = setup_midadm_account()
    sys.exit(0 if success else 1)
