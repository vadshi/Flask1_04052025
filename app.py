from flask import Flask, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False


about_me = {
   "name": "Вадим",
   "surname": "Шиховцов",
   "email": "vshihovcov@specialist.ru"
}


@app.route("/") # Это первый URL, который мы будет обрабатывать
def hello_world(): 
    """ Это функция-обработчик, которая будет 
        вызвана приложением для обработки URL'a. """
    return jsonify(hello="Hello, Students!"), 200


@app.route("/about")
def about():
   return jsonify(about_me), 200


if __name__ == "__main__":
    app.run(debug=True)
