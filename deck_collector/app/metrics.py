from prometheus_client import Counter, Gauge, Histogram

METRICS_PORT = 9100

clash_api_requests_total = Counter(
    "deck_collector_clash_api_requests_total",
    "Requests made to the Clash Royale API",
    ["endpoint", "status"],
)

collection_run_duration_seconds = Histogram(
    "deck_collector_collection_run_duration_seconds",
    "Duration of a full deck-collection run",
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)

decks_collected = Gauge(
    "deck_collector_decks_collected",
    "Decks collected during the most recent run",
    ["type"],
)
