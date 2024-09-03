from django.db import models, connection

from home.models.base_model import BaseModel
from .tech_family import TechFamily
from ..utils.enumerate import EnvironmentType
from datetime import datetime, timedelta


class IndexWeight(BaseModel):
    class Meta:
        db_table = "index_weight"
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "created_at", "tech_family"],
                name="unique_daily_index_weight",
            )
        ]

    tech_family = models.ForeignKey(
        TechFamily, related_name="index_weight", on_delete=models.PROTECT, blank=False
    )

    value = models.FloatField()
    environment = models.CharField(max_length=12, choices=EnvironmentType.choices())
    created_at = models.DateTimeField(blank=False)

    def __str__(self):
        return self.environment

    @classmethod
    def get_index_weight(cls):
        query = f"""
                SELECT 
                    t1.id,
                    t1.value AS value, 
                    t1.environment, 
                    tf.project, 
                    tf.slug
                FROM index_weight t1
                JOIN (
                    SELECT tech_family_id, environment, MAX(created_at) AS max_created_at
                    FROM index_weight
                    GROUP BY tech_family_id, environment
                ) t2 ON t1.tech_family_id = t2.tech_family_id AND t1.environment = t2.environment AND t1.created_at = t2.max_created_at
                JOIN tech_family AS tf ON t1.tech_family_id = tf.id
                ORDER BY t1.id;
            """
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

        organized_data = {}
        for index_id, value, environment, project, slug in result:
            if project not in organized_data:
                organized_data[project] = {}
            if slug not in organized_data[project]:
                organized_data[project][slug] = {}
            organized_data[project][slug][environment] = {
                "id": index_id,
                "value": value,
            }

        return organized_data

    @classmethod
    def get_daily_index_weight(cls, usage_date: str):
        date_object = datetime.strptime(usage_date, "%Y-%m-%d")
        date_object_after = date_object + timedelta(days=1)
        date_after_str = date_object_after.strftime("%Y-%m-%d")

        query = f"""
            SELECT iw.id, iw.value, iw.environment, tf.project, tf.slug 
            FROM index_weight iw
            JOIN tech_family AS tf ON iw.tech_family_id = tf.id
            WHERE iw.created_at > "{usage_date}" and iw.created_at < "{date_after_str}"
            GROUP BY iw.environment, tf.slug
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

        organized_data = {}
        for index_id, value, environment, project, slug in result:
            if project not in organized_data:
                organized_data[project] = {}
            if slug not in organized_data[project]:
                organized_data[project][slug] = {}
            organized_data[project][slug][environment] = value

        return organized_data
