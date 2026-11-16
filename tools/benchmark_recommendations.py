"""Read-only benchmark: 300 and 10,000 requests, four clients, 50 in flight."""
import argparse
import asyncio
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import multiprocessing as mp
import os
from pathlib import Path
import subprocess
from time import perf_counter
from urllib.parse import quote

from dotenv import dotenv_values
import httpx

from benchmark_http import execute, latency

REPO = Path(__file__).resolve().parents[1]
CONCURRENCY = [13, 13, 12, 12]


async def run_client(index, count, concurrency, args, route, ready, start, results):
    key = os.environ.get('API_KEY', dotenv_values(REPO / '.env').get('API_KEY', ''))
    async with httpx.AsyncClient(
        base_url=args.base_url, headers={'X-API-Key': key} if key else {},
        limits=httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency,
                            keepalive_expiry=60),
        timeout=httpx.Timeout(30, connect=5, pool=5), trust_env=False,
    ) as client:
        warmup, _ = await execute(client, route, 25, concurrency, args.candidate)
        if warmup['failed']:
            raise RuntimeError(f'Warmup failed: {warmup}')
        ready.put(index)
        if not await asyncio.to_thread(start.wait, 120):
            raise TimeoutError('Other clients did not reach the start barrier')
        began = perf_counter()
        summary, samples = await execute(client, route, count // 4, concurrency, args.candidate)
        ended = perf_counter()
        target = args.output / f'raw-{count}-process-{index}.json'
        target.write_text(json.dumps({'summary': summary, 'samples': samples}), encoding='utf-8')
        results.put({'index': index, 'began': began, 'ended': ended, 'path': str(target)})


def child(index, count, concurrency, args, route, ready, start, results):
    try:
        asyncio.run(run_client(index, count, concurrency, args, route, ready, start, results))
    except Exception as exc:
        results.put({'index': index, 'error': type(exc).__name__ + ': ' + str(exc)})
        ready.put(index)


def main(args):
    # Refuse existing output so a later run cannot erase earlier evidence.
    args.output.mkdir(parents=True, exist_ok=False)
    route = '/api/v1/candidates/' + quote(args.candidate, safe='') + '/recommendations?limit=10&minScore=0'
    report = {
        'started_at_utc': datetime.now(timezone.utc).isoformat(), 'base_url': args.base_url,
        'client_processes': 4, 'total_concurrency': 50, 'concurrency_by_process': CONCURRENCY,
        'warmup_per_case_excluded': 100, 'endpoint': route, 'method': 'GET',
        'model': 'closed-loop, 4 independent HTTP clients, keep-alive, no retries',
        'api_revision': args.api_revision,
        'benchmark_git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
        'working_tree_dirty': bool(subprocess.check_output(
            ['git', 'status', '--porcelain'], cwd=REPO, text=True).strip()),
        'results': [],
    }
    context = mp.get_context('spawn')
    for count in [300, 10000]:
        print(json.dumps({'case': count, 'concurrency': 50, 'warming_up': 100}), flush=True)
        ready, results, start = context.Queue(), context.Queue(), context.Event()
        processes = [context.Process(target=child, args=(
            i, count, concurrency, args, route, ready, start, results,
        )) for i, concurrency in enumerate(CONCURRENCY)]
        try:
            for process in processes:
                process.start()
            for _ in processes:
                ready.get(timeout=120)
            start.set()
            messages = [results.get(timeout=180) for _ in processes]
            errors = [message for message in messages if 'error' in message]
            if errors:
                raise RuntimeError(str(errors))
            raw = [json.loads(Path(m['path']).read_text(encoding='utf-8')) for m in messages]
            samples = [sample for chunk in raw for sample in chunk['samples']]
            duration = max(m['ended'] for m in messages) - min(m['began'] for m in messages)
            good = sum(s['valid_success'] for s in samples)
            statuses, errors, totals = Counter(), Counter(), Counter()
            for chunk in raw:
                statuses.update(chunk['summary']['http_status_counts'])
                errors.update(chunk['summary']['error_counts'])
                totals.update(chunk['summary']['recommendation_total_counts'])
            summary = {
                'requests': count, 'concurrency': 50, 'client_processes': 4,
                'duration_s': round(duration, 6), 'successful': good, 'failed': count - good,
                'throughput_rps': round(count / duration, 3),
                'latency_ms_all': latency([s['latency_ms'] for s in samples]),
                'latency_ms_success': latency([s['latency_ms'] for s in samples if s['valid_success']]),
                'http_status_counts': dict(statuses), 'error_counts': dict(errors),
                'recommendation_total_counts': dict(totals),
                'unique_request_ids': len({s['request_id'] for s in samples if s['request_id']}),
                'generator_cpu_s_total': round(sum(c['summary']['generator_cpu_s'] for c in raw), 3),
                'generator_cpu_one_core_percent_by_process': [
                    c['summary']['generator_cpu_one_core_percent'] for c in raw],
            }
            report['results'].append(summary)
            with (args.output / f'latencias-{count}.csv').open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=list(samples[0]))
                writer.writeheader()
                writer.writerows(dict(sample, request=i) for i, sample in enumerate(samples, 1))
            (args.output / 'resultados.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(json.dumps({'finished_case': count, 'summary': summary}), flush=True)
        finally:
            start.set()
            for process in processes:
                if process.pid is not None:
                    process.join(timeout=5)
                    if process.is_alive():
                        process.terminate()
                        process.join()
    report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    (args.output / 'resultados.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return int(any(case['failed'] for case in report['results']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--candidate', default='c-202')
    parser.add_argument('--api-revision', help='Deployed API revision (explicit label, not autodetected)')
    parser.add_argument('--output', type=Path, required=True, help='New directory outside the repository')
    raise SystemExit(main(parser.parse_args()))
