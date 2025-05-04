from flask import Flask, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False


about_me = {
   "name": "Вадим",
   "surname": "Шиховцов",
   "email": "vshihovcov@specialist.ru"
}

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "author": "Mosher's Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]


@app.route("/") # Это первый URL, который мы будет обрабатывать
def hello_world(): 
    """ Это функция-обработчик, которая будет 
        вызвана приложением для обработки URL'a. """
    return jsonify(hello="Hello, Students!"), 200


@app.route("/about")
def about():
   return jsonify(about_me), 200


@app.get("/quotes")
def get_quotes():
    """ Функция преобразует список словарей в массив объектов JSON. """
    return jsonify(quotes)


@app.get("/params/<value>")
def get_params(value: str):
    """ Пример динамического URL'a."""
    return jsonify(param=value, value_type=str(type(value))), 200


# /quotes/1
# /quotes/2
# /quotes/3
# ...
# /quotes/n-1
# /quotes/n
@app.get("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id: int):
    """ Return quote by id from 'quotes' list."""
    for quote in quotes:
        if quote["id"] == quote_id:
            return jsonify(quote), 200
    return jsonify(error=f"Quote with id={quote_id} not found"), 404



if __name__ == "__main__":
    app.run(debug=True)
