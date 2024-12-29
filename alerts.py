import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

DB_NAME = "darkweb_data.db"

def fetch_data_from_db():
    """Retrieve all scraped data from the SQLite database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scraped_data")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

def format_data_as_html(data):
    """Format database data as an HTML table."""
    if not data:
        return "<html><body><h2>No data available to display.</h2></body></html>"
    
    html = "<html><body><h2>Scraped Dark Web Data</h2><table border='1'>"
    html += "<tr><th>ID</th><th>URL</th><th>Keywords</th><th>Sentiment</th><th>Snippet</th></tr>"
    for row in data:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>"
    html += "</table></body></html>"
    return html

def send_email(to_email):
    """Send scraped data via email."""
    from_email = os.getenv("EMAIL_ADDRESS")
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    
    if not from_email or not app_password:
        print("Email credentials are not set in the .env file.")
        return

    data = fetch_data_from_db()
    if not data:
        print("No data to send.")
        return

    html_content = format_data_as_html(data)

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Scraped Dark Web Data"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(from_email, app_password)
            server.sendmail(from_email, to_email, msg.as_string())
        print(f"Data sent successfully to {to_email}")
    except smtplib.SMTPAuthenticationError:
        print("Authentication error: Please check your email and app password.")
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
