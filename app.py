# import os
import csv
# import markdown
# import codecs
from flask import Flask, render_template, request, redirect
from cs50 import SQL
import requests

app = Flask(__name__)

db = SQL("sqlite:///booklog.db")


@app.route("/", methods=["GET"])
def home():
    # book = db.execute("SELECT * FROM books ORDER BY random() LIMIT 1")
    # return render_template("index.html", books=book)
    return redirect("/collection")

@app.route("/random", methods=["GET"])
def random():
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
    books = db.execute("SELECT * FROM books ORDER BY title")
    return render_template("collection.html", books=books, title="Full Collection")


@app.route("/delete", methods=["POST"])
def delete():
    id = request.form.get("id")
    db.execute("DELETE FROM books WHERE book_id = ?", id)
    return redirect("/collection")

@app.route("/erase", methods=["GET"])
def rebuild():
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
    filename = request.form.get("file")
    with open(filename, "r") as file:
        reader = csv.DictReader(file)
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
            
            db.execute(
                "INSERT INTO books (title, subtitle, year, authors, cover, description, isbn) VALUES (?, ?, ?, ?, ?, ?, ?)",
                row["title"],
                row["subtitle"],
                row["year"],
                row["authors"],
                cover,
                row["description"],
                row["isbn"]
            )
    return redirect("/collection")
