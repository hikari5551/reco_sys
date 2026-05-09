from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

# =========================================================
# 数据库表结构
# =========================================================
# 注意：图片和模型文件不要直接存数据库，数据库只保存文件路径和结构化信息。
# =========================================================


class Dataset(Base):
    # 数据集表：管理不同版本的数据集。
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[list["ImageItem"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class ImageItem(Base):
    # 图片表：保存训练集、验证集、测试集图片的路径和元数据。
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(700), unique=True)
    url: Mapped[str] = mapped_column(String(800))
    split: Mapped[str] = mapped_column(String(20), default="test")  # train / val / test / unassigned
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped["Dataset"] = relationship(back_populates="images")
    annotations: Mapped[list["Annotation"]] = relationship(back_populates="image", cascade="all, delete-orphan")
    detections: Mapped[list["Detection"]] = relationship(back_populates="image", cascade="all, delete-orphan")


class Annotation(Base):
    # 人工标注表：保存人工标注框，可用于后续训练。
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), index=True)
    class_name: Mapped[str] = mapped_column(String(80), index=True)
    x1: Mapped[float] = mapped_column(Float)
    y1: Mapped[float] = mapped_column(Float)
    x2: Mapped[float] = mapped_column(Float)
    y2: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    image: Mapped["ImageItem"] = relationship(back_populates="annotations")


class ModelFile(Base):
    # 模型表：保存上传到服务器的 .pt 模型文件。
    __tablename__ = "model_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    file_path: Mapped[str] = mapped_column(String(700), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否作为当前默认模型
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Detection(Base):
    # 检测结果表：保存 YOLO 推理输出的类别、置信度和检测框。
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), index=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("model_files.id"), nullable=True)
    class_name: Mapped[str] = mapped_column(String(80), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    x1: Mapped[float] = mapped_column(Float)
    y1: Mapped[float] = mapped_column(Float)
    x2: Mapped[float] = mapped_column(Float)
    y2: Mapped[float] = mapped_column(Float)
    result_image_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    result_image_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    image: Mapped["ImageItem"] = relationship(back_populates="detections")
