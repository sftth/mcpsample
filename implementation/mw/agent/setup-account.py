#!/usr/bin/env python3
"""
Setup midadm user on EC2 server via SSH
Creates midadm account and configures SSH access
Alternative to Ansible for Windows environments
"""

import paramiko
import sys
import re
from pathlib import Path

# midadm configuration
MIDADM_USER = "midadm"
MIDADM_GROUP = "midadm"
MIDADM_PASSWORD = "midadm"

def parse_server_spec(spec_file_path):
    """
    Parse server-spec.md file to extract IP, User, and PEM values
    
    Args:
        spec_file_path: Path to the server-spec.md file
        
    Returns:
        dict: Dictionary containing 'ips' (list), 'user', and 'pem'
        
    Raises:
        FileNotFoundError: If spec file doesn't exist
        ValueError: If required fields are missing
    """
    spec_path = Path(spec_file_path)
    
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_file_path}")
    
    # Read the spec file
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract values using regex
    ip_match = re.search(r'-\s*IP:\s*(.+)', content)
    user_match = re.search(r'-\s*User:\s*(.+)', content)
    pem_match = re.search(r'-\s*PEM:\s*(.+)', content)
    
    # Validate required fields
    if not ip_match:
        raise ValueError("Missing required field 'IP' in spec-server.md")
    if not user_match:
        raise ValueError("Missing required field 'User' in spec-server.md")
    if not pem_match:
        raise ValueError("Missing required field 'PEM' in spec-server.md")
    
    # Parse IP addresses (support comma-separated values)
    ip_string = ip_match.group(1).strip()
    ips = [ip.strip() for ip in ip_string.split(',') if ip.strip()]
    
    if not ips:
        raise ValueError("No valid IP addresses found in spec-server.md")
    
    return {
        'ips': ips,
        'user': user_match.group(1).strip(),
        'pem': pem_match.group(1).strip()
    }

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

def create_midadm_account(ssh_client):
    """Create midadm user account on the server"""
    
    print("\n" + "=" * 60)
    print("PART 1: Creating midadm Account")
    print("=" * 60)
    
    # Step 1: Create midadm group
    print("\n" + "-" * 60)
    print("Step 1: Creating midadm group")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client, 
        f"groupadd {MIDADM_GROUP}"
    )
    if status == 0:
        print(f"[Success] Group '{MIDADM_GROUP}' created")
    elif "already exists" in error:
        print(f"[Info] Group '{MIDADM_GROUP}' already exists")
    else:
        print(f"[Warning] Group creation returned status {status}")
    
    # Step 2: Create midadm user
    print("\n" + "-" * 60)
    print("Step 2: Creating midadm user")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"useradd -m -g {MIDADM_GROUP} {MIDADM_USER}"
    )
    if status == 0:
        print(f"[Success] User '{MIDADM_USER}' created with home directory")
    elif "already exists" in error:
        print(f"[Info] User '{MIDADM_USER}' already exists")
    else:
        print(f"[Warning] User creation returned status {status}")
    
    # Step 3: Set password
    print("\n" + "-" * 60)
    print("Step 3: Setting password for midadm user")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"bash -c \"echo '{MIDADM_USER}:{MIDADM_PASSWORD}' | chpasswd\""
    )
    if status == 0:
        print(f"[Success] Password set for user '{MIDADM_USER}'")
    else:
        print(f"[Warning] Password setting returned status {status}")
    
    # Step 4: Verify user creation
    print("\n" + "-" * 60)
    print("Step 4: Verifying midadm user")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"id {MIDADM_USER}",
        use_sudo=False
    )
    if status == 0:
        print(f"[Success] User verification: {output}")
    
    # Step 5: Check home directory
    print("\n" + "-" * 60)
    print("Step 5: Checking home directory")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"ls -ld /home/{MIDADM_USER}",
        use_sudo=False
    )
    if status == 0:
        print(f"[Success] Home directory: {output}")
    
    print("\n[Info] midadm account creation completed")
    return True

