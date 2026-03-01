from django.core.management.base import BaseCommand
import time
from myapp.simulator import generate_all_assets


class Command(BaseCommand):
    help = "Simulate real-time power readings"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting simulator..."))

        while True:
            generate_all_assets()
            self.stdout.write("Generated new readings")
            time.sleep(5)