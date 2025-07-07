import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks
from jinja2 import Environment, FileSystemLoader
from utils.logging import logger

class EmailService:
    def __init__(self):
        self.sender_email = os.getenv("EMAIL_SENDER")
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "email")
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def _send_email(self, to_email, subject, html_content):
        """Send an email with the provided content"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
                
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _render_template(self, template_name, **kwargs):
        """Render an HTML template with the provided context"""
        template = self.jinja_env.get_template(f"{template_name}.html")
        return template.render(**kwargs)
    
    def send_password_reset(self, background_tasks: BackgroundTasks, user_email, reset_token, username):
        """Send a password reset email with a token"""
        subject = "Reset Your Face Attendance Password"
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        html_content = self._render_template(
            "password_reset",
            username=username,
            reset_url=reset_url,
            expires_in="1 hour"
        )
        
        # Send in background to not block the request
        background_tasks.add_task(self._send_email, user_email, subject, html_content)
    
    def send_attendance_confirmation(self, background_tasks: BackgroundTasks, user_email, user_name, class_name, session_date, status):
        """Send attendance confirmation email"""
        subject = f"Attendance Recorded: {class_name}"
        
        html_content = self._render_template(
            "attendance_confirmation",
            user_name=user_name,
            class_name=class_name,
            session_date=session_date,
            status=status,
        )
        
        background_tasks.add_task(self._send_email, user_email, subject, html_content)
    
    def send_upcoming_session_reminder(self, background_tasks: BackgroundTasks, user_email, user_name, class_name, session_date, session_time, location):
        """Send reminder for upcoming session"""
        subject = f"Upcoming Class Session: {class_name}"
        
        html_content = self._render_template(
            "session_reminder",
            user_name=user_name,
            class_name=class_name,
            session_date=session_date,
            session_time=session_time,
            location=location,
        )
        
        background_tasks.add_task(self._send_email, user_email, subject, html_content)
    
    def send_absence_notification(self, background_tasks: BackgroundTasks, teacher_email, teacher_name, student_name, class_name, session_date):
        """Notify teacher of student absence"""
        subject = f"Absence Notification: {class_name}"
        
        html_content = self._render_template(
            "absence_notification",
            teacher_name=teacher_name,
            student_name=student_name,
            class_name=class_name,
            session_date=session_date,
        )
        
        background_tasks.add_task(self._send_email, teacher_email, subject, html_content)

    def send_welcome_email(self, background_tasks: BackgroundTasks, user_email, user_name, role):
        """Send welcome email to new users"""
        subject = "Welcome to Face Attendance System"
        
        html_content = self._render_template(
            "welcome_email",
            user_name=user_name,
            role=role,
            login_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login"
        )
        
        background_tasks.add_task(self._send_email, user_email, subject, html_content)

# Singleton instance
email_service = EmailService()