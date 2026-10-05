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
3. Setup Flask
```bash
sudo apt-get install python3-flask python3-flask-socketio
```

2. Setup as a service
```bash
sudo nano /etc/systemd/system/reatv.service
# then paste and save:

[Service]
User=pi
WorkingDirectory=/rea/REA-Lobby-TV
ExecStart=/usr/bin/python3 /rea/REA-Lobby-TV/main.py
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
```
