from django.db import models
from ..utils.enumerate import ProjectType
from django.db.models import Q


class TechFamily(models.Model):
    class Meta:
        db_table = "tech_family"
        constraints = [
            models.UniqueConstraint(
                fields=['name'], 
                name='unique_name'
            )
        ]

    name = models.CharField(max_length=100)
    pic = models.CharField(max_length=100)
    pic_email = models.EmailField(max_length=100)
    slug = models.CharField(max_length=100)
    project = models.CharField(max_length=100, choices=ProjectType.choices())
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, blank=False)

    def __str__(self):
        return self.name

    @classmethod
    def get_tf_project(cls):
        return cls.objects.all()

    @classmethod
    def get_tf_mdi(cls):
        return cls.objects.filter(
            Q(slug="platform_mdi") | Q(slug="dana_tunai") | Q(slug="defi_mdi")
        )

    @classmethod
    def get_tf_mfi(cls):
        return cls.objects.filter(
            Q(slug="platform_mfi") | Q(slug="mofi") | Q(slug="defi_mfi")
        )

    @classmethod
    def get_id(cls, column_name, value):
        data = (column_name, value)
        return cls.objects.get(data).id

    @staticmethod
    def included_mdi():
        return ["dana_tunai", "platform_mdi"]

    @staticmethod
    def included_mfi():
        return ["mofi", "defi", "platform_mfi"]

    def get_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'pic': self.pic,
            'pic_email': self.pic_email,
            'slug': self.slug,
            'project': self.project
        }
