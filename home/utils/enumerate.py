from enum import Enum


class ProjectType(Enum):
    MFI = "MFI"
    MDI = "MDI"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class EnvironmentType(Enum):
    DEVL = "development"
    STAG = "staging"
    PROD = "production"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class ServiceType(Enum):
    BE = "backend"
    FE = "frontend"
    INFRA = "infra"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
