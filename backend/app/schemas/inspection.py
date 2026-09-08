from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

PUBLIC_ID_PATTERN = r"^IN-[0-9]{4}-[0-9]{4}$"


class InspectionCreate(BaseModel):
    location: str = ""
    channel: str = Field(default="retail", pattern="retail|ecommerce|institutional|industrial")
    inspection_date: date = date.today()
    category: Optional[str] = None
    package_structure: str = Field(default="single",
                                   pattern="single|multi_product|multi_unit|promotional")
    origin: str = Field(default="domestic", pattern="domestic|imported")
    special_status: Optional[str] = None
    product_name_hint: Optional[str] = None


class InspectionImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    original_url: str
    processed_url: Optional[str]
    sha256: str
    width: Optional[int]
    height: Optional[int]
    quality_score_json: Optional[dict]


class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field: str
    raw: Optional[str]
    normalized: Optional[dict]
    confidence: Optional[float]
    source_ocr_ids: Optional[list]
    is_edited: bool


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: str
    ruleset_version: str
    image_id: Optional[int]
    ocr_block_id: Optional[int]
    bbox: Optional[dict]
    summary: str
    severity: str
    confidence: Optional[float]
    automated_result: str
    review_status: str
    review_comment: Optional[str]
    reviewed_at: Optional[datetime]


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: str
    ruleset_version: str
    result: str
    evidence_json: Optional[dict]
    detail: Optional[str]
    findings: List[FindingOut] = []


class InspectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    inspector_id: int
    location: str
    channel: str
    inspection_date: date
    category: Optional[str]
    package_structure: str
    origin: str
    special_status: Optional[str]
    product_name_hint: Optional[str]
    status: str
    ruleset_version: Optional[str]
    process_error: Optional[str]
    created_at: datetime
    closed_at: Optional[datetime]
    images: List[InspectionImageOut] = []
    fields: List[FieldOut] = []
    assessments: List[AssessmentOut] = []


class InspectionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    location: str
    channel: str
    inspection_date: date
    category: Optional[str]
    status: str
    ruleset_version: Optional[str]
    created_at: datetime
    image_count: int = 0
    finding_count: int = 0


class AssessmentPatch(BaseModel):
    review_status: str = Field(pattern="CONFIRMED|REJECTED|MANUAL VERIFICATION")
    review_comment: str = Field(default="", max_length=1000)


class FieldPatch(BaseModel):
    raw: str = Field(max_length=500)
    normalized: Optional[dict] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class CategoryPatch(BaseModel):
    category: str = Field(min_length=1, max_length=80)