import os
import csv
from pymongo_get_database import get_database
from bson.objectid import ObjectId
import random
from PIL import Image
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect

# from cs50 import SQL
import requests

app = Flask(__name__)

dbname = get_database()
db = dbname["books"]


def getColour(imageUrl):
    r = requests.get(imageUrl)
    with open("temp_image", "wb") as f:
        f.write(r.content)
    image = Image.open("temp_image")
    width, height = image.size
    pix = image.load()
    red, green, blue = 0, 0, 0
    start = 5
    end = 10
    area = pow((end - start), 2)
    for row in range(start, end):
        for col in range(start, end):
            r, g, b = pix[col, row]
            red += r
            green += g
            blue += b
    red = int(red / area)
    green = int(green / area)
    blue = int(blue / area)
    rgb = (red, green, blue)
    return rgb


def colour_group(rgb_value):
    """Allocates an RGB value to a colour group based on a predefined chart."""

    color_chart = {
        (0, 0, 0): "Black",
        (255, 255, 255): "White",
        (255, 0, 0): "Red",
        (0, 255, 0): "Lime",
        (0, 0, 255): "Blue",
        (255, 255, 0): "Yellow",
        (0, 255, 255): "Cyan",
        (255, 0, 255): "Fuchsia",
        (192, 192, 192): "Silver",
        (128, 128, 128): "Grey",
        (128, 0, 0): "Maroon",
        (128, 128, 0): "Olive",
        (0, 128, 0): "Green",
        (128, 0, 128): "Purple",
        (0, 128, 128): "Teal",
        (0, 0, 128): "Navy",
    }

    closest_color = min(
        color_chart, key=lambda x: sum((a - b) ** 2 for a, b in zip(rgb_value, x))
    )
    return color_chart[closest_color]


@app.route("/", methods=["GET"])
def home():
    return redirect("/collection")


@app.route("/random", methods=["GET"])
def randombook():
    count = db.estimated_document_count() - 1
    number = random.randint(0, count)
    book = db.find().skip(number).limit(1)
    return render_template("collection.html", books=book, title="Random Selection")


@app.route("/", methods=["POST"])
def find():
    try:
        isbn = request.form.get("isbn")
        if len(isbn) not in (10, 13):
            raise ValueError("Invalid ISBN length. Please enter 10 or 13 digits.")
        if not isbn.isdigit():
            raise ValueError("Invalid ISBN format. Please enter only digits.")
    except ValueError as e:
        return render_template("error.html", title=e)
    except Exception as e:
        return render_template("error.html", title=e)

    if len(isbn) == 10:
        isbn = f"978{isbn}"
    GBooksURL = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(GBooksURL).json()
    book = response["items"][0]["volumeInfo"]
    title = book["title"].title()
    try:
        subtitle = book["subtitle"]
    except KeyError:
        subtitle = ""
    except Exception as e:
        return render_template("error.html", title=e)

    try:
        authors = book["authors"]
    except KeyError:
        subtitle = ""
    except Exception as e:
        return render_template("error.html", title=e)

    try:
        cover = book["imageLinks"]["thumbnail"]
    except KeyError:
        cover = "https://books.google.co.uk/googlebooks/images/no_cover_thumb.gif"
    except ValueError:
        cover = "https://books.google.co.uk/googlebooks/images/no_cover_thumb.gif"
    except Exception as e:
        return render_template("error.html", title=e)

    try:
        rgb = getColour(cover)
    except TypeError:
        rgb = (128, 0, 0)
    except Exception as e:
        return render_template("error.html", title=e)

    try:
        colour = colour_group(rgb)
    except ValueError:
        colour = "Maroon"
    except TypeError:
        colour = "Maroon"
    except Exception as e:
        return render_template("error.html", title=e)

    try:
        pageCount = book["pageCount"]
    except KeyError:
        pageCount = ""
    except Exception as e:
        return render_template("error.html", title=e)

    try:
        description = book["description"]
    except KeyError:
        description = ""
    except Exception as e:
        return render_template("error.html", title=e)

    try:
        year = book["publishedDate"]
    except KeyError:
        year = ""
    except Exception as e:
        return render_template("error.html", title=e)

    return render_template(
        "result.html",
        title=title,
        subtitle=subtitle,
        cover=cover,
        year=year[:4],
        authors=authors,
        colour=colour,
        pageCount=pageCount,
        isbn=isbn,
        description=description[:200],
    )


