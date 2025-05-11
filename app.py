from flask import Flask, abort, jsonify, request, g
from random import choice
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db"  # <- тут путь к БД

app = Flask(__name__)
app.json.ensure_ascii = False


def make_dicts(cursor, row):
    """ Create dicts from db results."""
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(path_to_db)
    db.row_factory = make_dicts
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('./db_sql/db_data.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def check(data: dict, check_rating=False) -> tuple[bool, dict]:
    keys = ('author', 'text', 'rating')
    if check_rating:
        rating = data.get('rating')    
        if rating and rating not in range(1, 6):
            return False, {"error": "Rating must be between 1 and 5"}
    
    if set(data.keys()) - set(keys):
        return False, {"error": "Invalid fields to create/update"}
    return True, data
         

@app.get("/quotes")
def get_quotes():
    """ Функция возвращает все цитаты из БД. """
    select_quotes = "SELECT * from quotes"
    quotes = query_db(select_quotes) # now get list[dict]
    return jsonify(quotes), 200


@app.get("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id: int):
    """ Return quote by id from db."""
    quote_select = "SELECT * FROM quotes WHERE id=?"
    quote = query_db(quote_select, (quote_id,), one=True)
    if quote:
        return jsonify(quote), 200
    return jsonify(error=f"Quote with id={quote_id} not found"), 404


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
        cursor.execute(insert_quote, tuple(new_quote.values()))
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
    if not path_to_db.exists():
        init_db()
    app.run(debug=True)


