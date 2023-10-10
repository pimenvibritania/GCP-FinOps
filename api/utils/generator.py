from google.cloud import storage
from weasyprint import HTML
from core import settings
from PyPDF2 import PdfReader, PdfWriter
import datetime

import os
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


def upload_file(local_filepath, bucket_folder, filename, content_type=None):
    storage_client = storage.Client.from_service_account_json(
        settings.GOOGLE_APPLICATION_CREDENTIALS
    )
    bucket = storage_client.bucket(settings.GOOGLE_CLOUD_STORAGE_BUCKET_NAME)
    # bucket_folder = settings.GOOGLE_CLOUD_STORAGE_PDF_REPORT_FOLDER_NAME
    blob = bucket.blob(f"{bucket_folder}/{filename}")
    blob.upload_from_filename(local_filepath, content_type=content_type)

    # return blob.public_url
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=3),
        method="GET",
    )


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

    bucket_folder = settings.GOOGLE_CLOUD_STORAGE_PDF_REPORT_FOLDER_NAME

    return (
        upload_file(
            local_encrypted_filepath,
            bucket_folder,
            encrypted_filename,
            content_type="application/pdf",
        ),
        local_encrypted_filepath,
    )
