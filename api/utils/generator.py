from google.cloud import storage
from weasyprint import HTML
from core import settings
from PyPDF2 import PdfReader, PdfWriter

import os
import datetime
import random
import string
import shutil

MEDIA_ROOT = settings.MEDIA_ROOT


def random_string(length):
    return str(
        "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    )


def clear_media():
    print("Deleting all local media files...")
    shutil.rmtree(MEDIA_ROOT)


def upload_file(local_encrypted_filepath, filename):
    storage_client = storage.Client.from_service_account_json(
        settings.GOOGLE_APPLICATION_CREDENTIALS
    )
    bucket = storage_client.bucket(settings.GOOGLE_CLOUD_STORAGE_BUCKET_NAME)
    blob = bucket.blob(
        f"pdf-report/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}-{filename}"
    )
    blob.upload_from_filename(local_encrypted_filepath, content_type="application/pdf")

    print(blob.public_url)
    return blob.public_url


def pdf(filename, content, password):
    pdf_content = HTML(string=content).write_pdf()

    pdf_filename = f"{filename}.pdf"

    local_pdf_path = os.path.join(MEDIA_ROOT, pdf_filename)
    with open(local_pdf_path, "wb") as local_pdf_file:
        local_pdf_file.write(pdf_content)

    reader = PdfReader(local_pdf_path)

    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    encrypted_filename = f"enc-{pdf_filename}"
    local_encrypted_filepath = os.path.join(MEDIA_ROOT, encrypted_filename)

    with open(local_encrypted_filepath, "wb") as f:
        writer.write(f)

    os.remove(local_pdf_path)

    return (
        upload_file(local_encrypted_filepath, encrypted_filename),
        local_encrypted_filepath,
    )
