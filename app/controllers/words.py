''' controller and routes for words '''
import os
import json
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
            # NOTE: if word is not in the database, show <definition not in database> as definition
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

    #NOTE: if cannot get data from API, store <could not get definition from oxforddictionaries API> as definition
    d = "<could not get definition from oxforddictionaries API>"
    if res.status_code == 200:
        # NOTE: try/except to handle when response has no or invalid results
        try:
            d = res.json()["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]["definitions"][0]
        except KeyError:
            pass

    return d

@app.route("/word/fetch-definitions", methods=["GET"])
def fetch_definitions():
    args = request.args
    words = set()
    # NOTE: no official str to bool type checking, here is our own
    true_strings = ["True", "true", "yes", "YES"]

    # NOTE: save words.txt file in <root>/data/words
    with open(os.path.join(ROOT_PATH, "data/words/words.txt"), "r") as f:
        for line in f:
            for word in line.split():
                words.add(word)

    res_words = []
    for w in words:
        data = mongo.db.words.find_one({"word": w})

        # NOTE: optional flag to force a refresh,
        #       we will call the API only if the word in not in our database, or if the flag is up
        is_force_refresh = args and args["forceRefresh"] and args["forceRefresh"] in true_strings
        should_fetch = data is None or is_force_refresh

        if should_fetch:
            d = get_definition(w)
            # NOTE: upsert operation: updat if exist, if not, insert
            mongo.db.words.update_one({"word": w}, {"$set": {"definition": d}}, True)
            res_words.append({"word": w, "definition": d})

    return jsonify({"ok": True, "insert_count": len(res_words), "words": res_words}), 200


@app.route("/test/word", methods=["GET"])
def test_word():
    test_data = [
        {"word": "applesss", "expected": "<definition not in database>"},
        {"word": "apple", "expected": "the round fruit of a tree of the rose family, which typically has thin green or red skin and crisp flesh."},
        {"word": "analyze", "expected": "<could not get definition from oxforddictionaries API>"},
        {"word": "attack", "expected": "take aggressive military action against (a place or enemy forces) with weapons or armed force"},
        {"word": "arrest", "expected": "seize (someone) by legal authority and take them into custody"},
        {"word": "acorn", "expected": "<definition not in database>"},
        {"word": "jhjhgjhgjhghj", "expected": "<definition not in database>"},
        {"word": "", "expected": "<definition not in database>"},
        {"word": -15543, "expected": "<definition not in database>"},
        {"word": True, "expected": "<definition not in database>"},
        {"word": False, "expected": "<definition not in database>"},
        {"word": None, "expected": "Bad request parameters!"}
    ]
    results = []
    success_count = 0

    fetch_definitions()

    for t in test_data:
        print t
        request.args = {"word": t["word"]}
        # NOTE: calling the function associated with route /word
        res, _ = word()
        data = json.loads(res.get_data())

        # NOTE: special case when word argument is not provided
        if t["word"] is not None:
            t["actual"] = data["definition"]
        else:
            t["actual"] = data["message"]

        t["success"] = t["expected"] == t["actual"]
        if t["success"]:
            success_count = success_count + 1
        results.append(t)

    results_str = "Passed " + str(success_count) + " tests out of " + str(len(test_data))
    return jsonify({"ok": True, "summary": results_str, "results": results}), 200
