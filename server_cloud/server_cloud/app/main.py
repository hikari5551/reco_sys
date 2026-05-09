import hashlib
import shutil
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import APP_NAME, MODEL_DIR, PUBLIC_BASE_URL, RESULT_DIR, UPLOAD_DIR
from app.db import Base, engine, get_db
from app.models import Annotation, Dataset, Detection, ImageItem, ModelFile
from app.schemas import (
    AnnotationCreate,
    AnnotationOut,
    DatasetCreate,
    DatasetOut,
    DetectResponse,
    DetectionOut,
    ImageOut,
    ModelOut,
)
from app.security import require_api_key
from app.yolo_service import yolo_service

# =========================================================
# FastAPI 后端入口
# =========================================================
# 服务器负责：数据集、测试集、模型、YOLO 运行和检测结果保存。
# 客户端只负责调用这些接口。
# =========================================================

Base.metadata.create_all(bind=engine)

app = FastAPI(title=APP_NAME, version="2.0.0")

# 暴露图片和检测结果图，客户端可通过 URL 直接显示。
app.mount("/files", StaticFiles(directory=str(UPLOAD_DIR)), name="files")
app.mount("/results", StaticFiles(directory=str(RESULT_DIR)), name="results")


def sha256_file(path: Path) -> str:
    # 计算文件 SHA256，便于追踪和去重。
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_image_suffix(filename: str) -> str:
    # 检查上传文件是否为允许的图片格式。
    suffix = Path(filename).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise HTTPException(status_code=400, detail="仅支持 jpg/jpeg/png/bmp/webp 图片")
    return suffix


@app.get("/health")
def health():
    # 健康检查接口，客户端用它测试服务器是否在线。
    return {"status": "ok", "app": APP_NAME}


