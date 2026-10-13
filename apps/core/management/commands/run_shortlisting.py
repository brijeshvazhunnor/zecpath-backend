
from django.core.management.base import BaseCommand

from apps.core.models import Job
from apps.core.services.shortlisting import process_job_applications


class Command(BaseCommand):
    help = "Process pending applications using ATS shortlisting rules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--job-id",
            type=int,
            default=None,
            help="Process one specific job.",
        )

    def handle(self, *args, **options):
        jobs = Job.objects.all()

        if options["job_id"] is not None:
            jobs = jobs.filter(pk=options["job_id"])

        total_processed = 0
        total_shortlisted = 0
        total_rejected = 0
        total_errors = 0

        for job in jobs.iterator():
            result = process_job_applications(job, actor=None)

            total_processed += result["processed"]
            total_shortlisted += result["shortlisted"]
            total_rejected += result["rejected"]
            total_errors += result["errors"]

            self.stdout.write(
                f"Job {job.id}: "
                f"processed={result['processed']}, "
                f"shortlisted={result['shortlisted']}, "
                f"rejected={result['rejected']}, "
                f"errors={result['errors']}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"Finished. Processed={total_processed}, "
            f"shortlisted={total_shortlisted}, "
            f"rejected={total_rejected}, errors={total_errors}"
        ))
