"""
Report Service

Generates financial reports with data analysis and AI summaries.
"""

import json
from datetime import datetime
from typing import Any

from sqlmodel import and_, col, select

from app.core.llm import get_model
from app.db.session import SessionDep
from app.models.category import Category
from app.models.report import Report, ReportStatus
from app.models.transaction import Transaction
from app.schemas.report import (
    CategoryBreakdown,
    MonthlyTrend,
    ReportData,
    ReportRequest,
)


async def generate_report(
    session: SessionDep,
    user_id: int,
    request: ReportRequest,
) -> Report:
    """Generate a financial report for a user."""

    # Create report record
    title = (
        request.title
        or f"Reporte {request.report_type} - {request.period_start.strftime('%Y-%m-%d')}"
    )

    report = Report(
        user_id=user_id,
        title=title,
        report_type=request.report_type,
        format=request.format,
        status=ReportStatus.GENERATING.value,
        period_start=request.period_start,
        period_end=request.period_end,
    )
    session.add(report)
    session.commit()
    session.refresh(report)

    try:
        # Generate report data
        report_data = await _calculate_report_data(
            session, user_id, request.period_start, request.period_end
        )

        # Generate AI summary if requested
        ai_summary = None
        if request.include_ai_summary:
            ai_summary = await _generate_ai_summary(report_data, request.report_type)

        # Update report with data
        report.data = json.dumps(report_data.model_dump())
        report.ai_summary = ai_summary
        report.status = ReportStatus.COMPLETED.value

    except Exception as e:
        report.status = ReportStatus.FAILED.value
        report.ai_summary = f"Error generando reporte: {str(e)}"

    session.add(report)
    session.commit()
    session.refresh(report)

    return report


async def _calculate_report_data(
    session: SessionDep,
    user_id: int,
    period_start: datetime,
    period_end: datetime,
) -> ReportData:
    """Calculate all report metrics from transactions."""

    # Get all transactions in period
    transactions = session.exec(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .where(
            and_(
                Transaction.date >= period_start,
                Transaction.date <= period_end,
            )
        )
    ).all()

    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.transaction_type == "income")
    total_expenses = sum(
        t.amount for t in transactions if t.transaction_type == "expense"
    )
    net_balance = total_income - total_expenses
    savings_rate = (net_balance / total_income * 100) if total_income > 0 else 0

    # Category breakdown
    category_totals: dict[int, dict[str, Any]] = {}
    for t in transactions:
        if t.transaction_type == "expense":
            if t.category_id not in category_totals:
                cat = session.exec(
                    select(Category).where(Category.id == t.category_id)
                ).first()
                category_totals[t.category_id] = {
                    "name": cat.name if cat else "Sin categoría",
                    "amount": 0,
                    "count": 0,
                }
            category_totals[t.category_id]["amount"] += t.amount
            category_totals[t.category_id]["count"] += 1

    category_breakdown = [
        CategoryBreakdown(
            category_id=cat_id,
            category_name=data["name"],
            total_amount=data["amount"],
            percentage=(data["amount"] / total_expenses * 100)
            if total_expenses > 0
            else 0,
            transaction_count=data["count"],
        )
        for cat_id, data in sorted(
            category_totals.items(),
            key=lambda x: x[1]["amount"],
            reverse=True,
        )
    ]

    # Monthly trends
    monthly_data: dict[str, dict[str, float]] = {}
    for t in transactions:
        key = f"{t.date.year}-{t.date.month:02d}"
        if key not in monthly_data:
            monthly_data[key] = {"income": 0, "expenses": 0}
        if t.transaction_type == "income":
            monthly_data[key]["income"] += t.amount
        else:
            monthly_data[key]["expenses"] += t.amount

    monthly_trends = [
        MonthlyTrend(
            month=key.split("-")[1],
            year=int(key.split("-")[0]),
            income=data["income"],
            expenses=data["expenses"],
            balance=data["income"] - data["expenses"],
        )
        for key, data in sorted(monthly_data.items())
    ]

    # Top expenses (individual transactions)
    expense_transactions = [t for t in transactions if t.transaction_type == "expense"]
    expense_transactions.sort(key=lambda x: x.amount, reverse=True)
    top_expenses = [
        {
            "description": t.description,
            "amount": t.amount,
            "date": t.date.strftime("%Y-%m-%d"),
            "category_id": t.category_id,
        }
        for t in expense_transactions[:10]
    ]

    # Income sources
    income_by_category: dict[int, float] = {}
    for t in transactions:
        if t.transaction_type == "income":
            if t.category_id not in income_by_category:
                income_by_category[t.category_id] = 0
            income_by_category[t.category_id] += t.amount

    income_sources = []
    for cat_id, amount in sorted(
        income_by_category.items(), key=lambda x: x[1], reverse=True
    ):
        cat = session.exec(select(Category).where(Category.id == cat_id)).first()
        income_sources.append(
            {
                "category_id": cat_id,
                "category_name": cat.name if cat else "Sin categoría",
                "amount": amount,
                "percentage": (amount / total_income * 100) if total_income > 0 else 0,
            }
        )

    return ReportData(
        period_start=period_start.strftime("%Y-%m-%d"),
        period_end=period_end.strftime("%Y-%m-%d"),
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=net_balance,
        savings_rate=round(savings_rate, 1),
        transaction_count=len(transactions),
        category_breakdown=category_breakdown,
        monthly_trends=monthly_trends,
        top_expenses=top_expenses,
        income_sources=income_sources,
    )


