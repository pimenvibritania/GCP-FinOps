import asyncio
import datetime
import functools
import os

from django.template.loader import render_to_string
from httpx import AsyncClient

from api.utils.crypter import encrypt
from api.utils.generator import random_string, pdf
from core.settings import APP_ENVIRONMENT, MAIL_DATA, MAILGUN_API_KEY
from home.models import TechFamily
from home.models.logger import ReportLogger


class Mailer:

    # Function to send the email report
    @staticmethod
    async def send_report(to_email, subject, template_path, context, em_name, tech_family, metadata, logger=True):
        email_content = render_to_string(template_path, context)

        if em_name is None:
            em_name = "Data"

        # Generate PDF content and filename
        pdf_filename = (
            f"{tech_family}-{em_name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        pdf_content = f"""
                <h3 style="text-align: right">{tech_family}</h3>
                <h4 style="text-align: right">{em_name} | {datetime.datetime.now().strftime("%d-%m-%Y")}</h4>
                <hr />
            """
        pdf_content += email_content

        pdf_password = random_string(32)

        pdf_link, pdf_file = pdf(pdf_filename, pdf_content, pdf_password)
        encrypted_pdf_pass = encrypt(pdf_password)

        # Append the PDF password and link to the email content
        password_html = f"""
                <hr/>
                <a href="{pdf_link}"><strong>Your PDF file</strong></a><br/>
                <strong>Your PDF password is: {pdf_password}</strong>
            """

        email_content += password_html

        # Log the report (PDF & password) into database
        if logger:
            loop = asyncio.get_event_loop()
            tech_family_id = await loop.run_in_executor(None, TechFamily.get_id, "slug", tech_family)
            instance = ReportLogger(
                created_by="Admin",
                tech_family_id=tech_family_id,
                metadata=metadata,
                link=pdf_link,
                pdf_password=encrypted_pdf_pass,
            )

            await loop.run_in_executor(
                None,
                functools.partial(
                    instance.save,
                    force_insert=False,
                    force_update=False,
                    using=None,
                    update_fields=None
                )
            )

        if APP_ENVIRONMENT == "production":
            MAIL_DATA["to"] = to_email

        MAIL_DATA["subject"] = subject
        MAIL_DATA["html"] = email_content
        MAIL_DATA["o:tag"] = "important"

        # Read the PDF file and prepare the email attachment
        with open(pdf_file, "rb") as pdf_attachment:
            pdf_content = pdf_attachment.read()

        files = [("attachment", (f"{pdf_filename}.pdf", pdf_content, "application/pdf"))]

        # Send the email using AsyncClient
        async with AsyncClient() as client:
            response = await client.post(
                os.getenv("MAILGUN_URL"),
                auth=("api", MAILGUN_API_KEY),
                data=MAIL_DATA,
                files=files,
            )
            if response.status_code != 200:
                raise ValueError(response.content)

        os.remove(pdf_file)

