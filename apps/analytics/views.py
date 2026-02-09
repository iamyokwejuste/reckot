from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.core.cache import caches
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from plotly.subplots import make_subplots

import plotly.graph_objects as go

from apps.payments.models import Payment
from apps.tickets.models import Booking, Ticket
from apps.events.models import Event
from django.contrib.auth import get_user_model
from .utils import convert_to_usd

User = get_user_model()


def get_plotly_theme():
    return {
        "template": "plotly_dark",
        "paper_bgcolor": "rgba(31, 41, 55, 1)",
        "plot_bgcolor": "rgba(31, 41, 55, 1)",
        "font": {"color": "#e5e7eb"},
        "xaxis": {"gridcolor": "rgba(75, 85, 99, 0.3)"},
        "yaxis": {"gridcolor": "rgba(75, 85, 99, 0.3)"},
    }


def get_admin_context(request, title):
    context = {
        "site_header": admin.site.site_header,
        "site_title": admin.site.site_title,
        "site_url": "/",
        "has_permission": True,
        "available_apps": admin.site.get_app_list(request),
        "is_nav_sidebar_enabled": True,
        "is_popup": False,
        "title": title,
        "opts": None,
    }
    context.update(admin.site.each_context(request))
    return context


def dashboard_callback(request, context):
    cache = caches["analytics"]
    cached = cache.get("admin_dashboard_kpis")
    if cached is not None:
        context.update(cached)
        return context

    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)

    total_revenue_raw = Payment.objects.filter(
        status="CONFIRMED", created_at__gte=last_30_days
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_revenue = convert_to_usd(total_revenue_raw, "XAF")

    total_orders = Booking.objects.filter(created_at__gte=last_30_days).count()

    total_tickets = Ticket.objects.filter(booking__created_at__gte=last_30_days).count()

    active_events = Event.objects.filter(
        Q(start_at__gte=timezone.now()) | Q(end_at__gte=timezone.now())
    ).count()

    revenue_last_7_raw = Payment.objects.filter(
        status="CONFIRMED", created_at__gte=last_7_days
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    revenue_last_7 = convert_to_usd(revenue_last_7_raw, "XAF")

    orders_last_7 = Booking.objects.filter(created_at__gte=last_7_days).count()

    revenue_chart = generate_revenue_chart(last_30_days, today)
    sales_chart = generate_sales_chart(last_30_days, today)

    result = {
        "navigation": [
            {"title": "Dashboard", "link": "/admin/"},
            {"title": "Analytics", "link": "/admin/reports/revenue/"},
        ],
        "kpi_data": [
            {
                "title": "Total Revenue (30d)",
                "metric": f"${total_revenue:,.2f}",
                "footer": f"Last 7 days: ${revenue_last_7:,.2f}",
                "icon": "attach_money",
            },
            {
                "title": "Total Orders (30d)",
                "metric": str(total_orders),
                "footer": f"Last 7 days: {orders_last_7}",
                "icon": "shopping_cart",
            },
            {
                "title": "Tickets Sold (30d)",
                "metric": str(total_tickets),
                "footer": f"Active now: {total_tickets}",
                "icon": "confirmation_number",
            },
            {
                "title": "Active Events",
                "metric": str(active_events),
                "footer": "Currently running or upcoming",
                "icon": "event",
            },
        ],
        "charts": [
            {"title": "Revenue Trend", "html": revenue_chart},
            {"title": "Sales Overview", "html": sales_chart},
        ],
    }

    cache.set("admin_dashboard_kpis", result, 300)
    context.update(result)
    return context


def generate_revenue_chart(start_date, end_date):
    payments = (
        Payment.objects.filter(
            status="CONFIRMED",
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(revenue=Sum("amount"))
        .order_by("date")
    )

    dates = [p["date"] for p in payments]
    revenues = [float(convert_to_usd(p["revenue"], "XAF")) for p in payments]

    theme = get_plotly_theme()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=revenues,
            mode="lines+markers",
            name="Revenue",
            line=dict(color="#a78bfa", width=3),
            marker=dict(size=8, color="#a78bfa"),
        )
    )

    fig.update_layout(
        template=theme["template"],
        paper_bgcolor=theme["paper_bgcolor"],
        plot_bgcolor=theme["plot_bgcolor"],
        font=theme["font"],
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        xaxis=theme["xaxis"],
        yaxis=theme["yaxis"],
        hovermode="x unified",
    )

    return fig.to_html(
        include_plotlyjs="cdn", div_id="revenue_chart", config={"displayModeBar": False}
    )


def generate_sales_chart(start_date, end_date):
    orders = (
        Booking.objects.filter(
            created_at__date__gte=start_date, created_at__date__lte=end_date
        )
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    dates = [o["date"] for o in orders]
    counts = [o["count"] for o in orders]

    theme = get_plotly_theme()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=counts, name="Orders", marker_color="#a78bfa"))

    fig.update_layout(
        template=theme["template"],
        paper_bgcolor=theme["paper_bgcolor"],
        plot_bgcolor=theme["plot_bgcolor"],
        font=theme["font"],
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title="Date",
        yaxis_title="Number of Orders",
        xaxis=theme["xaxis"],
        yaxis=theme["yaxis"],
        hovermode="x unified",
    )

    return fig.to_html(
        include_plotlyjs="cdn", div_id="sales_chart", config={"displayModeBar": False}
    )


