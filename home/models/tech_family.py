from django.db import models
from django.db.models import Q

from home.models.base_model import BaseModel
from ..utils.enumerate import ProjectType


class TechFamily(BaseModel):
    class Meta:
        db_table = "tech_family"
        constraints = [models.UniqueConstraint(fields=["name"], name="unique_name")]

    name = models.CharField(max_length=100)
    pic = models.CharField(max_length=100)
    pic_email = models.EmailField(max_length=100)
    pic_telp = models.TextField(max_length=500, null=True, default=None)
    limit_budget = models.FloatField()
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

    @classmethod
    def get_slug(cls, column_name, value):
        data = (column_name, value)
        return cls.objects.get(data).slug

    @classmethod
    def get_row_name_by_slug(cls, value):
        data = cls.objects.get(("slug", value)).name
        data_list = data.split()
        return (
            "PLATFORM"
            if data_list[0] == "PLATFORM"
            else "DEFI"
            if data_list[0] == "DEFI"
            else data
        )

    @staticmethod
    def tech_cost():
        return [
            "dana_tunai",
            "defi_mdi",
            "platform_mdi",
            "mofi",
            "defi_mfi",
            "platform_mfi",
        ]

    @staticmethod
    def included_mdi():
        return ["dana_tunai", "defi_mdi", "platform_mdi"]

    @staticmethod
    def included_mfi():
        return ["mofi", "defi_mfi", "platform_mfi"]

    @classmethod
    def get_monthly_limit(cls, slug):
        data = ("slug", slug)
        return cls.objects.get(data).limit_budget

    @classmethod
    def get_weekly_limit(cls, slug):
        data = ("slug", slug)
        return cls.objects.get(data).limit_budget / 4

    def get_data(self):
        return {
            "id": self.id,
            "name": self.name,
            "pic": self.pic,
            "pic_email": self.pic_email,
            "slug": self.slug,
            "project": self.project,
        }
