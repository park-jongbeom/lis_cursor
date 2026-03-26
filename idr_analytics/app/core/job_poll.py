"""ARQ 잡 폴링용 공통 응답 조립."""

from __future__ import annotations

from typing import Any

from arq.connections import ArqRedis
from arq.jobs import Job, JobStatus
from fastapi import HTTPException, status


def _status_str(st: JobStatus) -> str:
    if st == JobStatus.complete:
        return "completed"
    if st == JobStatus.in_progress:
        return "running"
    if st in (JobStatus.queued, JobStatus.deferred):
        return "pending"
    return "not_found"


async def get_arq_job_view(arq_redis: ArqRedis, job_id: str) -> dict[str, Any]:
    job = Job(job_id, arq_redis)
    st = await job.status()
    if st == JobStatus.not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    out_status = _status_str(st)
    result: Any = None
    error: str | None = None
    if st == JobStatus.complete:
        ri = await job.result_info()
        if ri is None:
            out_status = "failed"
            error = "Missing result"
        elif ri.success:
            result = ri.result
        else:
            out_status = "failed"
            err = ri.result
            error = repr(err) if err is not None else "Job failed"
    return {"job_id": job_id, "status": out_status, "result": result, "error": error}