@staff_member_required
def revenue_analytics(request):
    today = timezone.now().date()
    last_90_days = today - timedelta(days=90)

    payments = Payment.objects.filter(status="CONFIRMED", created_at__gte=last_90_days)

    total_revenue_raw = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal(
        "0.00"
    )
    total_fees_raw = payments.aggregate(Sum("service_fee"))[
        "service_fee__sum"
    ] or Decimal("0.00")

    total_revenue = convert_to_usd(total_revenue_raw, "XAF")
    total_fees = convert_to_usd(total_fees_raw, "XAF")
    net_revenue = total_revenue - total_fees

    revenue_by_date = (
        payments.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(revenue=Sum("amount"), fees=Sum("service_fee"))
        .order_by("date")
    )

    dates = [r["date"] for r in revenue_by_date]
    revenues = [float(convert_to_usd(r["revenue"], "XAF")) for r in revenue_by_date]
    fees = [float(convert_to_usd(r["fees"] or 0, "XAF")) for r in revenue_by_date]
    net = [revenues[i] - fees[i] for i in range(len(revenues))]

    theme = get_plotly_theme()
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Revenue Over Time",
            "Fee Breakdown",
            "Net Revenue",
            "Payment Status",
        ),
        specs=[
            [{"type": "scatter"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "pie"}],
        ],
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=revenues,
            name="Total Revenue",
            line=dict(color="#a78bfa", width=3),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Pie(
            labels=["Service Fees", "Net Revenue"],
            values=[float(total_fees), float(net_revenue)],
            marker=dict(colors=["#a78bfa", "#34d399"]),
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(x=dates, y=net, name="Net Revenue", marker_color="#34d399"), row=2, col=1
    )

    payment_status = (
        Payment.objects.filter(created_at__gte=last_90_days)
        .values("status")
        .annotate(count=Count("id"))
    )

    fig.add_trace(
        go.Pie(
            labels=[p["status"] for p in payment_status],
            values=[p["count"] for p in payment_status],
            marker=dict(colors=["#34d399", "#ef4444", "#fbbf24", "#a78bfa", "#60a5fa"]),
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        height=800,
        showlegend=True,
        template=theme["template"],
        paper_bgcolor=theme["paper_bgcolor"],
        plot_bgcolor=theme["plot_bgcolor"],
        font=theme["font"],
    )

    fig.update_xaxes(gridcolor=theme["xaxis"]["gridcolor"])
    fig.update_yaxes(gridcolor=theme["yaxis"]["gridcolor"])

    chart_html = fig.to_html(include_plotlyjs="cdn", div_id="revenue_analytics")

    context = get_admin_context(request, "Revenue Analytics")
    context.update(
        {
            "total_revenue": total_revenue,
            "service_fees": total_fees,
            "net_revenue": net_revenue,
            "chart_html": chart_html,
        }
    )

    return render(request, "admin/analytics/revenue.html", context)


@staff_member_required
def event_analytics(request):
    events = Event.objects.annotate(
        revenue=Sum(
            "bookings__payment__amount", filter=Q(bookings__payment__status="CONFIRMED")
        ),
        tickets_sold=Count("ticket_types__tickets"),
        bookings_count=Count("bookings", distinct=True),
    ).order_by("-revenue")[:20]

    event_names = [e.title[:30] for e in events]
    event_revenues = [float(convert_to_usd(e.revenue or 0, "XAF")) for e in events]
    event_tickets = [e.tickets_sold for e in events]

    theme = get_plotly_theme()
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Top Events by Revenue", "Tickets Sold per Event"),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
    )

    fig.add_trace(
        go.Bar(
            y=event_names,
            x=event_revenues,
            orientation="h",
            marker_color="#a78bfa",
            name="Revenue",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            y=event_names,
            x=event_tickets,
            orientation="h",
            marker_color="#ec4899",
            name="Tickets",
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        height=600,
        showlegend=False,
        template=theme["template"],
        paper_bgcolor=theme["paper_bgcolor"],
        plot_bgcolor=theme["plot_bgcolor"],
        font=theme["font"],
    )

    fig.update_xaxes(gridcolor=theme["xaxis"]["gridcolor"])
    fig.update_yaxes(gridcolor=theme["yaxis"]["gridcolor"])

    chart_html = fig.to_html(include_plotlyjs="cdn", div_id="event_analytics")

    context = get_admin_context(request, "Event Performance")
    context.update(
        {
            "events": events,
            "chart_html": chart_html,
        }
    )

    return render(request, "admin/analytics/events.html", context)


@staff_member_required
def ticket_analytics(request):
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    tickets = (
        Ticket.objects.filter(booking__created_at__date__gte=last_30_days)
        .annotate(date=TruncDate("booking__created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    dates = [t["date"] for t in tickets]
    counts = [t["count"] for t in tickets]

    checked_in = Ticket.objects.filter(checked_in_at__isnull=False).count()
    not_checked_in = Ticket.objects.filter(
        checked_in_at__isnull=True, booking__status="CONFIRMED"
    ).count()

    theme = get_plotly_theme()
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Tickets Sold Over Time", "Check-in Status"),
        specs=[[{"type": "scatter"}, {"type": "pie"}]],
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=counts,
            mode="lines+markers",
            line=dict(color="#a78bfa", width=3),
            name="Tickets Sold",
            marker=dict(size=8, color="#a78bfa"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Pie(
            labels=["Checked In", "Not Checked In"],
            values=[checked_in, not_checked_in],
            marker=dict(colors=["#34d399", "#fbbf24"]),
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        height=400,
        showlegend=True,
        template=theme["template"],
        paper_bgcolor=theme["paper_bgcolor"],
        plot_bgcolor=theme["plot_bgcolor"],
        font=theme["font"],
    )

    fig.update_xaxes(gridcolor=theme["xaxis"]["gridcolor"])
    fig.update_yaxes(gridcolor=theme["yaxis"]["gridcolor"])

    chart_html = fig.to_html(include_plotlyjs="cdn", div_id="ticket_analytics")

    context = get_admin_context(request, "Ticket Analytics")
    context.update(
        {
            "total_tickets": Ticket.objects.count(),
            "checked_in": checked_in,
            "not_checked_in": not_checked_in,
            "chart_html": chart_html,
        }
    )

    return render(request, "admin/analytics/tickets.html", context)


@staff_member_required
def payment_analytics(request):
    today = timezone.now().date()
    last_90_days = today - timedelta(days=90)

    payments = Payment.objects.filter(created_at__date__gte=last_90_days)

    total_volume_raw = payments.filter(status="CONFIRMED").aggregate(Sum("amount"))[
        "amount__sum"
    ] or Decimal("0.00")
    failed_volume_raw = payments.filter(status="FAILED").aggregate(Sum("amount"))[
        "amount__sum"
    ] or Decimal("0.00")
    pending_volume_raw = payments.filter(status="PENDING").aggregate(Sum("amount"))[
        "amount__sum"
    ] or Decimal("0.00")

    total_volume = convert_to_usd(total_volume_raw, "XAF")
    failed_volume = convert_to_usd(failed_volume_raw, "XAF")
    pending_volume = convert_to_usd(pending_volume_raw, "XAF")

    payments_by_gateway = (
        payments.filter(status="CONFIRMED")
        .values("provider")
        .annotate(volume=Sum("amount"), count=Count("id"))
    )

    gateways = [p["provider"] for p in payments_by_gateway]
    gateway_volumes = [
        float(convert_to_usd(p["volume"], "XAF")) for p in payments_by_gateway
    ]
    gateway_counts = [p["count"] for p in payments_by_gateway]

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Payment Volume by Gateway",
            "Transaction Count by Gateway",
            "Payment Status Distribution",
            "Processing Fees Over Time",
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "pie"}, {"type": "scatter"}],
        ],
    )

    fig.add_trace(
        go.Bar(x=gateways, y=gateway_volumes, marker_color="#8b5cf6", name="Volume"),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(x=gateways, y=gateway_counts, marker_color="#ec4899", name="Count"),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Pie(
            labels=["Confirmed", "Failed", "Pending"],
            values=[float(total_volume), float(failed_volume), float(pending_volume)],
            marker=dict(colors=["#34d399", "#ef4444", "#fbbf24"]),
        ),
        row=2,
        col=1,
    )

    fees_by_date = (
        payments.filter(status="CONFIRMED")
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(fees=Sum("service_fee"))
        .order_by("date")
    )

    fee_dates = [f["date"] for f in fees_by_date]
    fee_amounts = [float(convert_to_usd(f["fees"] or 0, "XAF")) for f in fees_by_date]

    fig.add_trace(
        go.Scatter(
            x=fee_dates,
            y=fee_amounts,
            mode="lines+markers",
            line=dict(color="#fbbf24", width=3),
            name="Service Fees",
            marker=dict(size=8, color="#fbbf24"),
        ),
        row=2,
        col=2,
    )

    theme = get_plotly_theme()
    fig.update_layout(
        height=800,
        showlegend=False,
        template=theme["template"],
        paper_bgcolor=theme["paper_bgcolor"],
        plot_bgcolor=theme["plot_bgcolor"],
        font=theme["font"],
    )

    fig.update_xaxes(gridcolor=theme["xaxis"]["gridcolor"])
    fig.update_yaxes(gridcolor=theme["yaxis"]["gridcolor"])

    chart_html = fig.to_html(include_plotlyjs="cdn", div_id="payment_analytics")

    total_fees_raw = payments.filter(status="CONFIRMED").aggregate(
        service=Sum("service_fee")
    )

    service_fees_usd = convert_to_usd(
        total_fees_raw["service"] or Decimal("0.00"), "XAF"
    )

    context = get_admin_context(request, "Payment Analytics")
    context.update(
        {
            "total_volume": total_volume,
            "service_fees": service_fees_usd,
            "chart_html": chart_html,
        }
    )

    return render(request, "admin/analytics/payments.html", context)
