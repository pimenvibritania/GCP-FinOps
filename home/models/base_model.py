from django.db import models
from django.utils import timezone


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    class Meta:
        abstract = True

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(auto_now=False, null=True)

    def delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    objects = BaseModelManager()
