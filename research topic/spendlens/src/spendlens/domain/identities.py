"""Canonical resource identity. Display names are never join keys."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from spendlens.domain.enums import CloudProvider, ResourceType


class ResourceIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    cloud: CloudProvider
    account_id: str = Field(min_length=1)
    region: str = Field(min_length=1)
    resource_type: ResourceType
    provider_id: str = Field(min_length=1)

    def canonical_key(self) -> str:
        return "|".join(
            [
                self.cloud.value,
                self.account_id,
                self.region,
                self.resource_type.value,
                self.provider_id,
            ]
        )

    @classmethod
    def parse(cls, key: str) -> ResourceIdentity:
        cloud, account_id, region, resource_type, provider_id = key.split("|", 4)
        return cls(
            cloud=CloudProvider(cloud),
            account_id=account_id,
            region=region,
            resource_type=ResourceType(resource_type),
            provider_id=provider_id,
        )
