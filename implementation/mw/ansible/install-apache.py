#!/usr/bin/env python3
"""
Install Apache on EC2 server
Creates directories, uploads Apache, extracts and configures
"""

import paramiko
import sys
import os
from scp import SCPClient

# Server configuration
SERVER_IP = "13.208.161.214"
SSH_USER = "ec2-user"  # Use ec2-user for sudo operations
MIDADM_USER = "midadm"
SSH_KEY_PATH = r"C:\Users\74469\.ssh\jacob.park-keypair.pem"

# Apache configuration
APACHE_TAR_FILE = r"implementation\mw\apache-2.4.66.tar.gz"
ENGN_PATH = "/engn001"
LOGS_PATH = "/logs001/apache/2.4.66/servers/webd-asc_80/logs"
SORC_PATH = "/sorc001/appadm/applications/htdocs"
APACHE_INSTALL_PATH = "/engn001/apache/2.4.66"

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

def install_apache():
    """Install Apache on EC2 server"""
    
    print("=" * 60)
    print("Installing Apache on EC2 server")
    print(f"Server: {SERVER_IP}")
    print("=" * 60)
    
    # Check if Apache tar file exists
    if not os.path.exists(APACHE_TAR_FILE):
        print(f"[Error] Apache tar file not found: {APACHE_TAR_FILE}")
        return False
    
    print(f"[Info] Apache tar file found: {APACHE_TAR_FILE}")
    
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
            f"chown midadm:midadm {ENGN_PATH}",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Ownership set to midadm:midadm")
        
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
            f"chown -R midadm:midadm /logs001",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Ownership set to midadm:midadm")
        
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
            f"chown -R midadm:midadm /sorc001",
            use_sudo=True
        )
        if status == 0:
            print(f"[Success] Ownership set to midadm:midadm")
        
        # Step 4: Upload Apache tar file to home directory first
        print("\n" + "=" * 60)
        print("Step 4: Uploading Apache tar file")
        print("=" * 60)
        print(f"[Info] Uploading {APACHE_TAR_FILE} to /home/{SSH_USER}/")
        
        try:
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(APACHE_TAR_FILE, f"/home/{SSH_USER}/apache-2.4.66.tar.gz")
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
            f"mv /home/{SSH_USER}/apache-2.4.66.tar.gz {ENGN_PATH}/",
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
        
        # Step 6: Verify extraction
        print("\n" + "=" * 60)
        print("Step 6: Verifying Apache installation")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"ls -la {ENGN_PATH}/",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] Engine directory contents:\n{output}")
        
        # Step 7: Check if httpd binary exists
        print("\n" + "=" * 60)
        print("Step 7: Checking Apache httpd binary")
        print("=" * 60)
        status, output, error = execute_remote_command(
            ssh,
            f"ls -la {APACHE_INSTALL_PATH}/bin/httpd",
            use_sudo=False
        )
        if status == 0:
            print(f"[Success] Apache httpd binary found:\n{output}")
            
            # Step 8: Set capabilities for port binding
            print("\n" + "=" * 60)
            print("Step 8: Setting capabilities for port binding")
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
        
        # Step 9: Test Apache httpd binary
        print("\n" + "=" * 60)
        print("Step 9: Testing Apache httpd binary")
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
        
        # Final summary
        print("\n" + "=" * 60)
        print("APACHE INSTALLATION COMPLETED")
        print("=" * 60)
        print(f"Engine Path: {ENGN_PATH}")
        print(f"Logs Path: {LOGS_PATH}")
        print(f"Source Path: {SORC_PATH}")
        print(f"Apache Install Path: {APACHE_INSTALL_PATH}")
        print(f"Dependencies Installed: pcre, pcre-devel, apr, apr-util")
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

if __name__ == "__main__":
    success = install_apache()
    sys.exit(0 if success else 1)