def configure_ssh_access(ssh_client, ssh_user):
    """Configure SSH access for midadm user"""
    
    print("\n" + "=" * 60)
    print("PART 2: Configuring SSH Access")
    print("=" * 60)
    
    # Step 6: Create .ssh directory for midadm
    print("\n" + "-" * 60)
    print("Step 6: Creating .ssh directory for midadm")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"mkdir -p /home/{MIDADM_USER}/.ssh",
        use_sudo=True
    )
    if status == 0 or "File exists" in error:
        print(f"[Success] .ssh directory created/exists")
    else:
        print(f"[Warning] Directory creation returned status {status}")
    
    # Step 7: Set permissions on .ssh directory
    print("\n" + "-" * 60)
    print("Step 7: Setting permissions on .ssh directory (700)")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"chmod 700 /home/{MIDADM_USER}/.ssh",
        use_sudo=True
    )
    if status == 0:
        print(f"[Success] Permissions set to 700")
    
    # Step 8: Copy authorized_keys from ssh_user to midadm
    print("\n" + "-" * 60)
    print(f"Step 8: Copying authorized_keys from {ssh_user} to midadm")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"cp /home/{ssh_user}/.ssh/authorized_keys /home/{MIDADM_USER}/.ssh/authorized_keys",
        use_sudo=True
    )
    if status == 0:
        print(f"[Success] authorized_keys copied")
    
    # Step 9: Set permissions on authorized_keys file
    print("\n" + "-" * 60)
    print("Step 9: Setting permissions on authorized_keys (600)")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"chmod 600 /home/{MIDADM_USER}/.ssh/authorized_keys",
        use_sudo=True
    )
    if status == 0:
        print(f"[Success] Permissions set to 600")
    
    # Step 10: Set ownership to midadm:midadm
    print("\n" + "-" * 60)
    print("Step 10: Setting ownership to midadm:midadm")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"chown -R {MIDADM_USER}:{MIDADM_USER} /home/{MIDADM_USER}/.ssh",
        use_sudo=True
    )
    if status == 0:
        print(f"[Success] Ownership set to {MIDADM_USER}:{MIDADM_USER}")
    
    # Step 11: Verify SSH configuration
    print("\n" + "-" * 60)
    print("Step 11: Verifying SSH configuration")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"ls -la /home/{MIDADM_USER}/.ssh/",
        use_sudo=True
    )
    if status == 0:
        print(f"[Success] SSH directory contents:\n{output}")
    
    # Step 12: Verify authorized_keys content
    print("\n" + "-" * 60)
    print("Step 12: Verifying authorized_keys file")
    print("-" * 60)
    status, output, error = execute_remote_command(
        ssh_client,
        f"wc -l /home/{MIDADM_USER}/.ssh/authorized_keys",
        use_sudo=True
    )
    if status == 0:
        print(f"[Success] authorized_keys file: {output}")
    
    print("\n[Info] SSH access configuration completed")
    return True

def setup_midadm_account_on_server(server_ip, ssh_user, ssh_key_path):
    """Setup midadm account and SSH access on a single EC2 server"""
    
    print("\n" + "=" * 60)
    print(f"Setting up midadm account on server: {server_ip}")
    print("=" * 60)
    
    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to server
        print(f"\n[Connecting] to {server_ip} as {ssh_user}...")
        
        # Try to load the private key
        try:
            private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
        except FileNotFoundError:
            print(f"[Error] SSH key not found at {ssh_key_path}")
            print("[Info] Please ensure the SSH key path is correct for your system")
            return False
        except Exception as e:
            print(f"[Error] Failed to load SSH key: {e}")
            return False
        
        ssh.connect(
            hostname=server_ip,
            username=ssh_user,
            pkey=private_key,
            timeout=10
        )
        print("[Success] Connected to server")
        
        # Execute account creation
        if not create_midadm_account(ssh):
            print("[Error] Failed to create midadm account")
            return False
        
        # Execute SSH configuration
        if not configure_ssh_access(ssh, ssh_user):
            print("[Error] Failed to configure SSH access")
            return False
        
        # Final summary
        print("\n" + "=" * 60)
        print("SETUP COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Server: {server_ip}")
        print(f"User: {MIDADM_USER}")
        print(f"Group: {MIDADM_GROUP}")
        print(f"Home Directory: /home/{MIDADM_USER}")
        print(f"Password: {MIDADM_PASSWORD}")
        print(f"SSH Directory: /home/{MIDADM_USER}/.ssh")
        print(f"Authorized Keys: /home/{MIDADM_USER}/.ssh/authorized_keys")
        print(f"Permissions: .ssh (700), authorized_keys (600)")
        print(f"Ownership: {MIDADM_USER}:{MIDADM_USER}")
        print("=" * 60)
        print("\nYou can now SSH to the server using:")
        print(f"  ssh -i {ssh_key_path} {MIDADM_USER}@{server_ip}")
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

def main():
    """Main function to setup midadm account on EC2 servers"""
    
    # Determine spec file path (relative to script location)
    script_dir = Path(__file__).parent
    spec_file = script_dir.parent / "spec" / "server-spec.md"
    
    print("=" * 60)
    print("Setup midadm Account - Reading Configuration")
    print("=" * 60)
    print(f"Spec file: {spec_file}")
    
    try:
        # Parse server spec file
        config = parse_server_spec(spec_file)
        
        print(f"\n[Config] Found {len(config['ips'])} server(s)")
        print(f"[Config] IPs: {', '.join(config['ips'])}")
        print(f"[Config] User: {config['user']}")
        print(f"[Config] PEM: {config['pem']}")
        
        # Process each server
        success_count = 0
        fail_count = 0
        
        for idx, server_ip in enumerate(config['ips'], 1):
            print("\n" + "#" * 60)
            print(f"# Processing Server {idx}/{len(config['ips'])}: {server_ip}")
            print("#" * 60)
            
            if setup_midadm_account_on_server(server_ip, config['user'], config['pem']):
                success_count += 1
            else:
                fail_count += 1
        
        # Final summary
        print("\n" + "=" * 60)
        print("OVERALL SUMMARY")
        print("=" * 60)
        print(f"Total servers: {len(config['ips'])}")
        print(f"Successful: {success_count}")
        print(f"Failed: {fail_count}")
        print("=" * 60)
        
        return fail_count == 0
        
    except FileNotFoundError as e:
        print(f"\n[Error] {e}")
        print("[Info] Please ensure spec-server.md exists in the spec directory")
        return False
    except ValueError as e:
        print(f"\n[Error] {e}")
        print("[Info] Please check spec-server.md has all required fields (IP, User, PEM)")
        return False
    except Exception as e:
        print(f"\n[Error] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
