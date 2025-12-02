"""
Reports API Endpoints

Generate and manage financial reports.
"""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.db.session import SessionDep
from app.services import report as report_service
from app.schemas.report import (
    ReportRequest,
    ReportResponse,
    ReportListItem,
    ReportData,
)

router = APIRouter()


@router.post("/{user_id}", response_model=ReportResponse)
async def generate_report(
    session: SessionDep,
    user_id: int,
    request: ReportRequest,
) -> ReportResponse:
    """
    Generate a new financial report.

    Parameters:
    - user_id: The user's ID
    - request: Report parameters (type, period, format)

    Returns:
    - Generated report with data and AI summary
    """
    report = await report_service.generate_report(
        session=session,
        user_id=user_id,
        request=request,
    )

    # Parse data JSON back to ReportData
    report_data = None
    if report.data:
        try:
            report_data = ReportData(**json.loads(report.data))
        except Exception:
            pass

    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        title=report.title,
        report_type=report.report_type,
        format=report.format,
        status=report.status,
        period_start=report.period_start,
        period_end=report.period_end,
        data=report_data,
        ai_summary=report.ai_summary,
        file_path=report.file_path,
        created_at=report.created_at,
    )


@router.get("/{user_id}", response_model=list[ReportListItem])
async def list_reports(
    session: SessionDep,
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReportListItem]:
    """
    List reports for a user.

    Returns:
    - List of reports (without full data for performance)
    """
    reports = await report_service.get_user_reports(
        session=session,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return [
        ReportListItem(
            id=r.id,
            title=r.title,
            report_type=r.report_type,
            format=r.format,
            status=r.status,
            period_start=r.period_start,
            period_end=r.period_end,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/{user_id}/{report_id}", response_model=ReportResponse)
async def get_report(
    session: SessionDep,
    user_id: int,
    report_id: int,
) -> ReportResponse:
    """
    Get a specific report with full data.
    """
    report = await report_service.get_report_by_id(
        session=session,
        report_id=report_id,
        user_id=user_id,
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Parse data JSON
    report_data = None
    if report.data:
        try:
            report_data = ReportData(**json.loads(report.data))
        except Exception:
            pass

    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        title=report.title,
        report_type=report.report_type,
        format=report.format,
        status=report.status,
        period_start=report.period_start,
        period_end=report.period_end,
        data=report_data,
        ai_summary=report.ai_summary,
        file_path=report.file_path,
        created_at=report.created_at,
    )


@router.get("/{user_id}/{report_id}/csv")
async def export_report_csv(
    session: SessionDep,
    user_id: int,
    report_id: int,
) -> PlainTextResponse:
    """
    Export a report as CSV.
    """
    report = await report_service.get_report_by_id(
        session=session,
        report_id=report_id,
        user_id=user_id,
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.data:
        raise HTTPException(status_code=400, detail="Report has no data")

    try:
        report_data = ReportData(**json.loads(report.data))
        csv_content = await report_service.export_to_csv(report_data)

        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="reporte_{report_id}.csv"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting: {str(e)}")


@router.delete("/{user_id}/{report_id}")
async def delete_report(
    session: SessionDep,
    user_id: int,
    report_id: int,
) -> dict:
    """
    Delete a report.
    """
    deleted = await report_service.delete_report(
        session=session,
        report_id=report_id,
        user_id=user_id,
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"deleted": True}


@router.post("/{user_id}/quick/{report_type}")
async def generate_quick_report(
    session: SessionDep,
    user_id: int,
    report_type: str,
    months: int = Query(default=1, ge=1, le=12),
) -> ReportResponse:
    """
    Quick report generation with preset periods.

    Parameters:
    - report_type: monthly_summary, category_breakdown, income_vs_expenses
    - months: Number of months back to analyze (default 1)
    """
    from datetime import timedelta

    now = datetime.now()
    period_end = now
    period_start = datetime(now.year, now.month, 1) - timedelta(days=30 * (months - 1))

    request = ReportRequest(
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        format="json",
        include_ai_summary=True,
    )

    report = await report_service.generate_report(
        session=session,
        user_id=user_id,
        request=request,
    )

    report_data = None
    if report.data:
        try:
            report_data = ReportData(**json.loads(report.data))
        except Exception:
            pass

    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        title=report.title,
        report_type=report.report_type,
        format=report.format,
        status=report.status,
        period_start=report.period_start,
        period_end=report.period_end,
        data=report_data,
        ai_summary=report.ai_summary,
        file_path=report.file_path,
        created_at=report.created_at,
    )
