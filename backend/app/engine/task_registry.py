import time
import random
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("chronos.handlers")

class TaskExecutionError(Exception):
    pass

class TaskRegistry:
    handlers: Dict[str, Callable[[Dict[str, Any], int], Any]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(func: Callable[[Dict[str, Any], int], Any]):
            cls.handlers[name] = func
            return func
        return decorator

    @classmethod
    def execute(cls, handler_name: str, payload: Dict[str, Any], attempt: int = 1) -> Any:
        # Chaos & Failure Injection Gates
        if payload.get("inject_timeout"):
            time.sleep(payload.get("timeout_duration", 3.0))
            raise TaskExecutionError("Simulated Network Timeout (Gateway Timeout 504)")

        if payload.get("fail_until_attempt") and attempt <= payload.get("fail_until_attempt"):
            raise TaskExecutionError(f"Simulated Transient Failure on attempt {attempt} (Auto-healing on attempt {payload.get('fail_until_attempt')+1})")

        if payload.get("always_fail"):
            raise TaskExecutionError("Simulated Unrecoverable Fatal Failure -> Routed to DLQ")

        handler = cls.handlers.get(handler_name)
        if not handler:
            time.sleep(0.3)
            return {"status": "success", "handler": handler_name}

        return handler(payload, attempt)

# --- 1. E-COMMERCE WORKFLOW HANDLERS ---

@TaskRegistry.register("inventory_reserve")
def handle_inventory(payload: Dict[str, Any], attempt: int):
    sku = payload.get("sku", "SKU-PROD-882")
    qty = payload.get("qty", 1)
    time.sleep(0.35)
    return {"status": "RESERVED", "sku": sku, "quantity": qty, "lock_id": f"loc_{random.randint(1000, 9999)}"}

@TaskRegistry.register("payment_charge")
def handle_payment(payload: Dict[str, Any], attempt: int):
    amount = payload.get("amount", 249.00)
    time.sleep(0.5)
    return {"status": "CAPTURED", "amount": amount, "gateway": "Stripe", "charge_id": f"ch_{random.randint(100000, 999999)}"}

@TaskRegistry.register("fraud_check")
def handle_fraud(payload: Dict[str, Any], attempt: int):
    time.sleep(0.4)
    risk_score = round(random.uniform(0.01, 0.08), 3)
    return {"status": "PASSED", "fraud_score": risk_score, "decision": "APPROVE"}

@TaskRegistry.register("invoice_generate")
def handle_invoice(payload: Dict[str, Any], attempt: int):
    time.sleep(0.45)
    return {"status": "RENDERED", "invoice_no": f"INV-2026-{random.randint(10000, 99999)}", "pdf_bytes": 48291}

@TaskRegistry.register("email_dispatch")
def handle_email(payload: Dict[str, Any], attempt: int):
    time.sleep(0.25)
    return {"status": "SENT", "recipient": payload.get("email", "customer@example.com"), "provider": "Resend/SES"}


# --- 2. DATA ETL WORKFLOW HANDLERS ---

@TaskRegistry.register("data_extract")
def handle_extract(payload: Dict[str, Any], attempt: int):
    rows = payload.get("rows", 100000)
    time.sleep(0.4)
    return {"status": "EXTRACTED", "source": "PostgreSQL Replica", "raw_rows": rows}

@TaskRegistry.register("data_clean")
def handle_clean(payload: Dict[str, Any], attempt: int):
    time.sleep(0.5)
    return {"status": "CLEANED", "nulls_dropped": 14, "duplicates_removed": 3}

@TaskRegistry.register("data_transform")
def handle_transform(payload: Dict[str, Any], attempt: int):
    time.sleep(0.6)
    return {"status": "TRANSFORMED", "aggregation": "Hourly Revenue Metric", "columns": ["hour", "total_usd", "unique_users"]}

@TaskRegistry.register("data_load")
def handle_load(payload: Dict[str, Any], attempt: int):
    time.sleep(0.4)
    return {"status": "LOADED", "destination": "Snowflake / BigQuery", "partitions_written": 24}


# --- 3. MEDIA / AI PIPELINE HANDLERS ---

@TaskRegistry.register("image_download")
def handle_download(payload: Dict[str, Any], attempt: int):
    time.sleep(0.3)
    return {"status": "DOWNLOADED", "file_size_mb": 4.2, "source": "S3 Raw Bucket"}

@TaskRegistry.register("image_resize")
def handle_resize(payload: Dict[str, Any], attempt: int):
    time.sleep(0.4)
    return {"status": "RESIZED", "variants": ["thumbnail_150x150", "preview_720p", "hd_1080p"]}

@TaskRegistry.register("model_inference")
def handle_inference(payload: Dict[str, Any], attempt: int):
    time.sleep(0.7)
    return {"status": "PREDICTED", "model": "ResNet-50 / CLIP", "top_class": "sports_car", "confidence": 0.984}

@TaskRegistry.register("s3_upload")
def handle_upload(payload: Dict[str, Any], attempt: int):
    time.sleep(0.35)
    return {"status": "UPLOADED", "cdn_url": "https://cdn.chronos.internal/media/processed_8819.webp"}

@TaskRegistry.register("slack_notify")
def handle_notify(payload: Dict[str, Any], attempt: int):
    time.sleep(0.2)
    return {"status": "DELIVERED", "channel": "#ops-alerts", "response_code": 200}
