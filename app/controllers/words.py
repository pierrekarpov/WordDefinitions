''' controller and routes for words '''
import os
from flask import request, jsonify
import requests as r
from app import app, mongo

ROOT_PATH = os.environ.get("ROOT_PATH")

# @app.route("/word", methods=["GET", "POST"])
@app.route("/word", methods=["GET"])
def word():
    if request.method == "GET":
        query = request.args
        if query.get("word", None) is not None:
            word = mongo.db.words.find_one({"word": query["word"]})
            definition = word["definition"] if word is not None else "<definition not in database>"
            res = {"word": query["word"], "definition": definition}
            return jsonify(res), 200
        else:
            return jsonify({"message": "Bad request parameters!"}), 400

    # data = request.get_json()
    # if request.method == "POST":
    #     if data.get("word", None) is not None and data.get("definition", None) is not None:
    #         mongo.db.words.insert_one(data)
    #         return jsonify({"ok": True, "message": "Word created successfully!", "data": data}), 200
    #     else:
    #         return jsonify({"ok": False, "message": "Bad request parameters!"}), 400

# @app.route("/word/all", methods=["GET"])
# def all_words():
#     words = []
#     cursor = mongo.db.words
#
#     for w in cursor.find():
#         words.append(w)
#
#     return jsonify({"ok": True, "wordCount": len(words), "words": words}), 200
#
# @app.route("/word/all/delete", methods=["DELETE"])
# def delete_all_words():
#     mongo.db.words.delete_many({})
#     return jsonify({"ok": True, "message": "all words deleted"}), 200

def get_definition(w):
    APP_ID = os.getenv("APP_ID")
    APP_KEY = os.getenv("APP_KEY")
    language = "en"
    word_id = w
    url = "https://od-api.oxforddictionaries.com:443/api/v1/entries/" + language + "/" + word_id.lower()

    res = r.get(url, headers={"app_id": APP_ID, "app_key": APP_KEY})

    d = "<could not get definition from oxforddictionaries API>"
    if res.status_code == 200:
        try:
            d = res.json()["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]["definitions"][0]
        except KeyError:
            pass

    return d

@app.route("/word/fetch-definitions", methods=["GET"])
def fetch_definitions():
    args = request.args
    words = set()
    true_strings = ["True", "true", "yes", "YES"]
    with open(os.path.join(ROOT_PATH, "data/words/words.txt"), "r") as f:
        for line in f:
            for word in line.split():
                words.add(word)

    res_words = []
    for w in words:
        data = mongo.db.words.find_one({"word": w})
        is_force_refresh = args and args["forceRefresh"] and args["forceRefresh"] in true_strings
        should_fetch = data is None or is_force_refresh

        if should_fetch:
            d = get_definition(w)
            mongo.db.words.update_one({"word": w}, {"$set": {"definition": d}}, True)
            res_words.append({"word": w, "definition": d})

    return jsonify({"ok": True, "insert_count": len(res_words), "words": res_words}), 200
