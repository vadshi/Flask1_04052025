from flask import Flask, abort, jsonify, request, g
from pathlib import Path
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class Base(DeclarativeBase):
    pass


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "main.db"  # <- тут путь к БД

app = Flask(__name__)
app.json.ensure_ascii = False

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{path_to_db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)


class QuoteModel(db.Model):
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(String(255))

    def __init__(self, author, text):
        self.author = author
        self.text  = text

    def __repr__(self):
        return f'Quote{self.id, self.author}'  # Quote(1, 'Mark Twen')
    
    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "text": self.text
        }
    


# ===============================
#  Функци-заглушки
query_db = get_db = lambda : ...
# ===============================


def check(data: dict, check_rating=False) -> tuple[bool, dict]:
    keys = ('author', 'text', 'rating')
    if check_rating:
        rating = data.get('rating')    
        if rating and rating not in range(1, 6):
            return False, {"error": "Rating must be between 1 and 5"}
    
    if set(data.keys()) - set(keys):
        return False, {"error": "Invalid fields to create/update"}
    return True, data
         

@app.errorhandler(HTTPException)
def handle_exception(e):
    """ Функция для перехвата HTTP ошибок и возврата в виде JSON."""
    return jsonify({"error": str(e)}), e.code


@app.get("/quotes")
def get_quotes():
    """ Функция возвращает все цитаты из БД. """
    quotes_db = db.session.scalars(db.select(QuoteModel)).all()
    # Формируем список словарей
    quotes = []
    for quote in quotes_db:
        quotes.append(quote.to_dict())
    return jsonify(quotes), 200


@app.get("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id: int):
    """ Return quote by id from db."""
    quote = db.get_or_404(QuoteModel, quote_id, description=f"Quote with id={quote_id} not found")
    return jsonify(quote.to_dict()), 200



@app.get("/quotes/count")
def get_quotes_count() -> int:
    """ Return count of quotes in db."""
    quantity_select = """SELECT COUNT(*) as count FROM quotes"""
    cursor = get_db().cursor()
    count = cursor.execute(quantity_select).fetchone()
    return jsonify(count), 200


@app.post("/quotes")
def create_quote():
    """ Function creates new quote and adds it to db."""
    if (result := check(request.json))[0]:
        new_quote = result[1]
        new_quote["rating"] = 1
        insert_quote = "INSERT INTO quotes (author, text, rating) VALUES (?, ?, ?)"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql=insert_quote, parameters=tuple(new_quote.values()))
        try:
            conn.commit()
        except Exception as e:
            conn.rollback()
            abort(503, f"error: {str(e)}")
        else:
            new_quote['id'] = cursor.lastrowid
            return jsonify(new_quote), 201
    
    return jsonify(result[1]), 400
    


@app.put("/quotes/<int:quote_id>")
def edit_quote(quote_id: int):
    """Update an existing quote"""
    new_data = request.json
    result = check(new_data, check_rating=True)
    if not result[0]:
        return jsonify(result[1]), 400
    
    conn = get_db()
    cursor = conn.cursor()

    # Создаем кортеж значений для подстановки и список строк из полей для обновления
    update_values = list(new_data.values())
    update_fieds = [f'{key} = ?' for key in new_data]

    if not update_fieds:
        return jsonify(error="No valid update fields provided."), 400
    

    update_values.append(quote_id)
    update_query = f""" UPDATE quotes SET {', '.join(update_fieds)} WHERE id = ? """
    cursor.execute(update_query, update_values)
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(503, f"error: {str(e)}")

    if cursor.rowcount == 0:
        return jsonify({"error": f"Quote with id={quote_id} not found"}), 404
    
    response, status_code = get_quote_by_id(quote_id)
    if status_code == 200:
        return response, 200
    abort(404, {"error": f"Quote with id={quote_id} not found"})


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    """Delete quote by id """
    delete_quote = "DELETE FROM quotes WHERE id=?"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(delete_quote, (quote_id, ))
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        abort(503, f"error: {str(e)}")

    if cursor.rowcount == 0:
        return jsonify({"error": f"Quote with id={quote_id} not found"}), 404
    return jsonify({"message": f"Quote with id {quote_id} has deleted."}), 200
    

# Homework
# TODO: change filter endpoint to work with db

# @app.route("/quotes/filter", methods=['GET'])
# def filter_quotes():
#     """Поиск по фильтру"""
#     author = request.args.get('author')
#     rating = request.args.get('rating')
#     filtered_quotes = quotes[:]

#     if author:
#         filtered_quotes = [quote for quote in filtered_quotes if quote['author'] == author]
#     if rating:
#         filtered_quotes = [quote for quote in filtered_quotes if str(quote['rating']) == rating]

#     return jsonify(filtered_quotes), 200


# @app.route("/quotes/filter_v2", methods=['GET'])
# def filter_quotes_v2():
#     """Поиск по фильтру"""
#     filtered_quotes = quotes.copy()
#     # Цикл по query parameters
#     for key, value in request.args.items():
#         result = []
#         if key not in KEYS:
#             return jsonify(error=f"Invalid param={value}"), 400
#         if key == 'rating':
#             value = int(value)
#         for quote in filtered_quotes:
#             if quote[key] == value:
#                 result.append(quote)     
#         filtered_quotes = result.copy()

#     return jsonify(filtered_quotes), 200


if __name__ == "__main__":
    app.run(debug=True)


