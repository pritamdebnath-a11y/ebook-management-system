from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret123"

DATABASE = "ebooks.db"


# ------------------ DATABASE CONNECTION ------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------ INITIALIZE DATABASE ------------------
def init_db():
    if os.path.exists(DATABASE):
        return

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            content TEXT,
            image TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT
        );
    """)

    sample_books = [
        (
            "Operating Systems Concepts",
    "Abraham Silberschatz",
    699.0,
    "Core concepts of modern operating systems.",
    """An Operating System (OS) is system software that manages computer hardware,
software resources, and provides common services for computer programs.

This book explains fundamental OS concepts such as:
- Process management and CPU scheduling
- Threads and concurrency
- Deadlocks and synchronization
- Memory management and virtual memory
- File systems and disk management
- Input/Output systems and device drivers

The book provides theoretical explanations along with practical examples,
helping students understand how operating systems work internally.
""",
    "images/os.jpg",
        ),
        (
             "Computer Organization and Architecture",
    "William Stallings",
    640.0,
    "Understanding the internal working of computers.",
    """Computer Organization and Architecture deals with the structure and behavior
of computer systems from the hardware perspective.

Key topics covered include:
- Basic computer organization
- CPU architecture and instruction cycles
- Memory hierarchy and cache memory
- Input/Output organization
- Pipelining and parallel processing
- RISC and CISC architectures

This book bridges the gap between hardware and software, enabling students
to understand how programs are executed at the machine level.
""",
    "images/coa.jpg",
        ),
        (
            "Artificial Intelligence Fundamentals",
    "Stuart Russell",
    799.0,
    "Introduction to artificial intelligence concepts.",
    """Artificial Intelligence (AI) focuses on creating systems capable of
performing tasks that normally require human intelligence.

This book introduces:
- Intelligent agents and environments
- Problem-solving techniques
- Search algorithms
- Knowledge representation
- Machine learning basics
- Natural language processing
- Ethical issues in AI

The book provides a strong conceptual foundation for students entering
the fields of AI and machine learning.
""",
    "images/ai.jpg",
        ),
        (
            "Machine Learning with Python",
    "Sebastian Raschka",
    850.0,
    "Practical machine learning using Python.",
    """Machine Learning is a subset of artificial intelligence that enables
systems to learn from data without being explicitly programmed.

This book covers:
- Supervised and unsupervised learning
- Regression and classification algorithms
- Decision trees and ensemble methods
- Model evaluation and optimization
- Feature engineering
- Real-world ML applications using Python

The book combines theory with hands-on examples, making it suitable for
students and beginners in machine learning.
""",
    "images/ml.jpg",
        ),
        (
            "Web Development Fundamentals",
    "David Flanagan",
    520.0,
    "Basics of modern web development.",
    """Web development involves building and maintaining websites and web applications.
This book explains both frontend and backend fundamentals.

Topics include:
- HTML structure and semantics
- CSS styling and layouts
- JavaScript basics
- Client-server architecture
- Introduction to backend frameworks
- Web security fundamentals

It helps students understand how complete web applications are built
and deployed on the internet.
""",
    "images/wd.jpg",
        ),
        (
            "Database Management Systems",
    "Elmasri & Navathe",
    680.0,
    "Comprehensive guide to DBMS concepts.",
    """Database Management Systems (DBMS) are used to store, manage,
and retrieve data efficiently.

This book covers:
- Database models and schemas
- Entity-Relationship diagrams
- Relational algebra and SQL
- Normalization techniques
- Transaction management
- Indexing and query optimization
- Database security

It provides a solid foundation for understanding modern database systems
used in software applications.
""",
    "images/dbms.jpg",
        ),
        (
            "Software Testing Techniques",
    "Boris Beizer",
    560.0,
    "Principles and methods of software testing.",
    """Software testing is a critical phase in the software development lifecycle.
It ensures that the software is reliable, secure, and meets user requirements.

This book discusses:
- Testing fundamentals
- Black-box and white-box testing
- Unit, integration, and system testing
- Test case design techniques
- Debugging and error handling
- Automated testing concepts

The book helps students understand how quality assurance improves
software reliability and performance.
""",
    "images/st.jpg",
        ),
    ]

    cur.executemany(
        "INSERT INTO books (title, author, price, description, content, image) VALUES (?, ?, ?, ?, ?, ?)",
        sample_books,
    )

    conn.commit()
    conn.close()


# ------------------ HOME PAGE ------------------
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    cur = conn.cursor()

    if query:
        like = f"%{query}%"
        cur.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY title",
            (like, like),
        )
    else:
        cur.execute("SELECT * FROM books ORDER BY title")

    books = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM wishlist")
    wishlist_count = cur.fetchone()[0]

    conn.close()

    return render_template(
        "home.html",
        books=books,
        query=query,
        wishlist_count=wishlist_count,
    )


# ------------------ READ BOOK + REVIEWS ------------------
@app.route("/book/<int:book_id>")
def read_book(book_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cur.fetchone()

    cur.execute("SELECT * FROM reviews WHERE book_id = ? ORDER BY id DESC", (book_id,))
    reviews = cur.fetchall()

    conn.close()

    if book is None:
        return "Book not found", 404

    return render_template("read_book.html", book=book, reviews=reviews)


@app.route("/book/<int:book_id>/review", methods=["POST"])
def add_review(book_id):
    if "username" not in session:
        return redirect(url_for("login"))

    rating = int(request.form["rating"])
    comment = request.form["comment"]
    username = session["username"]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reviews (book_id, username, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (book_id, username, rating, comment, created_at),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("read_book", book_id=book_id))


# ------------------ WISHLIST ------------------
@app.route("/wishlist")
def wishlist():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT b.* FROM books b
        JOIN wishlist w ON b.id = w.book_id
        ORDER BY b.title
    """)
    books = cur.fetchall()

    conn.close()
    return render_template("wishlist.html", books=books)


@app.route("/wishlist/add/<int:book_id>")
def add_to_wishlist(book_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM wishlist WHERE book_id = ?", (book_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO wishlist (book_id) VALUES (?)", (book_id,))
        conn.commit()

    conn.close()
    return redirect(url_for("wishlist"))


# ------------------ AUTH ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password),
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------ RUN ------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

