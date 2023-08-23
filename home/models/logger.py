from django.db import models
from home.models.tech_family import TechFamily


class ReportLogger(models.Model):
    class Meta:
        db_table = "report_log"

    id = models.BigAutoField(primary_key=True)
    created_by = models.CharField(max_length=50, default="Admin")
    tech_family = models.ForeignKey(
        TechFamily, related_name="report_log", on_delete=models.PROTECT, blank=False
    )
    metadata = models.TextField()
    link = models.TextField()
    pdf_password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)

    def __str__(self):
        return self.created_by.__str__()
