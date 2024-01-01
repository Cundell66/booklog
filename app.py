import os
import csv
import tempfile
# import codecs
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for
from cs50 import SQL
import requests

app = Flask(__name__)

# db = SQL("sqlite:///booklog.db")

@app.route('/get_remote_db')
def get_remote_db():
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.TemporaryFile() as temp_db:
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        return SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db



@app.route("/", methods=["GET"])
def home():
    # book = db.execute("SELECT * FROM books ORDER BY random() LIMIT 1")
    # return render_template("index.html", books=book)
    return redirect("/collection")

@app.route("/random", methods=["GET"])
def random():
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.TemporaryFile() as temp_db:
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
        book = db.execute("SELECT * FROM books ORDER BY random() LIMIT 1")
    return render_template("index.html", books=book)

@app.route("/", methods=["POST"])
def find():
    isbn = request.form.get("isbn")
    GBooksURL = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(GBooksURL).json()
    book = response["items"][0]["volumeInfo"]
    title = book["title"]
    try:
        subtitle = book["subtitle"]
    except KeyError:
        subtitle = ""
    except Exception as e:
        print(e)

    try:
        authors = book["authors"]
    except KeyError:
        subtitle = ""
    except Exception as e:
        print(e)

    try:
        cover = book["imageLinks"]["thumbnail"]
    except KeyError:
        cover = "https://books.google.co.uk/googlebooks/images/no_cover_thumb.gif"
    except ValueError:
        cover = "https://books.google.co.uk/googlebooks/images/no_cover_thumb.gif"
    except Exception as e:
        print(e)

    try:
        description = book["description"]
    except KeyError:
        description = ""
    except Exception as e:
        print(e)

    try:
        year = book["publishedDate"]
        print(year)
    except KeyError:
        year = ""
    except Exception as e:
        print(e)

    return render_template(
        "result.html",
        title=title,
        subtitle=subtitle,
        cover=cover,
        year=year[:4],
        authors=authors,
        isbn=isbn,
        description=description[:200],
    )


@app.route("/add", methods=["POST"])
def add():
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.TemporaryFile() as temp_db:
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
        db.execute(
        "INSERT INTO books (title, subtitle, year, authors, cover, description, isbn) VALUES (?, ?, ?, ?, ?, ?, ?)",
            request.form.get("title"),
            request.form.get("subtitle"),
            request.form.get("year"),
            request.form.get("authors"),
            request.form.get("cover"),
            request.form.get("description"),
            request.form.get("isbn"),
        )
    return redirect("/collection")


@app.route("/collection", methods=["GET"])
def collection():
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.NamedTemporaryFile() as temp_db:
        print("temp db path: ", temp_db.name)
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
        books = db.execute("SELECT * FROM books ORDER BY title")
    return render_template("collection.html", books=books, title="Full Collection")


@app.route("/delete", methods=["POST"])
def delete():
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.TemporaryFile() as temp_db:
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
        id = request.form.get("id")
        db.execute("DELETE FROM books WHERE book_id = ?", id)
    return redirect("/collection")

@app.route("/erase", methods=["GET"])
def rebuild():
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.TemporaryFile() as temp_db:
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
        try:
            db.execute("DELETE FROM books")
            db.execute("DELETE FROM sqlite_sequence WHERE name = 'books'")
            return redirect("/collection")
        except Exception as e:
            return str(e)

@app.route("/import", methods=["GET"])
def load():
    return render_template("/import.html")

@app.route("/import", methods=["POST"])
def importcsv():
    def get_field(row, book, field, default):
        try:
            if field == "year":
                return row[field] if row[field] else book["publishedDate"]
            return row[field] if row[field] else book[field]
        except KeyError:
            return default
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
        
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(upload_dir, filename))
        # Now you can open and read the file:
        with open(os.path.join(upload_dir, filename), 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                isbn = row["isbn"]
                GBooksURL = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
                response = requests.get(GBooksURL).json()
                book = response["items"][0]["volumeInfo"]
                try:
                    cover = book["imageLinks"]["thumbnail"]
                except KeyError:
                    cover = "https://books.google.co.uk/googlebooks/images/no_cover_thumb.gif"
                except ValueError:
                    cover = "https://books.google.co.uk/googlebooks/images/no_cover_thumb.gif"
                except Exception as e:
                    print(e)
            
                title = get_field(row, book, "title", "")
                subtitle = get_field(row, book, "subtitle", "")
                year = get_field(row, book, "year", "")
                authors = get_field(row, book, "authors", "")
                description = get_field(row, book, "description", "")
                response = requests.get('https://viral.cundell.com/booklog.db')
                with tempfile.TemporaryFile() as temp_db:
                    temp_db.write(response.content)
                    temp_db.seek(0) # Rewind to the beginning of the file
                    db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
                    db.execute(
                    "INSERT INTO books (title, subtitle, year, authors, cover, description, isbn) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    title,
                    subtitle,
                    year,
                    authors,
                    cover,
                    description,
                    isbn
                )
    return redirect("/collection")

@app.route("/author", methods=["POST"])
def author():
    author = request.form.get("authors")
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.TemporaryFile() as temp_db:
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
        books = db.execute("SELECT * FROM books WHERE authors = ? ORDER BY title", author)
    return render_template("collection.html", books=books, title=f"{author}  Collection")

@app.route("/title", methods=["POST"])
def title():
    title = request.form.get("q")
    response = requests.get('https://viral.cundell.com/booklog.db')
    with tempfile.TemporaryFile() as temp_db:
        temp_db.write(response.content)
        temp_db.seek(0) # Rewind to the beginning of the file
        db = SQL("sqlite:///{}".format(temp_db.name)) # connect to temporary db
        books = db.execute("SELECT * FROM books WHERE title LIKE ?", "%" + title + "%")
    headline = f"titles containing {title}"
    return render_template("collection.html", books=books, title=headline)

