# CS50 Finance

A web application that lets users simulate trading stocks — buying, selling, and tracking a virtual portfolio with real-time price lookups. This is the capstone project from the Python/web track of Harvard's CS50, and the most complete full-stack project in this portfolio.

## Features

- **User authentication** — registration, login, and session management with hashed passwords
- **Stock lookup** — real-time price data via API integration
- **Buy/Sell simulation** — users can purchase and sell shares using simulated cash balance
- **Portfolio tracking** — view current holdings, total value, and transaction history
- **SQL database** — persistent storage of users, transactions, and balances

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite (via CS50's SQL library)
- **Frontend:** HTML, Jinja templating, Bootstrap
- **Other:** Flask-Session for session management, Werkzeug for password hashing

## Project Structure

```
cs50-finance/
├── app.py              # Main Flask application & routes
├── helpers.py          # Helper functions (lookup, usd formatting, login_required decorator)
├── finance.db          # SQLite database
├── templates/          # HTML templates (login, register, index, buy, sell, history, quote)
└── static/             # CSS and static assets
```

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Create Database
sqlite3 finance.db .schema > schema.sql

# Run the app
flask run
```

## What I Learned

This project combined everything from earlier in the course — control flow, data structures, and algorithmic thinking — into a real, deployable web application. It was my first hands-on experience with:
- Structuring a multi-route Flask app
- Designing and querying a relational database
- Managing user sessions and authentication securely
- Connecting a backend to an external API

## About
Built as the final project for CS50's web programming track, this project marked the starting point for my transition toward backend development.
