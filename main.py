
from flask import Flask, request, render_template


class Server:
    def __init__( self ) -> None:
 
        # flask instance
        self.app = Flask(__name__)

        self.create_routes()

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
                file.save(f"static/{file.filename}")
                return "File uploaded successfully!"
            return "No file uploaded."

    def run( self ) -> None: 
            self.app.run(
                port=80,
                host="127.0.0.1"
            )

if __name__ == "__main__":
    manager = Server()
    manager.run()
    