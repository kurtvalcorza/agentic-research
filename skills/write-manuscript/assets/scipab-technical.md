---
marp: true
theme: technical
paginate: true
header: '**[Conference/Meetup Name]** | [Date]'
footer: '[Your Name/Handle] | [@yourhandle]'
style: |
  section {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Fira Code', 'Courier New', monospace;
    font-size: 24px;
  }
  h1 {
    color: #4ec9b0;
    font-size: 2.5em;
    font-weight: 700;
    border-bottom: 3px solid #569cd6;
    padding-bottom: 0.3em;
  }
  h2 {
    color: #569cd6;
    font-size: 2em;
    font-weight: 600;
  }
  h3 {
    color: #9cdcfe;
    font-size: 1.6em;
    font-weight: 500;
  }
  strong {
    color: #dcdcaa;
  }
  em {
    color: #ce9178;
  }
  code {
    background: #2d2d2d;
    padding: 0.2em 0.5em;
    border-radius: 4px;
    color: #ce9178;
    font-family: 'Fira Code', monospace;
  }
  pre {
    background: #2d2d2d;
    border-left: 4px solid #569cd6;
    padding: 1em;
    border-radius: 6px;
    overflow-x: auto;
  }
  pre code {
    background: transparent;
    padding: 0;
    color: #d4d4d4;
  }
  ul, ol {
    line-height: 1.8;
  }
  ul li:before {
    content: "›";
    color: #4ec9b0;
    font-weight: bold;
    display: inline-block;
    width: 1em;
    margin-left: -1em;
  }
  table {
    font-size: 0.85em;
    border-collapse: collapse;
    width: 100%;
  }
  th {
    background: #264f78;
    color: #ffffff;
    padding: 0.6em;
    text-align: left;
  }
  td {
    padding: 0.6em;
    border-bottom: 1px solid #3e3e42;
  }
  .metric {
    font-size: 2.5em;
    font-weight: 700;
    color: #4ec9b0;
  }
  .warning {
    font-size: 2.5em;
    font-weight: 700;
    color: #f48771;
  }
  section.complication {
    background: linear-gradient(135deg, #3e1f47 0%, #6a2c6e 100%);
    color: #f48771;
  }
  section.complication h1, section.complication h2 {
    color: #f48771;
    border-bottom-color: #f48771;
  }
  section.implication {
    background: #252526;
    color: #d4d4d4;
    font-size: 1.4em;
    border: 4px solid #f48771;
    padding: 2.5em;
  }
  section.implication h1 {
    color: #f48771;
    font-size: 2.8em;
  }
  section.benefit {
    background: linear-gradient(135deg, #0e639c 0%, #1177bb 100%);
    color: #ffffff;
  }
  section.benefit h1, section.benefit h2 {
    color: #4ec9b0;
    border-bottom-color: #4ec9b0;
  }
  section.architecture {
    background: #1e1e1e;
    border-left: 8px solid #569cd6;
    padding-left: 2em;
  }
  .callout {
    background: #2d2d2d;
    border-left: 4px solid #dcdcaa;
    padding: 1em 1.5em;
    margin: 1em 0;
  }
  .callout-warning {
    background: #2d2d2d;
    border-left: 4px solid #f48771;
    padding: 1em 1.5em;
    margin: 1em 0;
  }
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: "" -->
<!-- _footer: "" -->

# [Technical Topic/System Name]
## [Architecture/Deep Dive]

**[Your Name]**
*[Role/Title] @ [Company/Project]*

[Event Name] | [Date]

**Repo:** `github.com/[org]/[repo]`

---

<!-- _class: situation -->

# Situation: The Technical Landscape

**Current state of [system/problem domain]:**

```python
# Typical current approach
def process_request(data):
    # Monolithic, tightly-coupled
    result = legacy_system.process(data)
    return result
```

**What's standard:**
- [Technology/pattern 1 in use]
- [Technology/pattern 2 in use]
- [Common assumptions/constraints]

**Stack:** [Language] | [Framework] | [Database] | [Infra]

---

<!-- _class: situation -->

## Situation: System Context

**Architecture (current):**

```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│  Monolithic Application     │
│  ┌──────────────────────┐   │
│  │  Business Logic      │   │
│  │  Data Access         │   │
│  │  External APIs       │   │
│  └──────────────────────┘   │
└──────┬──────────────────────┘
       │
┌──────▼──────┐
│  Database   │
└─────────────┘
```

**Constraints:** [Technical debt, performance, scalability]

---

<!-- _class: complication -->

# Complication: The Problem

## [One-sentence technical problem description]

**Evidence of the issue:**

<div class="metric">3.2s</div>

**p95 latency** (SLA is 500ms)

<div class="metric">47%</div>

**error rate** under load (10K req/s)

<div class="metric">0</div>

**horizontal scalability** (single instance)

---

<!-- _class: complication -->

## Complication: Root Cause Analysis

**Bottlenecks identified:**

1. **Database N+1 queries**
   ```sql
   -- Executed 1000+ times per request
   SELECT * FROM users WHERE id = ?;
   ```

2. **Synchronous external API calls**
   - Blocking I/O (500ms avg per call)
   - No timeout/retry logic

3. **In-memory state management**
   - Session data in app memory (not distributed)
   - Instance restart = data loss

**Profiling:** `py-spy` flamegraph → 82% time in database calls

---

<!-- _class: implication -->

# Implication: What Breaks

## If we don't fix this within 6 months:

<div class="warning">System outages</div>

**weekly** (vs. monthly now)

<div class="warning">Data loss</div>

**guaranteed** on every deployment

<div class="warning">0 scalability</div>

**can't handle 2x load**

---

<!-- _class: implication -->

## Implication: Cascading Failures

**Failure scenarios:**

| Scenario | Trigger | Impact |
|----------|---------|--------|
| Database overload | >5K req/s | 100% error rate |
| Instance crash | OOM (8GB limit) | 5-min downtime |
| API timeout | External service slow | Request queue fills |
| Data corruption | Concurrent writes | Manual recovery (hours) |

**Real incident:** Nov 2025 outage (3 hours, $45K revenue loss)

**Extrapolated:** 12 incidents/year = $540K loss + reputation damage

---

<!-- _class: architecture -->

# Position: The Solution Architecture

## [System/approach name in 5 words]

**Core thesis:** [One sentence describing your architectural approach]

```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│   API Gateway (Nginx)       │
└──────┬──────────────────────┘
       │
    ┌──▼──────────┐
    │  Load Bal   │
    └──┬─────┬────┘
       │     │
┌──────▼─┐ ┌▼────────┐
│  App 1 │ │  App N  │  ← Stateless, horizontally scalable
└──┬───┬─┘ └─┬───┬───┘
   │   │     │   │
   │   └─────┴───┘
   │       │
┌──▼───────▼──┐ ┌─────────┐
│   Redis     │ │  Queue  │
│  (cache)    │ │ (async) │
└─────────────┘ └────┬────┘
                     │
              ┌──────▼──────┐
              │   Workers   │
              └─────────────┘
```

---

<!-- _class: architecture -->

## Position: Key Design Decisions

**Three core changes:**

### 1. Database Query Optimization

**Before:**
```python
# N+1 queries (1000+ DB roundtrips)
for user in users:
    profile = db.query("SELECT * FROM profiles WHERE user_id = ?", user.id)
```

**After:**
```python
# Single query with JOIN (1 DB roundtrip)
results = db.query("""
    SELECT u.*, p.*
    FROM users u
    LEFT JOIN profiles p ON u.id = p.user_id
""")
```

**Impact:** 3.2s → 180ms (94% reduction)

---

<!-- _class: architecture -->

## Position: Design Decision 2

### 2. Async I/O for External APIs

**Before (blocking):**
```python
# 500ms per call, synchronous
result1 = api1.call()  # 500ms
result2 = api2.call()  # 500ms
result3 = api3.call()  # 500ms
# Total: 1500ms
```

**After (async):**
```python
# 500ms total, parallel
import asyncio

results = await asyncio.gather(
    api1.call(),
    api2.call(),
    api3.call()
)
# Total: 500ms (3x speedup)
```

**Impact:** 1500ms → 500ms (67% reduction)

---

<!-- _class: architecture -->

## Position: Design Decision 3

### 3. Distributed State with Redis

**Before (in-memory):**
```python
# Session data in app memory
sessions = {}  # Lost on restart, not shared across instances
```

**After (Redis):**
```python
# Session data in Redis (distributed, persistent)
import redis
r = redis.Redis(host='redis', port=6379)

def save_session(user_id, data):
    r.setex(f"session:{user_id}", 3600, json.dumps(data))

def get_session(user_id):
    return json.loads(r.get(f"session:{user_id}"))
```

**Impact:** Zero data loss on deployment, horizontal scalability enabled

---

<!-- _class: performance -->

## Position: Performance Benchmarks

**Load testing results (10K req/s):**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| p50 latency | 1.2s | 120ms | **90%** |
| p95 latency | 3.2s | 280ms | **91%** |
| p99 latency | 5.8s | 450ms | **92%** |
| Error rate | 47% | 0.3% | **99.4%** |
| Throughput | 2K req/s | 15K req/s | **7.5x** |

**Test environment:** AWS EC2 (4x c5.2xlarge instances)

**Tool:** `locust` with realistic user scenarios

---

<!-- _class: action -->

# Action: Migration Plan

## Phase 1: Database Optimization (Week 1-2)

**Tasks:**
1. Identify N+1 queries (use Django Debug Toolbar)
2. Add `select_related()`/`prefetch_related()` to ORM calls
3. Create composite indexes for frequent queries
4. Benchmark before/after (target: <500ms p95)

**Owner:** Backend team
**Risk:** Low (read optimization only)
**Rollback:** Remove new indexes if performance degrades

---

<!-- _class: action -->

## Action: Phase 2 & 3

### Phase 2: Async API Calls (Week 3-4)

**Tasks:**
1. Refactor API client to use `httpx` (async HTTP)
2. Update views to `async def` (Django 4.1+ async views)
3. Add timeout/retry logic (`tenacity` library)
4. Deploy to staging, load test

**Owner:** Backend + DevOps
**Risk:** Medium (requires async expertise)
**Rollback:** Feature flag (`FF_ASYNC_API=false`)

### Phase 3: Redis Integration (Week 5-6)

**Tasks:**
1. Provision Redis cluster (AWS ElastiCache)
2. Migrate session backend (`django-redis`)
3. Implement cache-aside pattern for hot data
4. Blue-green deployment (gradual rollout)

---

<!-- _class: benefit -->

# Benefit: The Future State

## After migration:

<div class="metric">15K req/s</div>

**throughput** (7.5x improvement)

<div class="metric">280ms</div>

**p95 latency** (91% reduction)

<div class="metric">∞</div>

**horizontal scalability** (stateless)

---

<!-- _class: benefit -->

## Benefit: Business Impact

**Operational improvements:**

Cost reduction
- $12K/month fewer EC2 instances (2 → 6, but smaller)

Reliability
- 99.9% uptime (vs. 95% current)

Developer velocity
- 2-hour deploys → 15 minutes (zero-downtime)

User experience
- 3.2s page loads → 280ms (user retention +18%)

**ROI:** Break-even in 3 months (dev time vs. cost savings)

---

<!-- _class: technical-details -->

## Technical Details: Stack Changes

**Additions:**

| Component | Technology | Purpose |
|-----------|------------|---------|
| Cache | Redis 7.0 | Session + hot data |
| Queue | Celery + RabbitMQ | Async tasks |
| Monitoring | Prometheus + Grafana | Metrics + alerting |
| Tracing | OpenTelemetry | Distributed tracing |

**Removals:**
- In-memory session storage (replaced by Redis)
- Synchronous task execution (replaced by Celery)

**Unchanged:**
- PostgreSQL 14 (database)
- Django 4.2 (framework)
- Nginx (reverse proxy)

---

<!-- _class: security -->

## Security Considerations

**Attack surface changes:**

<div class="callout-warning">

**New risks:**
- Redis exposed to network (mitigation: VPC + auth)
- Async code complexity (mitigation: code review + fuzzing)
- Distributed state race conditions (mitigation: Redis transactions)

</div>

<div class="callout">

**Risk mitigation:**
- Redis: TLS encryption, `requirepass`, network isolation
- Async: `semaphore` for concurrency limits, `asyncio.timeout()`
- Race conditions: Redis `WATCH`/`MULTI`/`EXEC` (optimistic locking)

</div>

**Penetration testing:** Scheduled for Week 5 (before prod deployment)

---

<!-- _class: observability -->

## Observability Strategy

**Metrics to track:**

```python
# Key SLIs (Service Level Indicators)
request_latency_seconds = Histogram('http_request_duration_seconds',
                                     'Request latency', ['method', 'endpoint'])
request_count = Counter('http_requests_total',
                        'Total requests', ['method', 'status'])
active_connections = Gauge('active_connections',
                           'Active Redis connections')
```

**Alerts:**
- p95 latency > 500ms (page SRE)
- Error rate > 1% (page on-call)
- Redis connection pool exhausted (warning)

**Dashboards:** Grafana (request rate, latency heatmaps, error breakdown)

---

<!-- _class: lessons-learned -->

# Lessons Learned

**What worked:**
✓ Incremental migration (phased approach reduced risk)
✓ Feature flags (fast rollback on issues)
✓ Load testing early (caught issues before prod)

**What didn't:**
✗ Underestimated async complexity (2-week delay)
✗ Redis memory sizing (initial 2GB → 8GB needed)
✗ Missing distributed tracing (hard to debug cross-service issues)

**If doing again:**
- Start with distributed tracing (OpenTelemetry) from Day 1
- Hire async Python expert (contract basis)
- Over-provision Redis memory (2x estimated size)

---

<!-- _class: next-steps -->

# Next Steps

**For adoption in your system:**

1. **Profile first** (don't optimize blindly)
   - Use `py-spy`, `django-silk`, or `cProfile`
   - Identify your actual bottlenecks

2. **Start small** (database optimization is low-risk)
   - Fix N+1 queries first (biggest bang for buck)
   - Measure before/after

3. **Async is hard** (only if needed)
   - Don't go async unless blocking I/O is your bottleneck
   - Consider `gevent` as intermediate step

**Questions?** DM me: [@yourhandle] or [your.email@example.com]

---

<!-- _class: references -->
<!-- _paginate: false -->

# References & Resources

**Code:**
- GitHub: `github.com/[org]/[repo]`
- Architecture Decision Records: `github.com/[org]/[repo]/docs/adr/`

**Tools:**
- `py-spy`: github.com/benfred/py-spy (profiling)
- `locust`: locust.io (load testing)
- `django-silk`: github.com/jazzband/django-silk (query profiling)

**Reading:**
- "Designing Data-Intensive Applications" (Kleppmann)
- "Python Concurrency with asyncio" (Hattingh)
- AWS Well-Architected Framework (Performance Efficiency)

---

<!-- _class: backup -->
<!-- _paginate: false -->

# Backup Slides

*Deep dives and additional technical details*

---

## Backup: Redis Cluster Configuration

```yaml
# redis.conf (production settings)
maxmemory 8gb
maxmemory-policy allkeys-lru  # Evict least-recently-used keys
appendonly yes                 # Persistence (AOF)
appendfsync everysec           # Fsync every second (balance durability/performance)

# Security
requirepass [strong-password]
protected-mode yes
bind 10.0.1.0/24               # VPC subnet only

# Replication (1 master, 2 replicas)
replicaof redis-master 6379
replica-read-only yes
```

**Topology:** 1 master (writes) + 2 replicas (reads)
**Failover:** Redis Sentinel (automatic promotion)

---

## Backup: Database Index Strategy

**Added indexes (PostgreSQL):**

```sql
-- Composite index for frequent JOIN
CREATE INDEX idx_user_profile_lookup
ON profiles(user_id, status)
WHERE status = 'active';

-- Partial index for recent data
CREATE INDEX idx_recent_orders
ON orders(created_at DESC)
WHERE created_at > NOW() - INTERVAL '30 days';

-- Covering index (index-only scan)
CREATE INDEX idx_user_email_name
ON users(email, first_name, last_name);
```

**Monitoring:** `pg_stat_user_indexes` (unused indexes removed quarterly)

---

## Backup: Async API Client Implementation

```python
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class AsyncAPIClient:
    def __init__(self, base_url, timeout=5.0):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=httpx.Limits(max_connections=100)
        )

    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=1, max=10))
    async def call_api(self, endpoint, **kwargs):
        response = await self.client.get(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    async def call_multiple(self, endpoints):
        tasks = [self.call_api(ep) for ep in endpoints]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

---

<!--
SPEAKER NOTES TEMPLATE

Title Slide:
- Opening: "Hi, I'm [name]. Today I'll walk through how we scaled [system] from 2K to 15K req/s."
- Context: "This is a post-mortem + architecture deep-dive."
- Transition: "Let's start with where we were 6 months ago."

Situation Slide:
- Demo: Show the monolithic code (if live coding is allowed)
- Emphasize: "This is a common pattern—not criticizing the original design."
- Transition: "But as we scaled, problems emerged."

Complication Slide:
- Show flamegraph: "82% of time in database—that's our bottleneck."
- Real incident: "November outage cost us $45K and customer trust."
- Transition: "So what happens if we do nothing?"

Implication Slide:
- Pause after each failure scenario (let it sink in)
- Personal angle: "We were on call every weekend—unsustainable."
- Transition: "Here's how we solved it."

Position Slide:
- Code walkthrough: "Let me show you the actual diffs."
- Benchmarks: "These are real numbers from our staging environment."
- Transition: "And here's how you can adopt this."

Action Slide:
- Practical: "This is the exact migration plan we used."
- Risk management: "We had rollback plans for every phase."
- Transition: "And here's what we got out of it."

Benefit Slide:
- Celebrate: "15K req/s, 280ms p95—we're proud of this."
- Business impact: "This paid for itself in 3 months."
- Closing: "Questions? Let's chat after."
-->
