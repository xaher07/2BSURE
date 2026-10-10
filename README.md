2BSURE

Video Demo: [URL_HERE]

2BSURE is a full-stack web application designed to empower users with instant safety analysis of food products, cosmetics, and ingredients. Built with Python and Flask, 2BSURE caters to a global audience by providing multi-language support across 7 languages, dynamic dietary and religious restriction screening (Halal, Kosher, Vegan), customizable personal allergen tracking, and barcode/OCR label scanning capabilities.

Additionally, the application integrates an AI assistant powered by Google Gemini to answer complex ingredient and allergy-related queries, and features robust account security including strong password validation policies.

🚀 Key Features

Multi-Language Localization: Fully functional interface supporting 7 languages (English, Arabic, Spanish, Chinese, Hindi, French, and Russian) with automatic RTL/LTR layout adjustment based on the selected language.

Barcode Lookup Integration: Connects with the global Open Food Facts API to instantly fetch product names and ingredient lists via barcode scanning or manual entry.

OCR Label Scanning: Allows users to upload product label images to extract text and analyze ingredient safety.

Dietary & Religious Compliance Engine: Automated checks for dietary preferences including Halal, Kosher, Vegan, and custom user-defined allergens.

Strong Password Validation: Enforces strict security standards during user registration (requiring a minimum of 8 characters, uppercase letters, lowercase letters, numbers, and special symbols).

AI Assistant Chatbot: Leverages the gemini-1.5-flash model from Google Generative AI to provide real-time, intelligent guidance on ingredient safety and dietary restrictions.

User Accounts & Search History: Secure session-based authentication with password hashing (Werkzeug) and a persistent SQLite database storing historical search results and custom profile preferences.

🛠️ Technology Stack

Back-End: Python, Flask, Flask-Session

Database & ORM: SQLite managed via the CS50 SQL library (cs50)

Front-End: HTML5, Bootstrap 5 (Responsive UI with responsive components)

APIs & AI:

Open Food Facts API (Product metadata & ingredient retrieval)

Google Generative AI API (gemini-1.5-flash)

Security & Utilities: Werkzeug Security (password hashing and verification), Python re module for strict regex password validation.

📁 Project Structure

2bsure/
│
├── app.py               # Main Flask application (routes, session management, database queries)
├── helpers.py           # Helper functions (ingredient safety checking, barcode fetching, password validation)
├── translations.py      # Dictionary supporting all 7 languages and UI strings
├── safety.db            # SQLite database containing user accounts, allergen profiles, and history
├── static/              # Static directory containing stylesheets and uploads
│   └── uploads/         # Destination folder for user-uploaded ingredient label images
├── templates/           # HTML templates using Jinja2 and Bootstrap 5
│   ├── layout.html      # Base layout template with navbar, footer, and language toggler
│   ├── index.html       # Landing page introducing 2BSURE
│   ├── check.html       # Core ingredient analyzer interface
│   ├── login.html       # User authentication login page
│   ├── register.html    # User registration page with password policy prompts
│   ├── history.html     # Log of previous ingredient scans
│   └── profile.html     # User profile settings and dietary configurations
└── README.md            # Project documentation


⚙️ Installation & Setup

To run 2BSURE locally on your machine, follow these steps:

Clone the repository:

git clone https://github.com/your-username/2bsure.git
cd 2bsure


Install dependencies:
Ensure you have Python installed, then install the required packages:

pip install flask flask-session cs50 requests google-generativeai werkzeug


Configure Environment Variables (Optional for AI Assistant):
If you wish to use the Google Gemini AI chatbot feature, set your API key as an environment variable:

macOS/Linux: export GEMINI_API_KEY="your_api_key_here"

Windows (CMD): set GEMINI_API_KEY="your_api_key_here"

Run the Application:

python app.py


Access the Web App:
Open your browser and navigate to:
http://127.0.0.1:5000

📖 Usage Guide

Register & Secure Account: Navigate to the Register page, choose a username, and enter a strong password meeting the security criteria (at least 8 characters, including uppercase, lowercase, numbers, and special symbols). Select your dietary preference and optional personal allergens.

Analyze Ingredients: Use the Check tab to type ingredients manually, input a product barcode, or upload a package label.

Review Safety Results: Instantly view color-coded safety assessments indicating whether the product aligns with your profile or contains flagged components.

Consult the AI Assistant: Ask custom questions to the integrated Gemini chatbot for guidance on alternative ingredients or clarification on food additives.

Review History: Access your past analyses anytime via the Scan History tab.
