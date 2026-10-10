import os
import re
import requests
import google.generativeai as genai
from translations import TRANSLATIONS


def get_txt(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


def is_strong_password(password):
    """
    التحقق من قوة كلمة المرور (8+ خانات، حرف كبير، حرف صغير، رقم، ورمز خاص)
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def analyze_image_with_ai(image_path, api_key):
    """استخراج المكونات من صورة المنتج باستخدام Gemini AI (Vision OCR)"""
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        uploaded_file = genai.upload_file(image_path)
        prompt = (
            "Extract ONLY the list of ingredients from this product label image. "
            "Return them as a clean, comma-separated list of ingredients. Do not include extra text."
        )
        response = model.generate_content([uploaded_file, prompt])
        return response.text.strip() if response and response.text else None
    except Exception:
        return None


def fetch_ingredients_by_barcode(barcode):
    if not barcode:
        return None
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode.strip()}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                ingredients = product.get("ingredients_text") or product.get(
                    "ingredients_text_en"
                )
                product_name = product.get("product_name", "Unknown Product")
                return {
                    "ingredients": ingredients or "No ingredients listed",
                    "product_name": product_name,
                }
    except Exception:
        return None
    return None


def check_ingredients_safety(
    ingredients_text, user_allergens, dietary_restriction="none"
):
    if not ingredients_text:
        return {"total": 0, "warnings": [], "safe": [], "is_safe": True}

    ingredients_list = [
        item.strip().lower()
        for item in ingredients_text.replace("\n", ",").split(",")
        if item.strip()
    ]

    warnings = []
    safe_ingredients = []

    religious_bans = []
    if dietary_restriction == "halal":
        religious_bans = [
            "pork",
            "bacon",
            "ham",
            "lard",
            "alcohol",
            "wine",
            "beer",
            "gelatin (pork)",
        ]
    elif dietary_restriction == "vegan":
        religious_bans = [
            "milk",
            "egg",
            "meat",
            "honey",
            "gelatin",
            "whey",
            "casein",
            "chicken",
            "beef",
        ]
    elif dietary_restriction == "kosher":
        religious_bans = ["pork", "shellfish", "crab", "lobster"]

    for item in ingredients_list:
        found_issue = False
        reason = ""

        for ban in religious_bans:
            if ban in item:
                reason = f"Restricted ({dietary_restriction}): {ban}"
                warnings.append({"ingredient": item, "reason": reason})
                found_issue = True
                break

        if found_issue:
            continue

        for allergen in user_allergens:
            if allergen and allergen.lower() in item:
                reason = f"Allergy match: {allergen}"
                warnings.append({"ingredient": item, "reason": reason})
                found_issue = True
                break

        if not found_issue:
            safe_ingredients.append(item)

    return {
        "total": len(ingredients_list),
        "warnings": warnings,
        "safe": safe_ingredients,
        "is_safe": len(warnings) == 0,
    }
