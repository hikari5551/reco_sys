from datetime import datetime
from pydantic import BaseModel, Field

# =========================================================
# 接口请求和响应模型
# =========================================================


class DatasetCreate(BaseModel):
    # 创建数据集时客户端提交的数据。
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class DatasetOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class ImageOut(BaseModel):
    id: int
    dataset_id: int
    filename: str
    original_name: str
    url: str
    split: str
    sha256: str
    width: int | None
    height: int | None
    size_bytes: int
    created_at: datetime
    model_config = {"from_attributes": True}


class AnnotationCreate(BaseModel):
    class_name: str = Field(min_length=1, max_length=80)
    x1: float
    y1: float
    x2: float
    y2: float
    note: str | None = None


class AnnotationOut(AnnotationCreate):
    id: int
    image_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class ModelOut(BaseModel):
    id: int
    name: str
    file_path: str
    active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class DetectionOut(BaseModel):
    id: int
    image_id: int
    model_id: int | None
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    result_image_url: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class DetectResponse(BaseModel):
    # 检测接口返回：包含检测结果图 URL 和检测框列表。
    image_id: int
    result_image_url: str | None
    detections: list[DetectionOut]
