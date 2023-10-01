from django.db import models, connection
from ..utils.enumerate import EnvironmentType, ProjectType
from .services import Services
from .kubecost_clusters import KubecostClusters
from home.models.base_model import BaseModel
import json


class KubecostNamespaces(BaseModel):
    class Meta:
        db_table = "kubecost_namespaces"
        constraints = [
            models.UniqueConstraint(
                fields=['namespace', 'cluster','date'],
                name='unique_namespace_cluster_date'
            )
        ]

    namespace = models.CharField(max_length=100)
    service = models.ForeignKey(Services, on_delete=models.PROTECT, null=True)
    date = models.DateField(blank=False)
    project = models.CharField(max_length=12, choices=ProjectType.choices())
    environment = models.CharField(max_length=12, choices=EnvironmentType.choices())
    cluster = models.ForeignKey(KubecostClusters, on_delete=models.PROTECT, blank=False, null=False)
    cpu_cost = models.FloatField()
    memory_cost = models.FloatField()
    pv_cost = models.FloatField()
    lb_cost = models.FloatField()
    network_cost = models.FloatField()
    total_cost = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
  
    def __str__(self):
        return self.namespace
    
    @classmethod
    def get_namespace_report(cls, start_date_this_week, end_date_this_week, start_date_prev_week, end_date_prev_week):
        query = f"""
                SELECT
                    s.tech_family_id,
                    kn.service_id,
                    s.name,
                    kn.environment,
                    ROUND(SUM(CASE WHEN kn.date BETWEEN '{start_date_this_week}' AND '{end_date_this_week}' THEN kn.total_cost ELSE 0 END), 2) AS cost_this_week,
                    ROUND(SUM(CASE WHEN kn.date BETWEEN '{start_date_prev_week}' AND '{end_date_prev_week}' THEN kn.total_cost ELSE 0 END), 2) AS cost_prev_week
                FROM
                    kubecost_namespaces kn
                JOIN
                    services s ON kn.service_id = s.id
                WHERE
                    kn.service_id IS NOT NULL
                GROUP BY
                    s.tech_family_id,
                    kn.service_id,
                    s.name,
                    kn.environment
                ORDER BY s.tech_family_id, kn.service_id, kn.environment;
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return(rows)

    @classmethod
    def get_deployments_report(cls, start_date_this_week, end_date_this_week, start_date_prev_week, end_date_prev_week):
        query = f"""
                    SELECT
                        s.tech_family_id,
                        kn.service_id,
                        s.name,
                        kn.environment,
                        ROUND(SUM(CASE WHEN kn.date BETWEEN '{start_date_this_week}' AND '{end_date_this_week}' THEN kn.total_cost ELSE 0 END), 2) AS cost_this_week,
                        ROUND(SUM(CASE WHEN kn.date BETWEEN '{start_date_prev_week}' AND '{end_date_prev_week}' THEN kn.total_cost ELSE 0 END), 2) AS cost_prev_week
                    FROM
                        kubecost_deployments kn
                    JOIN
                        services s ON kn.service_id = s.id
                    WHERE
                        kn.service_id IS NOT NULL
                        AND (kn.namespace = "moladin-crm-mfe" OR kn.namespace = "moladin-b2c-mfe")
                    GROUP BY
                        s.tech_family_id,
                        kn.service_id,
                        s.name,
                        kn.environment
                    ORDER BY s.tech_family_id, kn.service_id, kn.environment;
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return(rows)

    @classmethod
    def get_unregistered_namespace(cls, start_date_this_week, end_date_this_week, start_date_prev_week, end_date_prev_week):
        query = f"""
                    SELECT
                        kn.namespace,
                        kn.project,
                        kn.environment,
                        kc.cluster_name,
                        ROUND(SUM(CASE WHEN kn.date BETWEEN '{start_date_this_week}' AND '{end_date_this_week}' THEN kn.total_cost ELSE 0 END), 2) AS cost_this_week,
                        ROUND(SUM(CASE WHEN kn.date BETWEEN '{start_date_prev_week}' AND '{end_date_prev_week}' THEN kn.total_cost ELSE 0 END), 2) AS cost_prev_week
                    FROM
                        kubecost_namespaces kn
                    JOIN
                    	 kubecost_clusters kc ON kn.cluster_id = kc.id
                    WHERE
                        kn.service_id IS NULL
                        AND kn.namespace != "moladin-crm-mfe" AND kn.namespace != "moladin-b2c-mfe" AND kn.namespace != "__unmounted__"
                    GROUP BY
                        kn.namespace,
                        kn.project,
                        kn.environment,
                        kc.cluster_name
                    ORDER BY
                        kn.namespace,
                        kn.project,
                        kn.environment,
                        kc.cluster_name;
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return(rows)

    @classmethod
    def get_unregistered_deployment(cls, start_date_this_week, end_date_this_week, start_date_prev_week, end_date_prev_week):
        query = f"""
                    SELECT
                    	 kd.deployment,
                        kd.project,
                        kd.environment,
                        kc.cluster_name,
                        ROUND(SUM(CASE WHEN kd.date BETWEEN '{start_date_this_week}' AND '{end_date_this_week}' THEN kd.total_cost ELSE 0 END), 2) AS cost_this_week,
                        ROUND(SUM(CASE WHEN kd.date BETWEEN '{start_date_prev_week}' AND '{end_date_prev_week}' THEN kd.total_cost ELSE 0 END), 2) AS cost_prev_week
                    FROM
                        kubecost_deployments kd
                    JOIN
                    	kubecost_clusters kc ON kd.cluster_id = kc.id
                    WHERE
                        kd.service_id IS NULL
                        AND (kd.namespace = "moladin-crm-mfe" OR kd.namespace = "moladin-b2c-mfe")
                        AND kd.deployment is not null
                        AND kd.deployment != '__unallocated__'
                    GROUP BY
                    	kd.deployment,
                        kd.project,
                        kd.environment,
                        kc.cluster_name
                    ORDER BY
                    	kd.deployment,
                        kd.project,
                        kd.environment,
                        kc.cluster_name;
                """
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return(rows)




class KubecostNamespacesMap(models.Model):
    class Meta:
        db_table = "kubecost_namespace_map"
        constraints = [
            models.UniqueConstraint(
                fields=['namespace', 'project'],
                name='unique_namespace_project'
            )
        ]

    namespace = models.CharField(max_length=100)
    service = models.ForeignKey(Services, on_delete=models.PROTECT, blank=False)
    project = models.CharField(max_length=12, choices=ProjectType.choices())
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, blank=False)
    updated_at = models.DateTimeField(auto_now=False, null=True)
  
    def __str__(self):
        return self.namespace

    @classmethod
    def get_all(cls):
        return cls.objects.all()
        
    @classmethod
    def get_namespaces_map(cls, project):
        return cls.objects.filter(project=project).values('service_id', 'namespace')
