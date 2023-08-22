from django.core.management.base import BaseCommand
from django.core.cache import cache
import os
import re
import shutil


class Command(BaseCommand):
    help = "Delete __pycache__ directories"

    def handle(self, *args, **options):
        directory = "."
        for root, dirs, files in os.walk(directory):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    dir_path = os.path.join(root, dir_name)
                    self.stdout.write(
                        self.style.ERROR(f"Deleting directory: {dir_path}")
                    )
                    shutil.rmtree(dir_path)

            for file_name in files:
                if re.match(r".*\.pyc$", file_name):
                    file_path = os.path.join(root, file_name)
                    self.stdout.write(self.style.ERROR(f"Deleting file: {file_path}"))
                    os.remove(file_path)

        self.stdout.write(
            self.style.SUCCESS("Successfully deleted __pycache__ directory")
        )

        cache.clear()
        self.stdout.write(self.style.SUCCESS("Memory cache cleared"))
