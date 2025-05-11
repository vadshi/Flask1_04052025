from flask import Flask, jsonify, request
from random import choice


app = Flask(__name__)
app.json.ensure_ascii = False

KEYS = ('author', 'text', 'rating')

about_me = {
   "name": "Вадим",
   "surname": "Шиховцов",
   "email": "vshihovcov@specialist.ru"
}

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает.",
       "rating": 4
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках.",
       "rating": 3
   },
   {
       "id": 6,
       "author": "Mosher's Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили.",
       "rating": 4
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так.",
       "rating": 2
       
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
    # print(vars(request))
    print(f'{request.path}')
    print(f'{request.url}')
    # print(f'{request.json}')  # Словарь с данными из тела запроса
    print(f'{request.args}')  # Словарь с данными(query parameters)
    return jsonify(param=value, value_type=str(type(value))), 200


@app.get("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id: int):
    """ Return quote by id from 'quotes' list."""
    for quote in quotes:
        if quote["id"] == quote_id:
            return jsonify(quote), 200
    return jsonify(error=f"Quote with id={quote_id} not found"), 404


@app.get("/quotes/count")
def get_quotes_count() -> int:
    """ Return count of quotes """
    return {"count": len(quotes)}


@app.get("/quotes/random")
def get_random_quotes():
    """ Return random quote."""
    return jsonify(choice(quotes))


def generate_new_id():
    """New id для цитаты"""
    if not quotes:
        return 1
    return quotes[-1]["id"] + 1


@app.route("/quotes", methods=['POST'])
def create_quote():
    """ Function creates new quote and adds it to the list of quotes"""
    new_quote = request.json
    if not set(new_quote.keys()) - set(KEYS):
        new_id = generate_new_id()
        new_quote["id"]= new_id
        new_quote["rating"] = 1
        quotes.append(new_quote)
    else:
        return jsonify(error="Send bad data to create new quote"), 400
    return jsonify(new_quote), 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    new_data = request.json
    if not set(new_data.keys()) - set(KEYS):
        for quote in quotes:
            if quote["id"] == quote_id:
                if "rating" in new_data and new_data['rating'] not in range(1, 6):  # Проверяем корректность рейтинга
                    new_data.pop('rating')                   
                quote.update(new_data)
                return jsonify(quote), 200
    else:
        return jsonify(error="Send bad data to update"), 400
    return jsonify({"error": f"Quote with id={quote_id} not found"}), 404


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    """Удаление цитат"""
    for i, quote in enumerate(quotes):
        if quote["id"] == quote_id:
            del quotes[i]
            return jsonify({"message": f"Quote with id {quote_id} is deleted."}), 200
    return jsonify({"error": "Quote not found"}), 404


@app.route("/quotes/filter", methods=['GET'])
def filter_quotes():
    """Поиск по фильтру"""
    author = request.args.get('author')
    rating = request.args.get('rating')
    filtered_quotes = quotes[:]

    if author:
        filtered_quotes = [quote for quote in filtered_quotes if quote['author'] == author]
    if rating:
        filtered_quotes = [quote for quote in filtered_quotes if str(quote['rating']) == rating]

    return jsonify(filtered_quotes), 200


@app.route("/quotes/filter_v2", methods=['GET'])
def filter_quotes_v2():
    """Поиск по фильтру"""
    filtered_quotes = quotes.copy()
    # Цикл по query parameters
    for key, value in request.args.items():
        result = []
        if key not in KEYS:
            return jsonify(error=f"Invalid param={value}"), 400
        if key == 'rating':
            value = int(value)
        for quote in filtered_quotes:
            if quote[key] == value:
                result.append(quote)     
        filtered_quotes = result.copy()

    return jsonify(filtered_quotes), 200


if __name__ == "__main__":
    app.run(debug=True)


