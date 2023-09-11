from django.core.management.base import BaseCommand
import subprocess


class Command(BaseCommand):
    help = "Run process with ASGI"

    def add_arguments(self, parser):
        parser.add_argument(
            "--development",
            action="store_true",
            help="Running development",
        )

    def handle(self, *args, **options):
        # Command to run uvicorn
        uvicorn_command = [
            "uvicorn",
            "--workers",
            "3",
            "core.asgi:application",
            "--port",
            "5005",
            "--host",
            "0.0.0.0",
            "--reload",
        ]

        if options["development"]:
            uvicorn_command.append("--reload-include")
            uvicorn_command.append("html")
        try:
            self.stdout.write("Running uvicorn with custom parameters...")
            subprocess.run(uvicorn_command, check=True)
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(f"Error running uvicorn: {e}"))
        else:
            self.stdout.write(
                self.style.SUCCESS("uvicorn command executed successfully")
            )