@app.post("/api/datasets", response_model=DatasetOut, dependencies=[Depends(require_api_key)])
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    # 创建数据集。
    exists = db.query(Dataset).filter(Dataset.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="数据集名称已存在")

    item = Dataset(name=payload.name, description=payload.description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/datasets", response_model=list[DatasetOut], dependencies=[Depends(require_api_key)])
def list_datasets(db: Session = Depends(get_db)):
    # 查看数据集列表。
    return db.query(Dataset).order_by(Dataset.id.desc()).all()


@app.post("/api/datasets/{dataset_id}/images", response_model=ImageOut, dependencies=[Depends(require_api_key)])
def upload_image(
    dataset_id: int,
    split: str = Form(default="test"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 上传图片到服务器。
    # split 可选：train / val / test / unassigned。
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    if split not in ["train", "val", "test", "unassigned"]:
        raise HTTPException(status_code=400, detail="split 必须是 train/val/test/unassigned")

    suffix = ensure_image_suffix(file.filename or "")
    folder = UPLOAD_DIR / f"dataset_{dataset_id}" / split
    folder.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = folder / stored_name

    with saved_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # 校验图片，并读取宽高。
    try:
        with Image.open(saved_path) as img:
            width, height = img.size
    except Exception:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="无效图片文件")

    item = ImageItem(
        dataset_id=dataset_id,
        filename=stored_name,
        original_name=file.filename or stored_name,
        file_path=str(saved_path),
        url=f"{PUBLIC_BASE_URL}/files/dataset_{dataset_id}/{split}/{stored_name}",
        split=split,
        sha256=sha256_file(saved_path),
        width=width,
        height=height,
        size_bytes=saved_path.stat().st_size,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/datasets/{dataset_id}/images", response_model=list[ImageOut], dependencies=[Depends(require_api_key)])
def list_images(dataset_id: int, split: str | None = None, db: Session = Depends(get_db)):
    # 查看指定数据集下的图片。
    q = db.query(ImageItem).filter(ImageItem.dataset_id == dataset_id)
    if split:
        q = q.filter(ImageItem.split == split)
    return q.order_by(ImageItem.id.desc()).all()


@app.post("/api/images/{image_id}/annotations", response_model=AnnotationOut, dependencies=[Depends(require_api_key)])
def create_annotation(image_id: int, payload: AnnotationCreate, db: Session = Depends(get_db)):
    # 保存人工标注框。
    image = db.get(ImageItem, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    if payload.x2 <= payload.x1 or payload.y2 <= payload.y1:
        raise HTTPException(status_code=400, detail="标注框坐标不合法")

    item = Annotation(image_id=image_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/images/{image_id}/annotations", response_model=list[AnnotationOut], dependencies=[Depends(require_api_key)])
def list_annotations(image_id: int, db: Session = Depends(get_db)):
    # 查看某张图片的人工标注框。
    return db.query(Annotation).filter(Annotation.image_id == image_id).order_by(Annotation.id.asc()).all()


@app.post("/api/models/upload", response_model=ModelOut, dependencies=[Depends(require_api_key)])
def upload_model(
    name: str = Form(...),
    active: bool = Form(default=True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 上传 .pt 模型到服务器。
    if Path(file.filename or "").suffix.lower() != ".pt":
        raise HTTPException(status_code=400, detail="仅支持 .pt 模型文件")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'model.pt').name}"
    saved_path = MODEL_DIR / stored_name

    with saved_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # 如果该模型设为 active，则关闭其他模型的 active 状态。
    if active:
        db.query(ModelFile).update({ModelFile.active: False})

    item = ModelFile(name=name, file_path=str(saved_path), active=active)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/models", response_model=list[ModelOut], dependencies=[Depends(require_api_key)])
def list_models(db: Session = Depends(get_db)):
    # 查看模型列表。
    return db.query(ModelFile).order_by(ModelFile.id.desc()).all()


@app.post("/api/models/{model_id}/activate", response_model=ModelOut, dependencies=[Depends(require_api_key)])
def activate_model(model_id: int, db: Session = Depends(get_db)):
    # 设置某个模型为当前默认模型。
    model = db.get(ModelFile, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    db.query(ModelFile).update({ModelFile.active: False})
    model.active = True
    db.commit()
    db.refresh(model)
    return model


@app.post("/api/images/{image_id}/detect", response_model=DetectResponse, dependencies=[Depends(require_api_key)])
def detect_image(image_id: int, model_id: int | None = None, conf: float = 0.25, db: Session = Depends(get_db)):
    # 对服务器中已经上传的图片执行 YOLO 检测。
    image = db.get(ImageItem, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    if model_id is None:
        model = db.query(ModelFile).filter(ModelFile.active == True).order_by(ModelFile.id.desc()).first()
    else:
        model = db.get(ModelFile, model_id)

    if not model:
        raise HTTPException(status_code=404, detail="没有可用模型，请先上传 .pt 模型")

    try:
        raw_detections = yolo_service.predict(image.file_path, model.file_path, conf=conf)
        result_path, result_url = yolo_service.draw_result_image(image.file_path, raw_detections)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"YOLO 检测失败：{exc}")

    # 删除同一图片、同一模型下的旧检测结果，避免重复显示。
    db.query(Detection).filter(Detection.image_id == image_id, Detection.model_id == model.id).delete()

    items = []
    for det in raw_detections:
        item = Detection(
            image_id=image_id,
            model_id=model.id,
            result_image_path=result_path,
            result_image_url=result_url,
            **det,
        )
        db.add(item)
        items.append(item)

    db.commit()
    for item in items:
        db.refresh(item)

    return DetectResponse(image_id=image_id, result_image_url=result_url, detections=items)


@app.post("/api/datasets/{dataset_id}/batch-detect", dependencies=[Depends(require_api_key)])
def batch_detect(dataset_id: int, split: str = "test", conf: float = 0.25, db: Session = Depends(get_db)):
    # 批量检测某个数据集的某个 split。
    # 2GB 内存服务器不建议一次处理太多图片，真实大批量任务建议后续改成队列。
    model = db.query(ModelFile).filter(ModelFile.active == True).order_by(ModelFile.id.desc()).first()
    if not model:
        raise HTTPException(status_code=404, detail="没有可用模型，请先上传并激活 .pt 模型")

    images = db.query(ImageItem).filter(ImageItem.dataset_id == dataset_id, ImageItem.split == split).order_by(ImageItem.id.asc()).all()
    summary = []

    for image in images:
        try:
            raw_detections = yolo_service.predict(image.file_path, model.file_path, conf=conf)
            result_path, result_url = yolo_service.draw_result_image(image.file_path, raw_detections)

            db.query(Detection).filter(Detection.image_id == image.id, Detection.model_id == model.id).delete()

            for det in raw_detections:
                db.add(Detection(
                    image_id=image.id,
                    model_id=model.id,
                    result_image_path=result_path,
                    result_image_url=result_url,
                    **det,
                ))

            summary.append({"image_id": image.id, "count": len(raw_detections), "result_image_url": result_url})
        except Exception as exc:
            summary.append({"image_id": image.id, "error": str(exc)})

    db.commit()
    return {"dataset_id": dataset_id, "split": split, "total": len(images), "items": summary}


@app.get("/api/images/{image_id}/detections", response_model=list[DetectionOut], dependencies=[Depends(require_api_key)])
def list_detections(image_id: int, db: Session = Depends(get_db)):
    # 查看某张图片的检测结果。
    return db.query(Detection).filter(Detection.image_id == image_id).order_by(Detection.id.asc()).all()


@app.get("/api/stats", dependencies=[Depends(require_api_key)])
def stats(db: Session = Depends(get_db)):
    # 系统统计信息，用于前端首页或状态面板。
    return {
        "datasets": db.query(func.count(Dataset.id)).scalar(),
        "images": db.query(func.count(ImageItem.id)).scalar(),
        "annotations": db.query(func.count(Annotation.id)).scalar(),
        "models": db.query(func.count(ModelFile.id)).scalar(),
        "detections": db.query(func.count(Detection.id)).scalar(),
    }
