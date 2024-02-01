import os
import sqlite3
import json
import uuid
import random

connection = None
cursor = None

def db_conn():
    global connection, cursor
    # connect to db
    db_path = "C:\\Users\\mrsintech\\Desktop\\x-ui-english.db"
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

def last_db_id():
    cursor.execute("SELECT * FROM inbounds;")
    # Fetch column names from the cursor description
    columns = [column[0] for column in cursor.description]
    # Fetch all rows
    rows = cursor.fetchall()
    # Print column names
    print(columns)
    # Print rows
    for row in rows:
        # print(" | ".join(str(value) for value in row))
        print(row)

    return rows[-1][0]


def inbound_insert(remark, phone, total_gb=0):
    new_uuid = uuid.uuid4()
    port = random.randint(10000, 100000)

    settings = {
        "clients": [
            {
                "id": 'ab71a812-d353-4b38-94bd-a2c6ce1d3eae',
                # "id": str(new_uuid),
                "flow": "xtls-rprx-direct",
                "email": str(phone),
                "limitIp": 0,
                "totalGB": total_gb,
                "expiryTime": ""
            }
        ],
        "decryption": "none",
        "fallbacks": []
    }
    stream_settings = {
        "network": "ws",
        "security": "tls",
        "tlsSettings": {
            "serverName": "test1.raptor.guru",
            "certificates": [
                {
                    "certificateFile": "/root/cert.crt",
                    "keyFile": "/root/private.key"
                }
            ],
            "alpn": "http/1.1"
        },
        "wsSettings": {
            "acceptProxyProtocol": False,
            "path": "/",
            "headers": {}
        }
    }
    sniffing = {
        "enabled": True,
        "destOverride": [
            "http",
            "tls"
        ]
    }
    # stream_settings = lower_true_false(stream_settings)
    # sniffing = lower_true_false(sniffing)
    print(stream_settings)
    inbound = {
        "id": last_db_id()+1,
        "user_id": 1,
        "up": 0,
        "down": 0,
        "total": 0,
        "remark": remark,
        "enable": 1,
        "expiry_time": 0,
        "listen": "",
        "port": port,
        "protocol": "vless",
        "settings": settings,
        "stream_settings": stream_settings,
        "tag": "inbound-"+str(port),
        "sniffing": sniffing
    }
    # cursor.execute('''CREATE TABLE IF NOT EXISTS inbounds (
    #                     id INTEGER PRIMARY KEY,
    #                     user_id INTEGER,
    #                     up INTEGER,
    #                     down INTEGER,
    #                     total INTEGER,
    #                     remark TEXT,
    #                     enable INTEGER,
    #                     expiry_time INTEGER,
    #                     listen TEXT,
    #                     port INTEGER,
    #                     protocol TEXT,
    #                     settings TEXT,
    #                     stream_settings TEXT,
    #                     tag TEXT,
    #                     sniffing TEXT
    #                 )''')
    settings_json = json.dumps(settings)
    stream_settings_json = json.dumps(stream_settings)
    sniffing_json = json.dumps(sniffing)
    print(sniffing_json)
    cursor.execute("INSERT INTO inbounds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (inbound['id'], inbound['user_id'], inbound['up'], inbound['down'],
                    inbound['total'], inbound['remark'], inbound['enable'], inbound['expiry_time'],
                    inbound['listen'], inbound['port'], inbound['protocol'], settings_json,
                    stream_settings_json, inbound['tag'], sniffing_json))
    # Commit the changes and close the connection
    connection.commit()
    connection.close()

def server_conn():
    import os
    import paramiko

    localpath = "C:\\Users\\mrsintech\\Desktop\\x-ui-english.db"
    remotepath = '/etc/x-ui-english/'

    # Create local directory if it doesn't exist
    # os.makedirs(localpath, exist_ok=True)

    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect("62.60.211.153", username='root', password='134679852')

    sftp = ssh.open_sftp()
    try:
        sftp.remove(remotepath+"x-ui-english.db")
    except FileNotFoundError:
        pass

    sftp.put(localpath, os.path.join(remotepath, os.path.basename(localpath)))
    sftp.close()

    command = "x-ui restart"
    stdin, stdout, stderr = ssh.exec_command(command)
    print("Command Output:")
    print(stdout.read().decode())
    ssh.close()


db_conn()
inbound_insert(remark='test4', phone=random.randint(1,10000000))
# print(last_db_id())
server_conn()



