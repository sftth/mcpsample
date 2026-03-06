#!/usr/bin/env python3
"""
Setup midadm user on EC2 server via SSH (Version 2)
Creates midadm account and configures SSH access
Uses ChromaDB vector database to retrieve EC2 configuration
Alternative to Ansible for Windows environments
"""

import paramiko
import sys
import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

# midadm configuration
MIDADM_USER = "midadm"
MIDADM_GROUP = "midadm"
MIDADM_PASSWORD = "midadm"

def get_ec2_config_from_vectordb():
    """
    Retrieve EC2 configuration from ChromaDB vector database
    
    Returns:
        dict: Dictionary containing 'ips' (list), 'user', and 'pem'
        
    Raises:
        ValueError: If required information cannot be retrieved
    """
    print("\n" + "=" * 60)
    print("Retrieving EC2 Configuration from Vector DB")
    print("=" * 60)
    
    try:
        # Connect to ChromaDB
        script_dir = Path(__file__).parent
        chroma_path = script_dir.parent.parent.parent / "chroma-agent" / "chroma_store"
        
        print(f"[Info] ChromaDB path: {chroma_path}")
        
        client = chromadb.PersistentClient(path=str(chroma_path))
        
        # Setup embedding function
        sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get collection
        collection = client.get_collection(
            name="agent_knowledge",
            embedding_function=sentence_ef
        )
        
        print("[Success] Connected to ChromaDB")
        
        # Retrieve EC2 IP information
        print("\n[Query] Retrieving EC2 IP information...")
        result = collection.get(ids=["ec2_ip_list"])
        if not result['documents']:
            raise ValueError("EC2 IP information not found in vector DB")
        
        ip_doc = result['documents'][0]
        print(f"[Found] {ip_doc}")
        
        # Extract IPs from document
        ip_match = re.search(r'EC2 IP 정보:\s*(.+)', ip_doc)
        if not ip_match:
            raise ValueError("Could not parse IP information from vector DB")
        
        ip_string = ip_match.group(1).strip()
        ips = [ip.strip() for ip in ip_string.split(',') if ip.strip()]
        
        # Retrieve EC2 SSH User information
        print("\n[Query] Retrieving EC2 SSH User information...")
        result = collection.get(ids=["ec2_ssh_user"])
        if not result['documents']:
            raise ValueError("EC2 SSH User information not found in vector DB")
        
        user_doc = result['documents'][0]
        print(f"[Found] {user_doc}")
        
        # Extract user from document
        user_match = re.search(r'EC2 SSH User 정보:\s*(.+)', user_doc)
        if not user_match:
            raise ValueError("Could not parse SSH User information from vector DB")
        
        ssh_user = user_match.group(1).strip()
        
        # Retrieve EC2 PEM path information
        print("\n[Query] Retrieving EC2 PEM path information...")
        result = collection.get(ids=["ec2_pem_path"])
        if not result['documents']:
            raise ValueError("EC2 PEM path information not found in vector DB")
        
        pem_doc = result['documents'][0]
        print(f"[Found] {pem_doc}")
        
        # Extract PEM path from document
        pem_match = re.search(r'EC2 PEM 경로:\s*(.+)', pem_doc)
        if not pem_match:
            raise ValueError("Could not parse PEM path information from vector DB")
        
        pem_path = pem_match.group(1).strip()
        
        config = {
            'ips': ips,
            'user': ssh_user,
            'pem': pem_path
        }
        
        print("\n" + "=" * 60)
        print("Configuration Retrieved Successfully")
        print("=" * 60)
        print(f"IPs: {', '.join(config['ips'])}")
        print(f"User: {config['user']}")
        print(f"PEM: {config['pem']}")
        print("=" * 60)
        
        return config
        
    except Exception as e:
        print(f"\n[Error] Failed to retrieve configuration from vector DB: {e}")
        import traceback
        traceback.print_exc()
        raise

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
    
    print("=" * 60)
    print("Setup midadm Account v2 - Using Vector DB")
    print("=" * 60)
    
    try:
        # Get configuration from ChromaDB vector database
        config = get_ec2_config_from_vectordb()
        
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
        
    except ValueError as e:
        print(f"\n[Error] {e}")
        print("[Info] Please ensure ChromaDB contains all required EC2 configuration")
        return False
    except Exception as e:
        print(f"\n[Error] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
