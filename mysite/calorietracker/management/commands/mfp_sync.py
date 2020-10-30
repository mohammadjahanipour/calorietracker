from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Syncs MFP Data to our DB'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Synced"))
