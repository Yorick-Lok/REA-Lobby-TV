# REA-Lobby-TV

Project Board: https://github.com/users/Yorick-Lok/projects/2

## Project Overview
### The question
A wall-mounted tv, displaying presentation slides, that could also include video? 

### Here is what we came up with
- Python `Flask` web-based backend.
- Admin page with `authentication`.
- Keep `x` amount of backups of previous uploads.
- Auto-update `clients` when a upload completes using `websocket`.
- Post upload `transcoding` with a progress bar.

### Technical usage breakdown
1. Login to the `http://<server-ip>:5000/admin`, see: [Auth credentials](#authentication)
2. Upload the `.mp4` that you want to display. `max 2GB`
3. The backend emits a **'refresh-page'** command using `websocket`, once upload completes.
    - `clients` may stop video playback, and display a blank screen during file replacement. This is to prevent any active file-locks.
4. `clients` display the newly uploaded `.mp4` after upload, backup and saving completes.

> [!WARNING]
> A `.mp4` may contains corrupted frames. Some hardware-encoders may present issues, like freezes or stuttering.
>
> - To make this safer:
>     - A post upload `transcoding` process is started, using `ffmpeg`. `Removing audio and discard corrupt frames`
>     - Transcoding may reduce filesize by 30-40%.
>     - Progress is displayed in the admin panel.
>     - **The browser does not need to remain open during this process.**
>     - Once completed, steps `3-4` are repeated, replacing the current video with the `transcoded` version.
>     - The original is preserved: `http://<server-ip>:5000/static/Screen-unencoded.mp4`

## Deployment Prerequisites
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

3. Setup Flask / Socket.IO & FFmpeg
```bash
sudo apt-get install python3-venv python3-full ffmpeg
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


## Development
1. Clone the project using your preferred `IDE` or `Github Desktop`.
2. Open a terminal in the root of the project.
3. Install the requirements
    ```bash
    python -m pip install -r requirements.txt
    ```
4. Run
    ```bash
    .\main.py

    # use ctrl+c to stop the active instance.
    ```
5. Navigate to: 
    - `http://localhost:5000` for video playback
    - `http://localhost:5000/admin` for admin panel

    ### FFmpeg on windows
    If you want to test `transcoding` in a windows environment, you needs to have ffmpeg installed on your device and added to system PATH.
    
    You can also use `winget` command:
    ```bash
    winget install Gyan.FFmpeg
    ```