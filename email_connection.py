import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable

from dotenv import load_dotenv

from offers import Offer

load_dotenv()


class EmailContoller:
    email: str
    password: str
    recipients: Iterable[str]

    def __init__(self) -> None:
        self.email = os.getenv("BOT_EMAIL")
        self.password = os.getenv("BOT_PASS")
        self.recipients = json.loads(os.getenv("RECIPIENT_EMAILS"))

    def createSubject(self, offer: Offer) -> str:
        return f"Nowa oferta za {offer.price} zl: {offer.title}"

    def createMessageBody(self, offer: Offer) -> str:
        return f"""
Tytuł: {offer.title}
Najem: {offer.price}
Czynsz: {offer.rent}
Łącznie: {offer.totalCost()}
Średnia odległość: {offer.distance}

Link: {offer.link}

Opis:
{offer.description}""".strip()

    def createMessage(self, offer: Offer) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self.email
        message["To"] = ", ".join(self.recipients)
        message["Subject"] = self.createSubject(offer)
        message.set_content(self.createMessageBody(offer))
        return message

    def sendOfferNotifications(self, offer: Offer) -> None:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(self.email, self.password)
            message = self.createMessage(offer)
            smtp.sendmail(self.email, self.recipients, message.as_string())
