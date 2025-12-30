import traceback
import print_xkcd
import xkcd
from dotenv import load_dotenv
import time
import smtplib
import os
from email.mime.text import MIMEText

load_dotenv()

# Allow overriding the status file path via environment for containerized runs
STATUS_FILE = os.getenv("STATUS_FILE", "xkcd_last_printed.txt")

def send_error_email(message):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("ERROR_RECIPIENT_EMAIL")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password, recipient_email]):
        print("Email configuration is incomplete. Cannot send error email.")
        return

    msg = MIMEText(message)
    msg["Subject"] = "XKCD Printer Error"
    msg["From"] = recipient_email
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(recipient_email, [recipient_email], msg.as_string())
        print("Error email sent successfully.")
    except Exception as e:
        print(f"Failed to send error email: {e}")

def try_print():
    # Read the last printed XKCD number from the status file
    try:
        with open(STATUS_FILE, "r") as f:
            last_printed = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        last_printed = None
    # Get the latest XKCD comic number
    latest_comic = xkcd.getLatestComicNum()
    # print the comic if it hasn't been printed yet
    if last_printed is None or last_printed < latest_comic:
        # update the status file
        with open(STATUS_FILE, "w") as f:
            f.write(str(latest_comic))
        try:
            print_xkcd.print_xkcd(latest_comic)
        except Exception as e:
            print(f"Error printing XKCD comic #{latest_comic}: {e}")
            email_message = ""
            email_message += f"An error occurred while printing XKCD comic #{latest_comic}.\n\n"
            email_message += f"Error details:\n{e}\n"
            email_message += f"Traceback:\n{traceback.format_exc()}\n"
            send_error_email(email_message)
            return
        
        print(f"Successfully printed XKCD comic #{latest_comic}.")
    else:
        print("No new XKCD comic to print.")

def main():
    while True:
        print("Checking for new XKCD comic to print...")
        try_print()
        # wait for an hour before checking again
        time.sleep(1 * 60 * 60)

if __name__ == "__main__":
    main()