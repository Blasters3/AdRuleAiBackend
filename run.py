from dotenv import load_dotenv
load_dotenv()

from app import create_app
from flask import make_response, jsonify, request

app = create_app()

@app.before_request
def before_request():
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
            'Access-Control-Allow-Credentials': 'true',
        }
        return ('', 204, headers)

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = ['http://localhost:5173', 'http://127.0.0.1:5173']
    
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=True) 