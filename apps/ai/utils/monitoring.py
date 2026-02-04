import time
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from apps.ai.models import AIUsageLog

logger = logging.getLogger(__name__)


class AIMetricsCollector:
    def __init__(self):
        self.cache_prefix = "ai_metrics"
        self.cache_ttl = 300

    def record_request(
        self,
        operation: str,
        duration_ms: float,
        tokens_used: int = 0,
        model: str = "unknown",
        success: bool = True,
        error: Optional[str] = None
    ):
        timestamp = time.time()
        cache_key = f"{self.cache_prefix}:requests:{int(timestamp // 60)}"

        metrics = cache.get(cache_key, [])
        metrics.append({
            'operation': operation,
            'duration_ms': duration_ms,
            'tokens': tokens_used,
            'model': model,
            'success': success,
            'error': error,
            'timestamp': timestamp
        })
        cache.set(cache_key, metrics, self.cache_ttl)

        self._update_counters(operation, success, tokens_used)

    def _update_counters(self, operation: str, success: bool, tokens: int):
        total_key = f"{self.cache_prefix}:total_requests"
        success_key = f"{self.cache_prefix}:successful_requests"
        tokens_key = f"{self.cache_prefix}:total_tokens"

        cache.incr(total_key, delta=1)
        if success:
            cache.incr(success_key, delta=1)
        if tokens > 0:
            cache.incr(tokens_key, delta=tokens)

    def get_real_time_metrics(self) -> Dict[str, Any]:
        now = time.time()
        current_minute = int(now // 60)

        recent_metrics = []
        for i in range(5):
            cache_key = f"{self.cache_prefix}:requests:{current_minute - i}"
            minute_metrics = cache.get(cache_key, [])
            recent_metrics.extend(minute_metrics)

        if not recent_metrics:
            return self._empty_metrics()

        total_requests = len(recent_metrics)
        successful = sum(1 for m in recent_metrics if m['success'])
        failed = total_requests - successful

        durations = [m['duration_ms'] for m in recent_metrics]
        tokens = sum(m['tokens'] for m in recent_metrics)

        operations = defaultdict(int)
        models = defaultdict(int)
        errors = defaultdict(int)

        for metric in recent_metrics:
            operations[metric['operation']] += 1
            models[metric['model']] += 1
            if not metric['success'] and metric.get('error'):
                errors[metric['error']] += 1

        return {
            'total_requests': total_requests,
            'successful_requests': successful,
            'failed_requests': failed,
            'success_rate': (successful / total_requests * 100) if total_requests > 0 else 0,
            'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
            'p50_duration_ms': self._percentile(durations, 50),
            'p95_duration_ms': self._percentile(durations, 95),
            'p99_duration_ms': self._percentile(durations, 99),
            'total_tokens': tokens,
            'avg_tokens_per_request': tokens / total_requests if total_requests > 0 else 0,
            'operations_breakdown': dict(operations),
            'models_breakdown': dict(models),
            'errors_breakdown': dict(errors),
            'time_window': '5 minutes'
        }

    def get_historical_metrics(self, hours: int = 24) -> Dict[str, Any]:
        since = timezone.now() - timedelta(hours=hours)

        usage_logs = AIUsageLog.objects.filter(created_at__gte=since)

        total_count = usage_logs.count()
        successful_count = usage_logs.filter(error__isnull=True).count()

        aggregates = usage_logs.aggregate(
            total_tokens=Sum('tokens_used'),
            avg_tokens=Avg('tokens_used'),
            avg_duration=Avg('execution_time'),
        )

        operations = list(
            usage_logs.values('operation_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        models = list(
            usage_logs.values('model_accessed')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        hourly_breakdown = list(
            usage_logs.extra(select={'hour': 'strftime("%%Y-%%m-%%d %%H:00", created_at)'})
            .values('hour')
            .annotate(
                total_requests=Count('id'),
                total_tokens=Sum('tokens_used'),
                avg_duration=Avg('execution_time')
            )
            .order_by('hour')
        )

        estimated_cost_usd = self._estimate_cost(aggregates.get('total_tokens') or 0)

        return {
            'time_range_hours': hours,
            'total_requests': total_count,
            'successful_requests': successful_count,
            'failed_requests': total_count - successful_count,
            'success_rate': (successful_count / total_count * 100) if total_count > 0 else 0,
            'total_tokens': aggregates.get('total_tokens') or 0,
            'avg_tokens_per_request': aggregates.get('avg_tokens') or 0,
            'avg_duration_ms': (aggregates.get('avg_duration') or 0) * 1000,
            'estimated_cost_usd': estimated_cost_usd,
            'operations_breakdown': operations,
            'models_breakdown': models,
            'hourly_trends': hourly_breakdown
        }

    def get_user_metrics(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        since = timezone.now() - timedelta(days=days)

        user_logs = AIUsageLog.objects.filter(
            user_id=user_id,
            created_at__gte=since
        )

        total_count = user_logs.count()
        aggregates = user_logs.aggregate(
            total_tokens=Sum('tokens_used'),
            avg_duration=Avg('execution_time'),
        )

        operations = list(
            user_logs.values('operation_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        daily_usage = list(
            user_logs.extra(select={'date': 'DATE(created_at)'})
            .values('date')
            .annotate(
                requests=Count('id'),
                tokens=Sum('tokens_used')
            )
            .order_by('date')
        )

        return {
            'user_id': user_id,
            'time_range_days': days,
            'total_requests': total_count,
            'total_tokens': aggregates.get('total_tokens') or 0,
            'avg_duration_ms': (aggregates.get('avg_duration') or 0) * 1000,
            'favorite_operations': operations[:5],
            'daily_usage': daily_usage,
            'estimated_cost_usd': self._estimate_cost(aggregates.get('total_tokens') or 0)
        }

    def get_system_health(self) -> Dict[str, Any]:
        from apps.ai.circuit_breaker import gemini_circuit_breaker, model_fallback

        circuit_metrics = gemini_circuit_breaker.get_metrics()

        real_time = self.get_real_time_metrics()

        health_score = 100
        health_issues = []

        if circuit_metrics['state'] == 'open':
            health_score -= 50
            health_issues.append("Circuit breaker is OPEN")

        if real_time['success_rate'] < 90:
            health_score -= 20
            health_issues.append(f"Low success rate: {real_time['success_rate']:.1f}%")

        if real_time['p95_duration_ms'] > 5000:
            health_score -= 15
            health_issues.append(f"High latency: P95 = {real_time['p95_duration_ms']:.0f}ms")

        if real_time['failed_requests'] > 10:
            health_score -= 15
            health_issues.append(f"High error count: {real_time['failed_requests']}")

        health_status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "critical"

        return {
            'status': health_status,
            'health_score': max(0, health_score),
            'issues': health_issues,
            'circuit_breaker': circuit_metrics,
            'current_model': model_fallback.get_current_model(),
            'real_time_metrics': real_time,
            'timestamp': datetime.now().isoformat()
        }

    def _percentile(self, values: List[float], percentile: int) -> float:
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _estimate_cost(self, tokens: int) -> float:
        cost_per_million_tokens = 0.075
        return (tokens / 1_000_000) * cost_per_million_tokens

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'success_rate': 0,
            'avg_duration_ms': 0,
            'p50_duration_ms': 0,
            'p95_duration_ms': 0,
            'p99_duration_ms': 0,
            'total_tokens': 0,
            'avg_tokens_per_request': 0,
            'operations_breakdown': {},
            'models_breakdown': {},
            'errors_breakdown': {},
            'time_window': '5 minutes'
        }


metrics_collector = AIMetricsCollector()
