
from flask import Flask, request, render_template
import os
import datetime
from flask_socketio import SocketIO, emit
from pathlib import Path
import random


class Server:
    def __init__( self ) -> None:
 
        # flask instance
        self.app = Flask(__name__)
        self.http_port = 5000
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading",)
        self.socketio_data = []
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
            return render_template( "admin.html" )
        
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
                self.socketio.emit("state", data)
                return "File uploaded successfully!"
            return "No file uploaded."

        self.socketio.run(
            self.app, 
            debug=False,
            port=self.http_port, 
            host="0.0.0.0",
            allow_unsafe_werkzeug=True
        )

if __name__ == "__main__":
    manager = Server()
    manager.run()
    