@app.route("/add", methods=["POST"])
def add():
    db.insert_one(
        {
            "title": request.form.get("title"),
            "subtitle": request.form.get("subtitle"),
            "year": request.form.get("year"),
            "author": request.form.get("authors"),
            "cover": request.form.get("cover"),
            "description": request.form.get("description"),
            "colour": request.form.get("colour"),
            "pageCount": request.form.get("pageCount"),
            "isbn": request.form.get("isbn"),
        }
    )
    return redirect("/collection")


@app.route("/collection", methods=["GET"])
def collection():
    books = db.find()
    return render_template("collection.html", books=books, title="Full Collection")


@app.route("/delete", methods=["POST"])
def delete():
    id = request.form.get("id")
    document_to_delete = {"_id": ObjectId(id)}
    try:
        db.delete_one(document_to_delete)
    except Exception as e:
        print(e)
    return redirect("/collection")


@app.route("/year", methods=["GET"])
def year():
    book = db.find().sort({"year": 1})
    return render_template("/collection.html", books=book, title="sorted by year")


@app.route("/titlesort", methods=["GET"])
def titlesort():
    book = db.find().sort({"title": 1})
    return render_template("/collection.html", books=book, title="sorted by title")


@app.route("/authorsort", methods=["GET"])
def authorsort():
    book = db.find().sort({"author": 1})
    return render_template("/collection.html", books=book, title="sorted by author")


@app.route("/pagecount", methods=["GET"])
def pagesort():
    book = db.find().sort({"pageCount": 1})
    return render_template("/collection.html", books=book, title="Sorted By Page Count")


@app.route("/colour", methods=["GET"])
def coloursort():
    book = db.find().sort({"colour": 1})
    return render_template("/collection.html", books=book, title="Sorted By Colour")


@app.route("/erase", methods=["GET"])
def rebuild():
    try:
        db.drop()
        return redirect("/collection")
    except Exception as e:
        return render_template("error.html", title=e)


@app.route("/import", methods=["GET"])
def load():
    return render_template("/import.html")


@app.route("/import", methods=["POST"])
def importcsv():
    def get_field(row, book, field, default):
        try:
            if field == "authors":
                return row[field] if row[field] else book["authors"][0]
            if field == "year":
                return row[field] if row[field] else book["publishedDate"][:4]
            return row[field] if row[field] else book[field]
        except KeyError:
            return default

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    if "file" not in request.files:
        return "No file part"
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(upload_dir, filename))
        # Now you can open and read the file:
        with open(os.path.join(upload_dir, filename), "r") as f:
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
                    return render_template("error.html", title=e)

                try:
                    rgb = getColour(cover)
                except TypeError:
                    rgb = (128, 0, 0)
                except ValueError:
                    rgb = (128, 0, 0)
                except Exception as e:
                    return render_template("error.html", title=e)

                colour = colour_group(rgb)
                title = get_field(row, book, "title", "").title()
                subtitle = get_field(row, book, "subtitle", "")
                year = get_field(row, book, "year", "")
                authors = get_field(row, book, "authors", "")
                pageCount = get_field(row, book, "pageCount", "")
                description = get_field(row, book, "description", "")
                db.insert_one(
                    {
                        "title": title,
                        "subtitle": subtitle,
                        "year": year,
                        "author": authors,
                        "cover": cover,
                        "pageCount": pageCount,
                        "colour": colour,
                        "description": description,
                        "isbn": isbn,
                    }
                )
    return redirect("/collection")


@app.route("/author", methods=["POST"])
def author():
    author = request.form.get("authors")
    books = db.find({"author": author})
    return render_template(
        "collection.html", books=books, title=f"{author}  Collection"
    )


@app.route("/title", methods=["POST"])
def title():
    title = request.form.get("q").lower()
    books = db.find({"title": {"$regex": title, "$options": "i"}})
    headline = f"titles containing {title}"
    return render_template("collection.html", books=books, title=headline)
