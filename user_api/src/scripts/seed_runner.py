"""课程数据种子执行器"""

import asyncio
import logging

from scripts.seed_courses import seed_courses

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    logger.info("开始初始化课程数据...")

    try:
        count = await seed_courses()
        logger.info(f"课程数据初始化完成！共处理 {count} 条记录")
    except Exception as e:
        logger.error(f"课程数据初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
