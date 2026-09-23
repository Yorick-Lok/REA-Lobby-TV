
from flask import Flask, request, render_template
import os
import datetime
from pathlib import Path


class Server:
    def __init__( self ) -> None:
 
        # flask instance
        self.app = Flask(__name__)

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
        newFile = static_dir / f"old videos/{now}.mp4"
        OldFile.rename(newFile)

    
    def create_routes( self ) -> None:
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
                # rename old ..
                folder= str(Path(__file__).resolve().parent)
                folder2 = Path(f"{folder}/static")
                print(folder)
                print(folder2)
                self.BackUpCurrentScreen_mp4(folder2)

                file.save("static/Screen.mp4")
                return "File uploaded successfully!"
            return "No file uploaded."

    def run( self ) -> None: 
            self.app.run(
                debug=False,
                port=5000,
                host="0.0.0.0"
            )

if __name__ == "__main__":
    manager = Server()
    manager.run()
    