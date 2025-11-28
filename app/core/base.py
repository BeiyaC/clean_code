import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, StrictInt, StrictStr


@dataclass
class GetEnviron:
    var: str
    default: str | None = None

    def __call__(self) -> Any:
        if self.default:
            return os.environ.get(self.var, self.default)
        return os.environ[self.var]


class Environment(Enum):
    development = "development"
    master = "master"
    test = "test"
    production = "production"


class Database(BaseModel, validate_default=True):
    host: StrictStr
    port: StrictInt
    database: StrictStr
    user: StrictStr
    password: StrictStr

    def uri(self, scheme: StrictStr) -> str:
        uri = f"{scheme}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return uri


class BaseConfig(BaseModel, validate_default=True):
    environment: Environment = Field(default_factory=GetEnviron("ENVIRONMENT"))

    def is_dev_environment(self) -> bool:
        return self.environment == Environment.development

    def is_test_environment(self) -> bool:
        return self.environment == Environment.test

    def is_prod_environment(self) -> bool:
        return self.environment == Environment.production
