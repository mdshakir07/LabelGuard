from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RuleFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: str
    version: str
    title: str
    description: str
    source: Optional[str]
    severity: str
    status: str
    effective_from: Optional[str]
    effective_to: Optional[str]
    rule_type: str
    applicability: Optional[dict]
    condition: Optional[str]
    verify_prompt: Optional[str]


class RuleCreate(BaseModel):
    rule_id: str = Field(max_length=30)
    version: str = Field(max_length=20)
    title: str = Field(max_length=255)
    description: str = ""
    source: Optional[str] = None
    severity: str = "mandatory"
    status: str = "draft"
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    rule_type: str = "deterministic"
    params: Optional[dict] = None
    applicability: Optional[dict] = None
    condition: Optional[str] = None
    verify_prompt: Optional[str] = None


class RulePublishIn(BaseModel):
    status: str = Field(pattern="published|superseded|retired")


class RuleListOut(BaseModel):
    version: str
    rules: List[RuleFlowOut]