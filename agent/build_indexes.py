import asyncio
import json
import time
from pathlib import Path
from moss_agent import MossAgent, DocumentInfo
from agent.config import MOSS_PROJECT_ID, MOSS_PROJECT_KEY

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"

# Map 3 consolidated Moss indexes to their constituent knowledge files
INDEX_CONSOLIDATION = {
    "dispatch_emergency_ops": [
        KNOWLEDGE_DIR / "dispatch_sops.json",
        KNOWLEDGE_DIR / "logistics_fleet.json",
    ],
    "clinical_healthcare_triage": [
        KNOWLEDGE_DIR / "healthcare_triage.json",
    ],
    "enterprise_field_and_support": [
        KNOWLEDGE_DIR / "field_worker_loto.json",
        KNOWLEDGE_DIR / "customer_support_sla.json",
        KNOWLEDGE_DIR / "financial_compliance.json",
    ],
}

BENCHMARK_QUERIES = [
    ("dispatch_emergency_ops", "What is 10-50 and when is Code 3 emergency lights and sirens authorized?"),
    ("dispatch_emergency_ops", "What is the initial isolation distance for Chlorine gas in HAZMAT ERG?"),
    ("dispatch_emergency_ops", "What is the FMCSA 11-hour driving rule under Hours of Service?"),
    ("clinical_healthcare_triage", "Patient has crushing substernal chest pain and shortness of breath"),
    ("clinical_healthcare_triage", "What are the FAST screening steps for suspected acute stroke?"),
    ("clinical_healthcare_triage", "What is the intramuscular dose of epinephrine for adult anaphylaxis?"),
    ("enterprise_field_and_support", "What are the 6 mandatory steps for OSHA Lockout Tagout zero energy verification?"),
    ("enterprise_field_and_support", "What does Caterpillar fault SPN 100 low engine oil pressure require?"),
    ("enterprise_field_and_support", "What is the initial response SLA for a P0 critical enterprise outage?"),
    ("enterprise_field_and_support", "When must a bank file a Currency Transaction Report under BSA?"),
]

async def build_and_benchmark():
    print(f"Connecting to Moss Context Engine...")
    print(f"Project ID: {MOSS_PROJECT_ID}")
    
    agent = MossAgent(
        project_id=MOSS_PROJECT_ID,
        project_key=MOSS_PROJECT_KEY,
    )

    # 1. Clean up old indexes
    existing_indexes = await agent.list_indexes()
    existing_names = [idx.name if hasattr(idx, 'name') else str(idx) for idx in existing_indexes]
    print(f"Current indexes in Moss: {existing_names}")

    target_index_names = list(INDEX_CONSOLIDATION.keys())

    for old_name in existing_names:
        if old_name not in target_index_names:
            print(f"Deleting outdated index '{old_name}'...")
            try:
                await agent.delete_index(old_name)
                print(f"Deleted '{old_name}'")
            except Exception as e:
                print(f"Delete warning for {old_name}: {e}")

    # 2. Build consolidated indexes
    for index_name, files in INDEX_CONSOLIDATION.items():
        all_docs = []
        for file_path in files:
            if not file_path.exists():
                print(f"Warning: file {file_path} not found")
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
            for item in raw_items:
                doc_text = f"[{item.get('vertical','').upper()} | {item.get('category','').upper()}] {item['title']}\n{item['text']}"
                all_docs.append(DocumentInfo(id=item["id"], text=doc_text))

        # Check if already present
        if index_name in existing_names:
            print(f"Index '{index_name}' exists. Recreating to refresh documents ({len(all_docs)} docs)...")
            try:
                await agent.delete_index(index_name)
            except Exception as e:
                pass

        print(f"Creating '{index_name}' with {len(all_docs)} rich documents...")
        mutation = await agent.create_index(index_name, all_docs)
        print(f"Created '{index_name}' successfully: {mutation}")

    # 3. Prewarm all indexes into process memory
    print(f"\nPrewarming all {len(target_index_names)} indexes into local cache...")
    t_start = time.perf_counter()
    await agent.load_indexes(target_index_names)
    t_load_ms = (time.perf_counter() - t_start) * 1000
    print(f"All indexes loaded and hot in {t_load_ms:.2f} ms")

    # 4. Latency benchmark across all 6 verticals
    print("\n" + "=" * 70)
    print("MOSS SUB-10MS CONTEXT RETRIEVAL BENCHMARK — ALL VERTICALS")
    print("=" * 70)

    durations = []
    for idx_name, q in BENCHMARK_QUERIES:
        # Warmup query
        await agent.query(idx_name, q)
        
        # Benchmark 5 runs
        runs = []
        res = None
        for _ in range(5):
            t0 = time.perf_counter()
            res = await agent.query(idx_name, q)
            runs.append((time.perf_counter() - t0) * 1000)
            
        avg_ms = sum(runs) / len(runs)
        min_ms = min(runs)
        durations.append(avg_ms)
        top_doc = res.docs[0].id if res and res.docs else "N/A"
        moss_internal = getattr(res, "time_taken_ms", "N/A")
        
        print(f"Index: {idx_name:<30}")
        print(f"Query: '{q[:45]}...'")
        print(f"  -> Min: {min_ms:.2f}ms | Avg: {avg_ms:.2f}ms | Moss Time: {moss_internal}ms | Top Doc: {top_doc}")
        print("-" * 70)

    overall_p50 = sorted(durations)[len(durations) // 2]
    overall_avg = sum(durations) / len(durations)
    print(f"\nBenchmark Summary across {len(BENCHMARK_QUERIES)} queries:")
    print(f"  Average Retrieval Time : {overall_avg:.2f} ms")
    print(f"  Median (P50)           : {overall_p50:.2f} ms")
    print(f"  Sub-10ms Verified      : {'YES (<10ms)' if overall_avg < 10.0 else 'CHECK CACHE'}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(build_and_benchmark())
