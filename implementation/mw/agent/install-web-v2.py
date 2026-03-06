#!/usr/bin/env python3
"""
Install Apache on EC2 server (Version 2)
Creates directories, uploads Apache, extracts and configures
Uses ChromaDB vector database to retrieve EC2 configuration
"""

import paramiko
import sys
import os
import re
import time
from pathlib import Path
from scp import SCPClient
import chromadb
from chromadb.utils import embedding_functions

# midadm configuration
MIDADM_USER = "midadm"

# Apache configuration
APACHE_TAR_FILE = r"c:\IDE\ws-ai\mcpsample\implementation\mw\apache-2.4.66.tar.gz"
ENGN_PATH = "/engn001"
LOGS_PATH = "/logs001/apache/2.4.66/servers/webd-asc_80/logs"
SORC_PATH = "/sorc001/appadm/applications/htdocs"
APACHE_INSTALL_PATH = "/engn001/apache/2.4.66"

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

def install_apache_on_server(server_ip, ssh_user, ssh_key_path):
    """Install Apache on a single EC2 server"""
    
    print("\n" + "=" * 60)
    print(f"Installing Apache on server: {server_ip}")
    print("=" * 60)
    
    # Check if Apache tar file exists
    if not os.path.exists(APACHE_TAR_FILE):
        print(f"[Error] Apache tar file not found: {APACHE_TAR_FILE}")
        return False
    
    print(f"[Info] Apache tar file found: {APACHE_TAR_FILE}")
    
    # Create SSH client for initial connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Create SSH client for midadm connection
    ssh_midadm = paramiko.SSHClient()
    ssh_midadm.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to server as initial user
        print(f"\n[Connecting] to {server_ip} as {ssh_user}...")
        
        # Try to load the private key
        try:
            private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
        except FileNotFoundError:
            print(f"[Error] SSH key not found at {ssh_key_path}")
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
        
        # Step 0: Install required dependencies
        print("\n" + "=" * 60)
        print("Step 0: Installing required dependencies")
        print("=" * 60)
        
        # Install pcre and other required libraries
        dependencies = [
            "pcre",
            "pcre-devel",
            "apr",
            "apr-util"
        ]
        
        for dep in dependencies:
            status, output, error = execute_remote_command(
                ssh,
                f"yum install -y {dep}",
                use_sudo=True
            )
            if status == 0:
                print(f"[Success] {dep} installed/updated")
            elif "already installed" in output or "already installed" in error:
                print(f"[Info] {dep} already installed")
            else:
                print(f"[Warning] {dep} installation returned status {status}")
        
        # Step 1: Create engine directory
        print("\n" + "=" * 60)
        print("Step 1: Creating engine directory (/engn001)")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"mkdir -p {ENGN_PATH}",
            use_sudo=True
        )
        if status == 0 or "File exists" in error:
            print(f"[Success] Engine directory created/exists")
        
        # Set ownership
        status, output, error = execute_remote_command(
            ssh,
            f"chown {MIDADM_USER}:{MIDADM_USER} {ENGN_PATH}",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Ownership set to {MIDADM_USER}:{MIDADM_USER}")
        
        # Step 2: Create logs directory
        print("\n" + "=" * 60)
        print("Step 2: Creating logs directory")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"mkdir -p {LOGS_PATH}",
            use_sudo=True
        )
        if status == 0 or "File exists" in error:
            print(f"[Success] Logs directory created/exists")
        
        # Set ownership
        status, output, error = execute_remote_command(
            ssh,
            f"chown -R {MIDADM_USER}:{MIDADM_USER} /logs001",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Ownership set to {MIDADM_USER}:{MIDADM_USER}")
        
        # Step 3: Create source directory
        print("\n" + "=" * 60)
        print("Step 3: Creating source directory")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"mkdir -p {SORC_PATH}",
            use_sudo=True
        )
        if status == 0 or "File exists" in error:
            print(f"[Success] Source directory created/exists")
        
        # Set ownership
        status, output, error = execute_remote_command(
            ssh,
            f"chown -R {MIDADM_USER}:{MIDADM_USER} /sorc001",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Ownership set to {MIDADM_USER}:{MIDADM_USER}")
        
        # Step 4: Upload Apache tar file to home directory first
        print("\n" + "=" * 60)
        print("Step 4: Uploading Apache tar file")
        print("=" * 60)
        print(f"[Info] Uploading {APACHE_TAR_FILE} to /home/{ssh_user}/")
        
        try:
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(APACHE_TAR_FILE, f"/home/{ssh_user}/apache-2.4.66.tar.gz")
            print("[Success] Apache tar file uploaded to home directory")
        except Exception as e:
            print(f"[Error] Failed to upload file: {e}")
            return False
        
        # Step 5: Move Apache tar file to /engn001
        print("\n" + "=" * 60)
        print("Step 5: Moving Apache tar file to /engn001")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"mv /home/{ssh_user}/apache-2.4.66.tar.gz {ENGN_PATH}/",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Apache tar file moved to {ENGN_PATH}")
        
        # Step 6: Extract Apache tar file
        print("\n" + "=" * 60)
        print("Step 6: Extracting Apache tar file")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"tar -xzf {ENGN_PATH}/apache-2.4.66.tar.gz -C {ENGN_PATH}",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Apache tar file extracted")
        else:
            print(f"[Warning] Extraction returned status {status}")
        
        # Step 7: Verify extraction
        print("\n" + "=" * 60)
        print("Step 7: Verifying Apache installation")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"ls -la {ENGN_PATH}/",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] Engine directory contents:\n{output}")
        
        # Step 8: Check if httpd binary exists
        print("\n" + "=" * 60)
        print("Step 8: Checking Apache httpd binary")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"ls -la {APACHE_INSTALL_PATH}/bin/httpd",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] Apache httpd binary found:\n{output}")
            
            # Step 9: Set capabilities for port binding
            print("\n" + "=" * 60)
            print("Step 9: Setting capabilities for port binding")
            print("=" * 60)
            status, output, error = execute_remote_command(
                ssh,
                f"setcap 'cap_net_bind_service=+ep' {APACHE_INSTALL_PATH}/bin/httpd",
                use_sudo=True
            )
            if status == 0:
                print(f"[Success] Capabilities set")
            
            # Verify capabilities
            status, output, error = execute_remote_command(
                ssh,
                f"getcap {APACHE_INSTALL_PATH}/bin/httpd",
                use_sudo=False
            )
            if status == 0:
                print(f"[Success] Capabilities verified: {output}")
        else:
            print(f"[Info] Apache httpd binary not found at expected location")
            print(f"[Info] This is normal if Apache needs to be compiled from source")
        
        # Step 10: Test Apache httpd binary
        print("\n" + "=" * 60)
        print("Step 10: Testing Apache httpd binary")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"{APACHE_INSTALL_PATH}/bin/httpd -v",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] Apache version check passed:\n{output}")
        else:
            print(f"[Warning] Apache version check failed")
            if error:
                print(f"[Error Details] {error}")
        
        # Step 11: Create test index.html
        print("\n" + "=" * 60)
        print("Step 11: Creating test index.html (as midadm)")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"su - {MIDADM_USER} -c \"echo 'Test' > {SORC_PATH}/index.html\"",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] index.html created in {SORC_PATH}")
        
        # Verify index.html
        status, output, error = execute_remote_command(
            ssh,
            f"cat {SORC_PATH}/index.html",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] index.html content: {output}")
        
        # Step 12: Start Apache web server
        print("\n" + "=" * 60)
        print("Step 12: Starting Apache web server (as midadm)")
        print("=" * 60)
        
        # Check if start.sh exists
        start_script_path = f"{APACHE_INSTALL_PATH}/servers/webd-asc_80/start.sh"
        status, output, error = execute_remote_command(
            ssh,
            f"ls -la {start_script_path}",
            use_sudo=False
        )
        
        if status == 0:
            print(f"[Success] start.sh found: {output}")
            
            # Execute start.sh as midadm user
            status, output, error = execute_remote_command(
                ssh,
                f"su - {MIDADM_USER} -c 'cd {APACHE_INSTALL_PATH}/servers/webd-asc_80 && ./start.sh'",
                use_sudo=True
            )
            if status == 0:
                print(f"[Success] Apache web server started")
                if output:
                    print(f"[Output] {output}")
            else:
                print(f"[Warning] start.sh execution returned status {status}")
                if error:
                    print(f"[Error] {error}")
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Step 13: Test web server with curl
            print("\n" + "=" * 60)
            print("Step 13: Testing web server with curl")
            print("=" * 60)
            status, output, error = execute_remote_command(
                ssh,
                "curl -s http://localhost:80",
                use_sudo=False
            )
            if status == 0:
                print(f"[Success] Web server is responding")
                print(f"[Response] {output}")
            else:
                print(f"[Warning] curl test failed with status {status}")
                if error:
                    print(f"[Error] {error}")
            
            # Check Apache process
            status, output, error = execute_remote_command(
                ssh,
                "ps aux | grep httpd | grep -v grep",
                use_sudo=False
            )
            if status == 0 and output:
                print(f"[Success] Apache processes running:\n{output}")
            else:
                print(f"[Info] No Apache processes found or check failed")
        else:
            print(f"[Warning] start.sh not found at {start_script_path}")
            print(f"[Info] You may need to start Apache manually")
        
        # Final summary
        print("\n" + "=" * 60)
        print("APACHE INSTALLATION COMPLETED")
        print("=" * 60)
        print(f"Server: {server_ip}")
        print(f"Engine Path: {ENGN_PATH}")
        print(f"Logs Path: {LOGS_PATH}")
        print(f"Source Path: {SORC_PATH}")
        print(f"Apache Install Path: {APACHE_INSTALL_PATH}")
        print(f"Dependencies Installed: pcre, pcre-devel, apr, apr-util")
        print(f"Test Page: {SORC_PATH}/index.html")
        print(f"Start Script: {start_script_path}")
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
        import traceback
        traceback.print_exc()
        return False
    finally:
        ssh.close()
        print("\n[Disconnected] from server")

def main():
    """Main function to install Apache on EC2 servers"""
    
    print("=" * 60)
    print("Install Apache v2 - Using Vector DB")
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
            
            if install_apache_on_server(server_ip, config['user'], config['pem']):
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