async def _generate_ai_summary(report_data: ReportData, report_type: str) -> str:
    """Generate AI summary for the report."""
    try:
        model = get_model()

        prompt = f"""Eres un asesor financiero analizando un reporte. Genera un resumen ejecutivo breve (máximo 4 oraciones) en español.

Datos del reporte ({report_type}):
- Período: {report_data.period_start} a {report_data.period_end}
- Ingresos totales: ${report_data.total_income:,.2f}
- Gastos totales: ${report_data.total_expenses:,.2f}
- Balance neto: ${report_data.net_balance:,.2f}
- Tasa de ahorro: {report_data.savings_rate}%
- Transacciones: {report_data.transaction_count}
- Categorías principales de gasto: {", ".join([f"{c.category_name} (${c.total_amount:,.2f})" for c in report_data.category_breakdown[:3]])}

Genera un resumen ejecutivo conciso con insights clave y una recomendación práctica."""

        from pydantic_ai import Agent

        agent = Agent(model=model)
        result = await agent.run(prompt)
        return str(result.output)

    except Exception as e:
        return f"No se pudo generar resumen automático: {str(e)}"


async def get_user_reports(
    session: SessionDep,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> list[Report]:
    """Get reports for a user."""
    query = (
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(col(Report.created_at).desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(query).all())


async def get_report_by_id(
    session: SessionDep,
    report_id: int,
    user_id: int,
) -> Report | None:
    """Get a specific report by ID (scoped to user)."""
    query = select(Report).where(
        and_(Report.id == report_id, Report.user_id == user_id)
    )
    return session.exec(query).first()


async def delete_report(
    session: SessionDep,
    report_id: int,
    user_id: int,
) -> bool:
    """Delete a report."""
    report = await get_report_by_id(session, report_id, user_id)
    if report:
        session.delete(report)
        session.commit()
        return True
    return False


async def export_to_csv(report_data: ReportData) -> str:
    """Convert report data to CSV format."""
    lines = []

    # Header
    lines.append("Reporte Financiero")
    lines.append(f"Período,{report_data.period_start},{report_data.period_end}")
    lines.append("")

    # Summary
    lines.append("Resumen")
    lines.append(f"Ingresos Totales,${report_data.total_income:.2f}")
    lines.append(f"Gastos Totales,${report_data.total_expenses:.2f}")
    lines.append(f"Balance Neto,${report_data.net_balance:.2f}")
    lines.append(f"Tasa de Ahorro,{report_data.savings_rate}%")
    lines.append(f"Total Transacciones,{report_data.transaction_count}")
    lines.append("")

    # Category breakdown
    lines.append("Desglose por Categoría")
    lines.append("Categoría,Monto,Porcentaje,Transacciones")
    for cat in report_data.category_breakdown:
        lines.append(
            f"{cat.category_name},${cat.total_amount:.2f},{cat.percentage:.1f}%,{cat.transaction_count}"
        )
    lines.append("")

    # Monthly trends
    lines.append("Tendencia Mensual")
    lines.append("Mes,Año,Ingresos,Gastos,Balance")
    for trend in report_data.monthly_trends:
        lines.append(
            f"{trend.month},{trend.year},${trend.income:.2f},${trend.expenses:.2f},${trend.balance:.2f}"
        )

    return "\n".join(lines)
