from django.core.management.base import BaseCommand
from core.etl.offer_etl import OfferETL
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run ETL process for laboratory offers from Gmail'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Days back to search emails (default: 3)'
        )

    def handle(self, *args, **options):
        days_back = options['days']

        self.stdout.write(self.style.NOTICE(f'Starting ETL (last {days_back} days)...'))

        etl = OfferETL()
        stats = etl.run(days_back=days_back)

        self.stdout.write(self.style.SUCCESS('\n=== ETL RESULTS ==='))
        self.stdout.write(f'Emails processed: {stats["emails_processed"]}')
        self.stdout.write(f'Attachments downloaded: {stats["attachments_downloaded"]}')
        self.stdout.write(f'Offers extracted: {stats["offers_extracted"]}')
        self.stdout.write(f'Offers inserted: {stats["offers_inserted"]}')
        self.stdout.write(f'Offers updated: {stats["offers_updated"]}')

        if stats['errors']:
            self.stdout.write(self.style.WARNING(f'\nErrors: {len(stats["errors"])}'))
            for error in stats['errors'][:10]:
                self.stdout.write(self.style.ERROR(f'  • {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ ETL completed without errors'))
