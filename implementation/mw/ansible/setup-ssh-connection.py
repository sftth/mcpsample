#!/usr/bin/env python3
"""
Setup SSH connection for midadm user on EC2 server
Configures SSH authorized_keys for midadm account
"""

import paramiko
import sys

# Server configuration
SERVER_IP = "13.208.161.214"
SSH_USER = "ec2-user"
SSH_KEY_PATH = r"C:\Users\74469\.ssh\jacob.park-keypair.pem"

# midadm configuration
MIDADM_USER = "midadm"

def execute_remote_command(ssh_client, command, use_sudo=False):
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

def setup_ssh_connection():
    """Setup SSH connection for midadm account"""
    
    print("=" * 60)
    print("Setting up SSH connection for midadm account")
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
        
        # Step 1: Create .ssh directory for midadm
        print("\n" + "=" * 60)
        print("Step 1: Creating .ssh directory for midadm")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"mkdir -p /home/{MIDADM_USER}/.ssh",
            use_sudo=True
        )
        if status == 0 or "File exists" in error:
            print(f"[Success] .ssh directory created/exists")
        else:
            print(f"[Warning] Directory creation returned status {status}")
        
        # Step 2: Set permissions on .ssh directory
        print("\n" + "=" * 60)
        print("Step 2: Setting permissions on .ssh directory (700)")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"chmod 700 /home/{MIDADM_USER}/.ssh",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Permissions set to 700")
        
        # Step 3: Copy authorized_keys from ec2-user to midadm
        print("\n" + "=" * 60)
        print("Step 3: Copying authorized_keys from ec2-user to midadm")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"cp /home/ec2-user/.ssh/authorized_keys /home/{MIDADM_USER}/.ssh/authorized_keys",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] authorized_keys copied")
        
        # Step 4: Set permissions on authorized_keys file
        print("\n" + "=" * 60)
        print("Step 4: Setting permissions on authorized_keys (600)")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"chmod 600 /home/{MIDADM_USER}/.ssh/authorized_keys",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Permissions set to 600")
        
        # Step 5: Set ownership to midadm:midadm
        print("\n" + "=" * 60)
        print("Step 5: Setting ownership to midadm:midadm")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"chown -R {MIDADM_USER}:{MIDADM_USER} /home/{MIDADM_USER}/.ssh",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Ownership set to {MIDADM_USER}:{MIDADM_USER}")
        
        # Step 6: Verify the setup
        print("\n" + "=" * 60)
        print("Step 6: Verifying SSH configuration")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"ls -la /home/{MIDADM_USER}/.ssh/",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] SSH directory contents:\n{output}")
        
        # Step 7: Verify authorized_keys content
        print("\n" + "=" * 60)
        print("Step 7: Verifying authorized_keys file")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"wc -l /home/{MIDADM_USER}/.ssh/authorized_keys",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] authorized_keys file: {output}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("SSH CONNECTION SETUP COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"User: {MIDADM_USER}")
        print(f"SSH Directory: /home/{MIDADM_USER}/.ssh")
        print(f"Authorized Keys: /home/{MIDADM_USER}/.ssh/authorized_keys")
        print(f"Permissions: .ssh (700), authorized_keys (600)")
        print(f"Ownership: {MIDADM_USER}:{MIDADM_USER}")
        print("=" * 60)
        print("\nYou can now SSH to the server using:")
        print(f"  ssh -i {SSH_KEY_PATH} {MIDADM_USER}@{SERVER_IP}")
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
    success = setup_ssh_connection()
    sys.exit(0 if success else 1)
