from django.db import models, connection
from ..utils.enumerate import EnvironmentType
from .tech_family import TechFamily
from ..utils.serializer import IndexWeightSerializer
from django.core import serializers

class IndexWeight(models.Model):
    class Meta:
        db_table = "index_weight"

    tech_family = models.ForeignKey(
        TechFamily,
        on_delete=models.PROTECT,
        blank=False
    )

    value = models.FloatField()

    environment = models.CharField(max_length=12, choices=EnvironmentType.choices())
    created_at = models.DateTimeField(auto_now_add = True, auto_now = False, blank = False)

    def __str__(self):
        return self.value
    
    @classmethod
    def get_index_weight(cls, from_date, to_date):
        query = f"""
                SELECT 
                    t1.value AS value, 
                    t1.environment, 
                    tf.project, 
                    tf.slug
                FROM index_weight t1
                JOIN (
                    SELECT tech_family_id, environment, MAX(created_at) AS max_created_at
                    FROM index_weight
                    WHERE created_at BETWEEN "2023-07-01" AND "2023-08-01"
                    GROUP BY tech_family_id, environment
                ) t2 ON t1.tech_family_id = t2.tech_family_id AND t1.environment = t2.environment AND t1.created_at = t2.max_created_at
                JOIN tech_family AS tf ON t1.tech_family_id = tf.id
                ORDER BY t1.id;
            """
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

        organized_data = {}
        for value, environment, project, slug in result:
            if project not in organized_data:
                organized_data[project] = {}
            if slug not in organized_data[project]:
                organized_data[project][slug] = {}
            organized_data[project][slug][environment] = value

        return organized_data
