import logging

logger = logging.getLogger(__name__)

def send_risk_alert_email(student_email: str, student_name: str, subject_name: str, risk_level: str):
    """
    Mock email service for sending risk alerts.
    In production, this would use a real SMTP server.
    """
    subject = f"Academic Risk Alert for {subject_name}"
    body = f"Hello {student_name},\n\nYour academic risk level for {subject_name} has changed to {risk_level}.\nPlease check your student dashboard for details and recommendations."
    
    # Mocking the email sending
    logger.info(f"--- MOCK EMAIL SENT ---")
    logger.info(f"To: {student_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body}")
    logger.info(f"-----------------------")
    
def send_intervention_email(student_email: str, student_name: str, title: str):
    subject = f"New Teacher Intervention: {title}"
    body = f"Hello {student_name},\n\nA teacher has scheduled a new intervention for you: {title}.\nPlease login to your portal for details."
    
    logger.info(f"--- MOCK EMAIL SENT ---")
    logger.info(f"To: {student_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body}")
    logger.info(f"-----------------------")
