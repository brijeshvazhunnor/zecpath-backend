from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, Employer, Candidate


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if not created:
        return

    if instance.role == User.Role.EMPLOYER:

        Employer.objects.create(
            user=instance,
            company_name=""
        )

    elif instance.role == User.Role.CANDIDATE:

        Candidate.objects.create(
            user=instance,
            full_name=instance.username,
            email=instance.email
        )