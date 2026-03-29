# FastAPI + EconomyController 缓存示例
# 运行: uvicorn examples.lms_api:app --reload

from fastapi import FastAPI, Query
from core.economy_controller import EconomyController

app = FastAPI(title="LMS 课程接口示例")
cache = EconomyController()


@app.get("/api/courses")
def get_courses(
    grade: int = Query(..., description="年级"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取课程列表

    - 按年级+分页维度隔离缓存
    - TTL=1小时（公开数据变化不频繁）
    """
    # 生成缓存键
    cache_key = f"courses:grade={grade}:page={page}:size={page_size}"

    # 1. 尝试从缓存读取
    cached = cache.get_cached_result(cache_key)
    if cached:
        return {
            "source": "cache",
            "message": "缓存命中",
            "data": cached,
        }

    # 2. 模拟数据库查询（替换为你的真实 db.query 逻辑）
    data = [
        {
            "id": i + 1,
            "title": f"课程{grade}-{page}-{i+1}",
            "teacher": "张老师",
            "cover": f"https://example.com/cover/{grade}_{page}_{i+1}.webp",
        }
        for i in range(page_size)
    ]

    # 3. 写入缓存（TTL=1小时）
    cache.save_cache(cache_key, data, ttl_hours=1)

    return {
        "source": "db",
        "message": "缓存未命中，查询数据库后写入缓存",
        "data": data,
    }


@app.get("/api/student/progress")
def get_student_progress(
    student_id: int = Query(..., description="学生ID"),
    course_id: int = Query(..., description="课程ID"),
):
    """获取学生学习进度（用户级隔离）

    - 按 student_id + course_id 隔离
    - TTL=5分钟（兼顾实时性与性能）
    """
    cache_key = f"student_progress:{student_id}:course={course_id}"

    cached = cache.get_cached_result(cache_key)
    if cached:
        return {"source": "cache", "data": cached}

    # 模拟数据库查询
    data = {
        "student_id": student_id,
        "course_id": course_id,
        "chapter_id": 3,
        "watched_sec": 1250,
        "score": 85,
        "last_updated": "2026-03-29 10:30:00",
    }

    # TTL=5分钟
    cache.save_cache(cache_key, data, ttl_hours=5 / 60)

    return {"source": "db", "data": data}


@app.get("/api/stats")
def get_stats():
    """获取缓存统计"""
    return cache.get_metrics_json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)