"""HTTP latency sampling shared by the four-process recommendation benchmark."""
import asyncio
from collections import Counter
import math
import statistics
from time import perf_counter, process_time

import httpx


def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p / 100
    lo, hi = math.floor(position), math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def latency(values):
    if not values:
        return None
    return {name: round(value, 3) for name, value in {
        'mean': statistics.mean(values), 'min': min(values), 'max': max(values),
        'p50': percentile(values, 50), 'p95': percentile(values, 95), 'p99': percentile(values, 99),
    }.items()}


def valid(body, candidate):
    if not isinstance(body, dict) or body.get('candidateId') != candidate:
        return False
    items, total = body.get('recommendations'), body.get('total')
    if not isinstance(items, list) or not isinstance(total, int) or total < len(items):
        return False
    return len(items) <= 10 and all(isinstance(r, dict) and isinstance(r.get('jobId'), str)
        and isinstance(r.get('matchScore'), (int, float)) and 0 <= r['matchScore'] <= 100
        and isinstance(r.get('breakdown'), dict) for r in items)


async def execute(client, route, count, concurrency, candidate, *, progress=False):
    remaining = iter(range(count))
    samples = [None] * count
    statuses, failures, result_counts = Counter(), Counter(), Counter()
    done = good = 0
    began, cpu_began = perf_counter(), process_time()

    async def worker():
        nonlocal done, good
        for index in remaining:
            start = perf_counter()
            status, error, size, request_id, success = None, '', 0, '', False
            try:
                response = await client.get(route)
                elapsed = (perf_counter() - start) * 1000
                status, size = response.status_code, len(response.content)
                request_id = response.headers.get('X-Request-ID', '')
                if status == 200:
                    try:
                        body = response.json()
                        success = valid(body, candidate)
                        if success:
                            result_counts[str(body['total'])] += 1
                        else:
                            error = 'InvalidResponseContract'
                    except ValueError:
                        error = 'InvalidJSON'
                else:
                    error = f'HTTP_{status}'
            except httpx.HTTPError as exc:
                elapsed = (perf_counter() - start) * 1000
                error = type(exc).__name__
            statuses[str(status) if status is not None else 'NO_RESPONSE'] += 1
            if error:
                failures[error] += 1
            good += int(success)
            samples[index] = {'request': index + 1, 'status': status, 'valid_success': success,
                              'latency_ms': elapsed, 'response_bytes': size,
                              'request_id': request_id, 'error': error}
            done += 1
            if progress and (done == count or done % max(100, count // 10) == 0):
                duration = perf_counter() - began
                print(json.dumps({'progress': f'{done}/{count}', 'elapsed_s': round(duration, 2),
                                  'completed_rps': round(done / duration, 2), 'errors': sum(failures.values())}), flush=True)

    await asyncio.gather(*(worker() for _ in range(min(count, concurrency))))
    duration, cpu = perf_counter() - began, process_time() - cpu_began
    summary = {'requests': count, 'concurrency': min(count, concurrency),
        'duration_s': round(duration, 6), 'successful': good, 'failed': count - good,
        'success_percent': round(100 * good / count, 3),
        'throughput_rps': round(count / duration, 3), 'successful_rps': round(good / duration, 3),
        'latency_ms_all': latency([s['latency_ms'] for s in samples]),
        'latency_ms_success': latency([s['latency_ms'] for s in samples if s['valid_success']]),
        'http_status_counts': dict(statuses), 'error_counts': dict(failures),
        'recommendation_total_counts': dict(result_counts),
        'response_bytes_total': sum(s['response_bytes'] for s in samples),
        'generator_cpu_s': round(cpu, 3), 'generator_cpu_one_core_percent': round(cpu / duration * 100, 2)}
    return summary, samples
