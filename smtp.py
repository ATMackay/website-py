import smtplib

class SMTPServer:
    """
    A class to manage SMTP server connection and send emails.
    """
    def __init__(self, server_type, user, password):
        """
        Initializes an SMTPServer object with server details.
        """
        self.user = user
        self.password = password
        if server_type == "Outlook":
            self.smtp_server = "smtp-mail.outlook.com"
            self.smtp_port = 587
        else:
            raise ValueError("Invalid SMTP server type")
        # Initialize the host attribute to None. It will be set in the connect method.
        self.host = None

    def connect(self):
        """
        Connects to the SMTP server using the credentials provided during initialization.
        """
        try:
            self.host = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.host.starttls()
            self.host.login(self.user, self.password)
        except smtplib.SMTPException as e:
            raise SystemError(e) from e

    def send(self, from_email, to_email, text):
        """
        Sends the supplied email via the connected SMTP server.
        """
        if not self.host:
            raise SystemError("SMTP connection not established. Please run connect() first.")
        try:
            self.host.sendmail(from_email, to_email, text)
        except smtplib.SMTPException as e:
            raise e

    def close(self):
        """
        Closes the connection to the SMTP server.
        """
        if self.host:
            self.host.quit()
            self.host = None
