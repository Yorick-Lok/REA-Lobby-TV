
from flask import Flask, request, redirect, url_for, session, render_template
import os
import datetime
from flask_socketio import SocketIO, emit
from pathlib import Path
import random
import glob
import locale

class Server:
    def __init__( self ) -> None:

        
        file = Path ("accountinfo.txt")
        if file.exists(): 
            with open( file , "r") as file:
                for line in file:
                    self.ADMIN_USERNAME,self.ADMIN_PASSWORD = line.strip().split(":", 1)
        else:
            self.ADMIN_USERNAME = 'admin'
            self.ADMIN_PASSWORD = 'admin'

        # flask instance
        self.app = Flask(__name__)
        self.http_port = 5000
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading", logger=True, engineio_logger=True)
        self.socketio_data = []

        # the maximum amount of backups that remains in the backups folder
        self.MAX_BACKUPS = 5
        
        self.app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024
        self.app.config['DROPZONE_TIMEOUT'] = 0

        self.app.config['SECRET_KEY'] = 'super-geheim-sleutel-123'
        self.create_routes()

    def BackUpCurrentScreen_mp4(self, static_dir: Path) -> None:
        OldFile = static_dir / "Screen.mp4"
        if not OldFile.exists():
            print ("the file does not exist")
            return
        
        now=str(datetime.datetime.now())
        print (now)
        now = now.replace(':', '-')
        print (now)    

        newFile = static_dir / f"backups/{now}.mp4"
        newpath = static_dir / f"backups"
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        OldFile.rename(newFile) 

    def get_sorted_backups( self ) -> list[str]:
        backups_folder = Path(f"{os.getcwd()}/static/backups")

        if not os.path.exists(backups_folder):
            return []
        
        files = []
        for file in glob.glob(f"{backups_folder}/*.mp4"):
            files.append(file)
        files.sort(key=lambda x: os.path.getmtime(x))
        files.reverse()

        return files

    def remove_old_backups( self ):
        backup_files = self.get_sorted_backups()

        to_remove = backup_files[self.MAX_BACKUPS:]

        for file in to_remove:
            path = Path(file)
            path.unlink()
    
    def create_routes( self ) -> None:
         
        @self.socketio.on("connect") 
        def handle_connect():
            """Send initial application state to a newly connected client."""
            print("Client connected")

        @self.app.route("/", methods=["GET"])
        def index():
            return render_template( "index.html" ) 
        
        @self.app.route("/admin", methods=["GET"]) 
        def admin():
            if not session.get('logged_in'):
                return redirect(url_for('login'))  # Stuur door naar login als dat niet zo is

            # get backups
            backups = self.get_sorted_backups()

            # convert backups to dict containing url and a readable name
            # wo 07 okt 2026 11:36
            readable = []
            for file in backups:
                filename = Path(file).name.replace(".mp4", "")
                date_obj = datetime.datetime.strptime(filename, "%Y-%m-%d %H-%M-%S.%f")
                readable_date = date_obj.strftime("%a %d %b %Y %H:%M")
                readable_date = readable_date.replace(".", "")

                data = {
                    "name": readable_date,
                    "url": file.replace(os.getcwd(), "")
                }
                readable.append( data )

            return render_template( "admin.html", backups=readable )

        @self.app.route("/update", methods=["GET"])
        def update():
            self.socketio.emit("state")
            return "Update command sent!"

            
        @self.app.route("/upload", methods=["POST"])
        def upload():
            file = request.files["file"]
            if file:
                if Path(f"{file.filename}").suffix != '.mp4':
                    return
                
                # rename old ..
                folder= str(Path(__file__).resolve().parent)
                folder2 = Path(f"{folder}/static")
                print(folder)
                print(folder2)
                self.BackUpCurrentScreen_mp4(folder2)

                data = {
                    "number": random.randrange(20, 5000, 3)
                }

                file.save("static/Screen.mp4")
                self.remove_old_backups()
                self.socketio.emit("state", data)
                return "File uploaded successfully!"
            return "No file uploaded."

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            error = None
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                
                # Controleer de inloggegevens
                if username == self.ADMIN_USERNAME and password == self.ADMIN_PASSWORD:
                    session['logged_in'] = True  # Sla de inlogstatus op in de sessie
                    return redirect(url_for('admin'))
                else:
                    error = 'Onjuiste gebruikersnaam of wachtwoord.'
                    
            return render_template("login.html", error=error)

        @self.app.route('/logout')
        def logout():
            session.pop('logged_in', None)  # Verwijder de inlogstatus uit de sessie
            return redirect(url_for('login'))

        self.socketio.run(
            self.app, 
            debug=False,
            port=self.http_port, 
            host="0.0.0.0",
            allow_unsafe_werkzeug=True
        )

if __name__ == "__main__":
    try:
        locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")
    except locale.Error:
        locale.setlocale(locale.LC_TIME, "Dutch_Netherlands.1252")

    manager = Server()
    