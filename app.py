from flask import Flask

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
    return "Hello, Students!"


@app.route("/about")
def about():
   return about_me


if __name__ == "__main__":
    app.run(debug=True)
