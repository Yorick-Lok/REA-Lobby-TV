# REA-Lobby-TV

Project Board: https://github.com/users/Yorick-Lok/projects/2


## Prerequisites
This example uses [FullPageOS](https://github.com/guysoft/fullpageos) as the linux operatinng system.

default OS login:
| Username | Password |
|----------|----------|
| pi       | raspberry |

## Installation
1. Create the root directory and clone the project:

```bash
sudo mkdir -p /rea
cd /rea
sudo git clone https://github.com/Yorick-Lok/REA-Lobby-TV.git
```
3. Setup Update script
```bash
sudo chmod +x update.sh
```

3. Setup Flask / Socket.IO
```bash
sudo apt-get install python3-venv python3-full
python3 -m venv .venv

.venv/bin/pip install \
    "Flask==2.2.5" \
    "Werkzeug==2.2.3" \
    "Flask-SocketIO==5.3.2" \
    "python-socketio==5.7.2" \
    "python-engineio==4.3.4" \
    "simple-websocket==1.1.0"

# verify versions:
.venv/bin/pip list | grep -Ei 'flask|werkzeug|socketio|engineio|websocket'
```

2. Setup as a service
```bash
sudo nano /etc/systemd/system/reatv.service
# then paste and save:

[Service]
User=pi
WorkingDirectory=/rea/REA-Lobby-TV
#ExecStart=/usr/bin/python3 /rea/REA-Lobby-TV/main.py
ExecStart=/rea/REA-Lobby-TV/.venv/bin/python /rea/REA-Lobby-TV/main.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=reatv

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable reatv
sudo systemctl start reatv

# check status:
systemctl status reatv

# check live output:
journalctl -u reatv -f

# restart service
sudo systemctl restart reatv

# update from main
cd /rea/REA-Lobby-TV
sudo ./update.sh
```

## Authentication
The default login is:

| Username | Password |
|----------|----------|
| `admin`  | `admin`  |

For a custom login, create a `accountinfo.txt` file containing the username and password separated by a `:`

```text
user:123456
```
```bash
cd /rea/REA-Lobby-TV
nano accountinfo.txt

# write:
admin:password

# restart service
sudo systemctl restart reatv
```

## Updating
There is a update script that will: 
- Stop Flask
- Pull the latest changes from Git
- Start Flask. 
- Then wait 10 seconds before restarting the fullscreen browser.

```bash
# run the following commands to execute this script
cd /rea/REA-Lobby-TV
sudo ./update.sh

# if updating fails due to local cahnges. run this to reset any local changes
sudo git reset --hard HEAD
```