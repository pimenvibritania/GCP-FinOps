# Generated by Django 4.2.4 on 2023-10-02 08:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0011_gcpservices_gcpservices_unique_sku"),
    ]

    operations = [
        migrations.CreateModel(
            name="GCPProjects",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("identity", models.CharField(max_length=120)),
                ("name", models.CharField(max_length=120)),
                ("environment", models.CharField(max_length=100)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "gcp_projects",
            },
        ),
        migrations.AddConstraint(
            model_name="gcpprojects",
            constraint=models.UniqueConstraint(
                fields=("identity",), name="unique_project_identity"
            ),
        ),
    ]