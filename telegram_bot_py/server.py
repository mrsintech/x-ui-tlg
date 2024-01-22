import os
import paramiko

class Server:
    def __init__(self):
        localpath = "C:\\Users\\mrsintech\\Desktop\\x-ui-english.db"
        remotepath = '/etc/x-ui-english/'

        # Create local directory if it doesn't exist
        # os.makedirs(localpath, exist_ok=True)

        ssh = paramiko.SSHClient()
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.connect("62.60.131.118", username='root', password='134679852')

        sftp = ssh.open_sftp()
        try:
            sftp.remove(remotepath + "x-ui-english.db")
        except FileNotFoundError:
            pass

        sftp.put(localpath, os.path.join(remotepath, os.path.basename(localpath)))
        sftp.close()

        command = "x-ui restart"
        stdin, stdout, stderr = ssh.exec_command(command)
        print("Command Output:")
        print(stdout.read().decode())
        ssh.close()
