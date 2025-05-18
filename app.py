from flask import Flask, abort, jsonify, request, g
from pathlib import Path
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, func, ForeignKey
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError
from flask_migrate import Migrate



class Base(DeclarativeBase):
    pass


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "quotes.db"  # <- тут путь к БД

app = Flask(__name__)
app.json.ensure_ascii = False

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{path_to_db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):
    __tablename__ = 'authors'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), index=True, unique=True)
    quotes: Mapped[list['QuoteModel']] = relationship(back_populates='author', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {"id": self.id, "name": self.name}
    

class QuoteModel(db.Model):
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(server_default="1")

    def __init__(self, author, text, rating=1):
        self.author = author
        self.text  = text
        self.rating = rating

    def __repr__(self):
        return f'Quote{self.id, self.author}'  
    
    def to_dict(self):
        return {
            "quote_id": self.id,
            "text": self.text,
            "rating": self.rating
        }
    

def check(data: dict, check_rating=False) -> tuple[bool, dict]:
    keys = ('author', 'text')
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


def add_to_db(cls, data):
    """ Function to work with db layer """
    try:
        new_instance = cls(**data)
        db.session.add(new_instance)
        db.session.commit()
    except TypeError:
        abort(400, f"Invalid data. Required: <name>. Received: {', '.join(data.keys())}")
    except Exception as e:
        abort(503, f"Database error: {str(e)}")
    return jsonify(new_instance.to_dict()), 201


# ====== Authors endpoints =======
@app.post("/authors")
def create_author():
    author_data = request.json
    # add_to_db(AuthorModel, author_data)  # Variant 2
    try:
        author = AuthorModel(**author_data)
        db.session.add(author)
        db.session.commit()
    except TypeError:
        abort(400, f"Invalid data. Required: <name>. Received: {', '.join(author_data.keys())}")
    except Exception as e:
        abort(503, f"Database error: {str(e)}")
    return jsonify(author.to_dict()), 201


# URL: "/authors/<int:author_id>/quotes"
@app.route("/authors/<int:author_id>/quotes", methods=["GET", "POST"])
def author_quotes(author_id: int):
    author = db.get_or_404(AuthorModel, author_id, description=f"Author with id={author_id} not found")

    if request.method == "GET":
        quotes = [quote.to_dict() for quote in author.quotes]
        return jsonify({"author": author.name} | {"quotes": quotes}), 200

    elif request.method == "POST":
        data = request.json
        new_quote = QuoteModel(author, **data)
        db.session.add(new_quote)
        db.session.commit()
        return jsonify(new_quote.to_dict() | { "author_id" : author.id}), 201
    else:
        abort(405)


# ====== Quotes endpoints =======
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
    quote = db.get_or_404(entity=QuoteModel, ident=quote_id, description=f"Quote with id={quote_id} not found")
    return jsonify(quote.to_dict()), 200



@app.get("/quotes/count")
def get_quotes_count() -> int:
    """ Return count of quotes in db."""
    count = db.session.scalar(func.count(QuoteModel.id))
    return jsonify(count=count), 200


@app.post("/quotes")
def create_quote():
    """ Function creates new quote and adds it to db."""
    data = request.json
    try:
        quote = QuoteModel(**data)
        db.session.add(quote)
        db.session.commit()
    except TypeError:
        abort(400, f"Invalid data. Required: <author> and <text>. Received: {', '.join(data.keys())}")
    except Exception as e:
        abort(503, f"Database error: {str(e)}")
    
    return jsonify(quote.to_dict()), 201
    


@app.put("/quotes/<int:quote_id>")
def edit_quote(quote_id: int):
    """ Update an existing quote """
    new_data = request.json
    result = check(new_data, check_rating=True)
    if not result[0]:
        return abort(400, result[1].get('error'))
    
    quote = db.get_or_404(entity=QuoteModel, ident=quote_id, description=f"Quote with id={quote_id} not found")

    try:
        for key_as_attr, value in new_data.items():
            setattr(quote, key_as_attr, value)

        db.session.commit()
        return jsonify(quote.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(503, f"Database error: {str(e)}")


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    """Delete quote by id """
    quote = db.get_or_404(entity=QuoteModel, ident=quote_id, description=f"Quote with id={quote_id} not found")
    db.session.delete(quote)
    try:
        db.session.commit()
        return jsonify({"message": f"Quote with id {quote_id} has deleted."}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(503, f"Database error: {str(e)}")
    
    
@app.route("/quotes/filter", methods=['GET'])
def filter_quotes():
    data = request.args # get query parameters from URL
    try:
        quotes = db.session.scalars(db.select(QuoteModel).filter_by(**data)).all()
    except InvalidRequestError:
        abort(400, f"Invalid data. Required: <author> and <text>. Received: {', '.join(data.keys())}")
    
    return jsonify([quote.to_dict() for quote in quotes]), 200


if __name__ == "__main__":
    app.run(debug=True)


