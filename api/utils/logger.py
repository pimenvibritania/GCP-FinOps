import logging

from home.models.tech_family import TechFamily
from asgiref.sync import sync_to_async
from home.models.logger import ReportLogger


class Logger:
    @classmethod
    async def log_report(cls, created_by, tech_family, metadata, link, pdf_password):
        tech_family_id = await sync_to_async(TechFamily.get_id)("name", tech_family)
        instance = ReportLogger(
            created_by=created_by,
            tech_family_id=tech_family_id,
            metadata=metadata,
            link=link,
            pdf_password=pdf_password,
        )
        return await sync_to_async(instance.save)(
            force_insert=False, force_update=False, using=None, update_fields=None
        )


class CustomLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.setLevel(logging.NOTSET)
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.addHandler(handler)
