from django.core.management.base import BaseCommand
import subprocess

class Command(BaseCommand):
    help = 'Run process with asgi'

    def handle(self, *args, **options):
        # Command to run uvicorn
        uvicorn_command = [
            "uvicorn",
            "--workers", "5",
            "core.asgi:application",
            "--port", "5005",
            "--host", "0.0.0.0",
            "--reload"
        ]

        try:
            self.stdout.write("Running uvicorn with custom parameters...")
            subprocess.run(uvicorn_command, check=True)
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(f"Error running uvicorn: {e}"))
        else:
            self.stdout.write(self.style.SUCCESS("uvicorn command executed successfully"))
