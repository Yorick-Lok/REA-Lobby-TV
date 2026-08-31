
from flask import Flask, request, render_template


class Server:
    def __init__( self ) -> None:
 
        # flask instance
        self.app = Flask(__name__)

        self.create_routes()

    def create_routes( self ) -> None:
        @self.app.route("/")
        def index():
            return render_template( "index.html" )

    def run( self ) -> None: 
            self.app.run(
                port=80,
                host="127.0.0.1"
            )

if __name__ == "__main__":
    manager = Server()
    manager.run()
    