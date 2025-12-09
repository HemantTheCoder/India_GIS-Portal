import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from services.storage import get_preference

def send_email_alert(subject, body):
    """Sends an email alert using SMTP credentials from secrets."""
    try:
        if "EMAIL" not in st.secrets:
            print("Email credentials not found in secrets.toml")
            return False

        smtp_server = st.secrets["EMAIL"].get("smtp_server", "smtp.gmail.com")
        smtp_port = st.secrets["EMAIL"].get("smtp_port", 587)
        sender_email = st.secrets["EMAIL"].get("sender_email")
        password = st.secrets["EMAIL"].get("password")
        
        # Get recipient from storage
        recipient_email = get_preference("alert_email")
        if not recipient_email:
            print("No recipient email configured.")
            return False

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        
        print(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_whatsapp_alert(message_body):
    """Sends a WhatsApp alert using Twilio credentials from secrets."""
    try:
        from twilio.rest import Client
        
        if "TWILIO" not in st.secrets:
            print("Twilio credentials not found in secrets.toml")
            return False
            
        account_sid = st.secrets["TWILIO"].get("account_sid")
        auth_token = st.secrets["TWILIO"].get("auth_token")
        from_whatsapp = st.secrets["TWILIO"].get("from_whatsapp") # e.g., 'whatsapp:+14155238886'
        
        # Get recipient from storage
        to_whatsapp = get_preference("alert_phone") # e.g., 'whatsapp:+919876543210'
        
        if not to_whatsapp:
            print("No recipient phone configured.")
            return False
            
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            from_=from_whatsapp,
            body=message_body,
            to=to_whatsapp
        )
        
        print(f"WhatsApp sent: {message.sid}")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")
        return False

def push_notification(subject, details):
    """Dispatch notifications based on user preferences."""
    
    # Always log to local console/logs
    print(f"NOTIFICATION: {subject} - {details}")
    
    email_enabled = get_preference("enable_email", "false").lower() == "true"
    whatsapp_enabled = get_preference("enable_whatsapp", "false").lower() == "true"
    
    results = {}
    
    if email_enabled:
        results['email'] = send_email_alert(subject, details)
        
    if whatsapp_enabled:
        results['whatsapp'] = send_whatsapp_alert(f"*{subject}*\n\n{details}")
        
    return results
