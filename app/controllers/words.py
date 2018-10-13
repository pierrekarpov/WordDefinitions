''' controller and routes for words '''
import os
from flask import request, jsonify
from app import app, mongo

ROOT_PATH = os.environ.get('ROOT_PATH')

@app.route('/word', methods=['GET', 'POST'])
def word():
    if request.method == 'GET':
        query = request.args
        data = mongo.db.words.find_one(query)
        return jsonify(data), 200

    data = request.get_json()
    if request.method == 'POST':
        if data.get('word', None) is not None and data.get('definition', None) is not None:
            mongo.db.words.insert_one(data)
            return jsonify({'ok': True, 'message': 'Word created successfully!'}), 200
        else:
            return jsonify({'ok': False, 'message': 'Bad request parameters!'}), 400
