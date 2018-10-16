# WordDefinitions
## See it live
The project is hosted on GCP here [http://35.240.243.255/](http://35.240.243.255/). Feel free to test the API endpoints there.

## Install
In the terminal, navigate to where you want the project to be.

Clone the project

```
git clone https://github.com/pierrekarpov/WordDefinitions.git
cd WordDefinitions
```

Add a .env file

`touch .env`

Fill in the environment details (unless otherwise specified, `OUT_PORT` should be `4000`)
You can get your Oxford API key for free [here](https://developer.oxforddictionaries.com/).
```
APP_ID=<Oxford API app id>
APP_KEY=<Oxford API key>
OUT_PORT=4000
TEST_KEY=<Any test key you want>
```

A preset list of words is located at `/data/words/words.txt`, you can add/remove words there.

Make sure you have Docker

`docker -v`

## Build and run
`docker-compose up --build`



## API endpoints
### Fetch definitions
`/word/fetch-definitions`

The app lookd through all the words from `/data/words/words.txt`, try to find them in the database. If there are not in the database, the app will call the Oxford API to get the definition, and add a new word document to the database.

method type: `GET`

optional parameter `forceRefresh`

If `forceRefresh` is set to one of these `["True", "true", "yes", "YES"]`, the app will call the Oxford API even if the word is in the database.

##### Examples:

###### URL `/word/fetch-definitions` (database is already filled)

status code `200`

```
{
  "insert_count": 0,
  "ok": true,
  "words": []
}
```

###### URL `/word/fetch-definitions?forceRefresh=true`

status code `200`

```
{
  "insert_count": 186,
  "ok": true,
  "words": [
    {
      "definition": "used to refer to the whole quantity or extent of a particular group or thing",
      "word": "all"
    },
    {
      "definition": "physically strong, fit, and active",
      "word": "athletic"
    },
    {
      "definition": "having the power, skill, means, or opportunity to do something",
      "word": "able"
    },
    ...
  ]
}
```

### Get word definition
`/word?word=<word_to_search>`

The app will look through our database for `<word_to_search>` and return the word and its definition.

method type: `GET`

required parameter `word`

##### Examples:

###### URL `/word?word=apple`

status code `200`

```
{
  "definition": "the round fruit of a tree of the rose family, which typically has thin green or red skin and crisp flesh.",
  "word": "apple"
}
```

###### URL `/word?word=applesss`

status code `200`

```
{
  "definition": "<definition not in database>",
  "word": "applesss"
}
```

###### URL `/word?word=analyze`

status code `200`

```
{
  "definition": "<could not get definition from oxforddictionaries API>",
  "word": "analyze"
}
```

###### URL `/word`

status code `400`

```
{
  "message": "Bad request parameters!"
}
```

## API testing endpoints

Tests are destructive, so you will need to provide a `testKey` matching your environment `TEST_KEY`. You will have access to the following:

### Test word endpoint
`/test/word?testKey=<your_test_key>`

This enpoint will test the `/word` endpoint by giving it existing, absent, abnormal, and malformed parameters.


### Test fetch definitions add endpoint
`/test/word/fetch-definitions/add?testKey=<your_test_key>`

This enpoint will test the `/word/fetch-definitions` endpoint. This will empty the database and make sure it is empty, fill it by fetching the definitions and make sure all the data is here. And fetch the data again and make sure no extra data was added nor any data was modified.

### Test fetch definitions forceRefresh endpoint
`/test/word/fetch-definitions/forceRefresh?testKey=<your_test_key>`

This enpoint will test the `/word/fetch-definitions` endpoint. It will get the definitions and make sure all the data is here. It will delete a definition and fetch again, then it will check that the data has been added back. It will modify a document and fetch the data again. It will make sure we do not overwrite the data by calling the Oxford API. It will finally fetch the definitions with the `forceRefresh` flag on, and check that the data was indeed overwritten.


## Implementation details
Most of the computing is done in `app/controllers/words.py`.

The `word.txt` file has word duplicates. To avoid creating duplicate documents in the database, we temporarily put the words in a set object, to ensure no duplicates are present. We then go through the set of unique words and check their definitions in the db or through the Oxford API.

For the time being, the Oxford API requests are called sequentially, which makes `/word/fetch-definitions` run for up to a couple of minutes. Oxford API allows only 60 requests per minute for free, so calling the APIs sequentially is necessary. This is a clear bottleneck that can be optimized later in the future under a premium paid plan.

The `OUT_PORT` environment variable is needed because on your machine, you will most likely need to listen to the `4000` port. But on my GCP virtual machine, I forwarded the app to port `80`. Having `OUT_PORT` in the `.env` file allows me to have the exact same codebase on my computer and on my VM.

For the time being, testing is done through API endpoints because it is easier to set up for both local machine and virtual machine. In the future, using `unittest` or `pytest` is more advisable.
