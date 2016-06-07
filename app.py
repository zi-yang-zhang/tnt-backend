from flask import Flask
from router import router_blueprint
app = Flask(__name__)
app.register_blueprint(router_blueprint)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=2001)
