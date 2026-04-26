"""课程数据种子脚本"""

import logging
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.database import AsyncSessionLocal
from models.course import Course

logger = logging.getLogger(__name__)


def load_courses_from_yaml() -> list[dict]:
    yaml_path = Path(__file__).parent.parent / "data" / "courses.yaml"

    logger.info(f"正在读取课程数据文件: {yaml_path}")

    if not yaml_path.exists():
        raise FileNotFoundError(f"课程数据文件不存在: {yaml_path}")

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    courses = data.get("courses", [])
    logger.info(f"成功读取 {len(courses)} 条课程数据")
    return courses


async def seed_courses() -> int:
    courses_data = load_courses_from_yaml()
    inserted_count = 0

    async with AsyncSessionLocal() as session:
        try:
            values = []
            for course in courses_data:
                values.append(
                    {
                        "title": course["title"],
                        "description": course["description"],
                        "price": Decimal(str(course["price"])),
                        "tag": course["tag"],
                    }
                )

            stmt = pg_insert(Course).values(values).on_conflict_do_nothing(index_elements=["title"])

            await session.execute(stmt)
            await session.commit()

            inserted_count = len(courses_data)
            logger.info(f"课程数据处理完成，共 {inserted_count} 条")

        except Exception as e:
            await session.rollback()
            logger.error(f"插入课程数据时发生错误: {e}")
            raise

    return inserted_count
