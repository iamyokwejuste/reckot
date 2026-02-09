import os
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from apps.orgs.models import Organization
from apps.events.models import Event, EventCustomization


def delete_file_if_exists(file_field):
    if file_field and hasattr(file_field, "path"):
        try:
            if os.path.isfile(file_field.path):
                os.remove(file_field.path)
        except Exception:
            pass


@receiver(pre_save, sender=Organization)
def delete_old_org_logo_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Organization.objects.get(pk=instance.pk)
        if old_instance.logo and old_instance.logo != instance.logo:
            delete_file_if_exists(old_instance.logo)
    except Organization.DoesNotExist:
        pass


@receiver(post_delete, sender=Organization)
def delete_org_logo_on_delete(sender, instance, **kwargs):
    delete_file_if_exists(instance.logo)


@receiver(pre_save, sender=Event)
def delete_old_event_cover_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Event.objects.get(pk=instance.pk)
        if (
            old_instance.cover_image
            and old_instance.cover_image != instance.cover_image
        ):
            delete_file_if_exists(old_instance.cover_image)
    except Event.DoesNotExist:
        pass


@receiver(post_delete, sender=Event)
def delete_event_cover_on_delete(sender, instance, **kwargs):
    delete_file_if_exists(instance.cover_image)


@receiver(pre_save, sender=EventCustomization)
def delete_old_customization_images_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = EventCustomization.objects.get(pk=instance.pk)

        if old_instance.hero_image and old_instance.hero_image != instance.hero_image:
            delete_file_if_exists(old_instance.hero_image)

        if old_instance.logo and old_instance.logo != instance.logo:
            delete_file_if_exists(old_instance.logo)
    except EventCustomization.DoesNotExist:
        pass


@receiver(post_delete, sender=EventCustomization)
def delete_customization_images_on_delete(sender, instance, **kwargs):
    delete_file_if_exists(instance.hero_image)
    delete_file_if_exists(instance.logo)
