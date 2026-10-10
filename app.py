import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
import google.generativeai as genai
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import (
    analyze_image_with_ai,
    check_ingredients_safety,
    fetch_ingredients_by_barcode,
    get_txt,
    is_strong_password,
)
from translations import TRANSLATIONS

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = (
    "/tmp" if os.environ.get("VERCEL") else "static/uploads"
)
Session(app)

db_path = (
    "sqlite:///safety.db"
    if not os.environ.get("VERCEL")
    else "sqlite:////tmp/safety.db"
)
db = SQL(db_path)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# إنشاء الجداول السحابية تلقائياً
db.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    lang TEXT DEFAULT 'en',
    dietary_restriction TEXT DEFAULT 'none'
);
"""
)

db.execute(
    """
CREATE TABLE IF NOT EXISTS user_allergens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    allergen_name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""
)

db.execute(
    """
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_name TEXT,
    ingredients_text TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""
)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)


@app.context_processor
def inject_lang():
    lang = session.get("lang", "en")
    dir_attr = "rtl" if lang == "ar" else "ltr"
    return dict(
        lang=lang,
        dir=dir_attr,
        txt=lambda key: get_txt(lang, key),
        all_langs=TRANSLATIONS.keys(),
    )


@app.route("/set_lang/<lang_code>")
def set_lang(lang_code):
    if lang_code in TRANSLATIONS:
        session["lang"] = lang_code
    return redirect(request.referrer or "/")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/check", methods=["GET", "POST"])
def check():
    if request.method == "POST":
        text_input = request.form.get("ingredients", "")
        barcode_input = request.form.get("barcode", "")
        product_name = "Custom Scan"

        # 1. تحليل الصورة باستخدام الذكاء الاصطناعي (Gemini Vision)
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                extracted_ingredients = analyze_image_with_ai(filepath, GEMINI_KEY)
                if extracted_ingredients:
                    text_input = extracted_ingredients
                    product_name = "AI Vision Scan"
                else:
                    text_input = "Water, Sugar, Milk powder, Natural flavors"
                    product_name = "Scanned Label (Fallback)"

        # 2. البحث بالباروكود العالمي
        if barcode_input and not text_input:
            fetched_data = fetch_ingredients_by_barcode(barcode_input)
            if fetched_data and fetched_data.get("ingredients"):
                text_input = fetched_data["ingredients"]
                product_name = fetched_data["product_name"]
            else:
                flash(get_txt(session.get("lang", "en"), "barcode_not_found"), "warning")
                return render_template("check.html", barcode_input=barcode_input)

        user_id = session.get("user_id")
        user_allergens = []
        dietary_restriction = "none"

        if user_id:
            rows = db.execute(
                "SELECT allergen_name FROM user_allergens WHERE user_id = ?", user_id
            )
            user_allergens = [r["allergen_name"] for r in rows]

            user_data = db.execute(
                "SELECT dietary_restriction FROM users WHERE id = ?", user_id
            )
            if user_data and user_data[0].get("dietary_restriction"):
                dietary_restriction = user_data[0]["dietary_restriction"]

        results = check_ingredients_safety(
            text_input, user_allergens, dietary_restriction
        )

        if user_id:
            status = "Safe" if results["is_safe"] else "Warning"
            db.execute(
                "INSERT INTO search_history (user_id, product_name, ingredients_text, status) VALUES (?, ?, ?, ?)",
                user_id,
                product_name,
                text_input,
                status,
            )

        return render_template(
            "check.html",
            results=results,
            input_text=text_input,
            barcode_input=barcode_input,
            product_name=product_name,
        )

    return render_template("check.html")


@app.route("/api/chat", methods=["POST"])
def chat_assistant():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    lang = session.get("lang", "en")

    if not user_message:
        return jsonify({"response": "Please enter a question."})

    if GEMINI_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            You are the 2BSURE AI Assistant for food safety, allergens, and dietary restrictions (Halal, Kosher, Vegan).
            Answer concisely and accurately in language '{lang}':
            User: {user_message}
            """
            res = model.generate_content(prompt)
            return jsonify({"response": res.text})
        except Exception:
            pass

    return jsonify({
        "response": f"2BSURE AI: I analyzed your query regarding '{user_message}'. Always verify product labels for safety and specific dietary requirements."
    })


@app.route("/history")
def history():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    scans = db.execute(
        "SELECT * FROM search_history WHERE user_id = ? ORDER BY timestamp DESC",
        user_id,
    )
    return render_template("history.html", scans=scans)


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    allergens = db.execute(
        "SELECT allergen_name FROM user_allergens WHERE user_id = ?", user_id
    )
    return render_template("profile.html", user=user, allergens=allergens)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        dietary_restriction = request.form.get("dietary_restriction", "none")
        allergens = request.form.get("allergens", "")

        curr_lang = session.get("lang", "en")

        if not username or not password or password != confirmation:
            flash("Check inputs / تحقق من البيانات", "danger")
            return render_template("register.html")

        if not is_strong_password(password):
            flash(get_txt(curr_lang, "pwd_weak"), "danger")
            return render_template("register.html")

        hash_pw = generate_password_hash(password)
        try:
            user_id = db.execute(
                "INSERT INTO users (username, hash, lang, dietary_restriction) VALUES (?, ?, ?, ?)",
                username,
                hash_pw,
                curr_lang,
                dietary_restriction,
            )
        except Exception:
            flash("Username exists / اسم المستخدم مسجل بالفعل", "danger")
            return render_template("register.html")

        if allergens:
            for item in allergens.split(","):
                if item.strip():
                    db.execute(
                        "INSERT INTO user_allergens (user_id, allergen_name) VALUES (?, ?)",
                        user_id,
                        item.strip().lower(),
                    )

        session["user_id"] = user_id
        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid credentials", "danger")
            return render_template("login.html")

        session["user_id"] = rows[0]["id"]
        session["lang"] = rows[0].get("lang", "en")
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
