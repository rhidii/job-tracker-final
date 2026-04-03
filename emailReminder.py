import sqlite3
# Used to connect and query the SQLite database

import smtplib
# Used to send emails via SMTP (Gmail server)

from email.mime.text import MIMEText
# Used to format the email content properly

from datetime import datetime, timedelta
# Used to calculate dates (e.g. 3 days before deadline)


def send_email(to_email, subject, body):
    """
    Sends an email using the project sender account.
    This is a reusable function used by all email features.
    """

    # Sender email credentials (Gmail app password)
    sender_email = "jobstracker.notifications@gmail.com"
    sender_password = "nban vida engt hgnt"

    # Create email message object
    msg = MIMEText(body)

    # Set email headers
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    # Connect securely to Gmail SMTP server and send email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())


def send_application_confirmation(to_email, company, role, deadline, interview_date=""):
    """
    Sends an email immediately after a job application is saved.
    This confirms to the user that their application was recorded.
    """

    # Email subject
    subject = f"Application saved, {company}"

    # Email body content
    body = f"""
Your job application has been saved successfully.

Company: {company}
Role: {role}
Deadline: {deadline}
Interview Date: {interview_date if interview_date else "Not set"}

Good luck with your application!
"""

    # Send the email
    send_email(to_email, subject, body)

def send_application_update(to_email, company, role):
    subject = f"Application updated: {company}"
    body = f"""
Hello,

Your job application for {role} at {company} has been successfully updated.

If you did not make this change, please check your tracker immediately.

"""
    send_email(to_email, subject, body)

def send_application_deleted(to_email, company, role):
    subject = f"Application deleted: {company}"
    body = f"""

Hello,

Your job application for {role} at {company} has been deleted.

If this was a mistake, you may need to re-add it.
"""
    send_email(to_email, subject, body)

def send_deadline_reminder(to_email, company, role, date_value, reminder_type="deadline"):
    """
    Sends a reminder email.
    Can be used for both deadline reminders and interview reminders.
    """

    # Check if this is an interview reminder
    if reminder_type == "interview":

        subject = f"Interview reminder, {company}"

        body = f"""
Reminder:

You have an interview for the role of {role} at {company} in 3 days.

Interview date: {date_value}

Good luck!
"""

    else:
        # Otherwise send deadline reminder

        subject = f"Deadline reminder, {company}"

        body = f"""
Reminder:

You have an upcoming application deadline for the role of {role} at {company} in 3 days.

Deadline: {date_value}

Good luck!
"""

    # Send the email
    send_email(to_email, subject, body)


def send_reminders():
    """
    Sends reminders for deadlines and interviews that are exactly 3 days away.

    This function:
    1. Connects to the database
    2. Finds applications with deadlines/interviews in 3 days
    3. Sends reminder emails
    """

    # Connect to database
    conn = sqlite3.connect("job_tracker.db")
    cursor = conn.cursor()

    # Calculate target date (today + 3 days)
    target_date = (datetime.today() + timedelta(days=3)).strftime("%Y-%m-%d")


    # DEADLINE REMINDERS


    cursor.execute("""
        SELECT applications.company, applications.role, applications.deadline, users.email
        FROM applications
        JOIN users ON applications.user_id = users.id
        WHERE applications.deadline = ?
          AND applications.status IN ('Applied', 'Interview')
    """, (target_date,))

    deadline_rows = cursor.fetchall()

    # Send reminder for each matching application
    for company, role, deadline, email in deadline_rows:
        print(f"Sending deadline reminder to {email} for {company} - {role}")
        send_deadline_reminder(email, company, role, deadline, "deadline")

    
    # INTERVIEW REMINDERS
    

    cursor.execute("""
        SELECT applications.company, applications.role, applications.interview_date, users.email
        FROM applications
        JOIN users ON applications.user_id = users.id
        WHERE applications.interview_date = ?
          AND applications.status IN ('Interview', 'Offer')
    """, (target_date,))

    interview_rows = cursor.fetchall()

    # Send reminder for each interview
    for company, role, interview_date, email in interview_rows:
        print(f"Sending interview reminder to {email} for {company} - {role}")
        send_deadline_reminder(email, company, role, interview_date, "interview")

    # If nothing found, print message
    if not deadline_rows and not interview_rows:
        print("No reminders to send.")

    # Close database connection
    conn.close()


# Run this file directly to trigger reminders manually
if __name__ == "__main__":
    send_reminders()
