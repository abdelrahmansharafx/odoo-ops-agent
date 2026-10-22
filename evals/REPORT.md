# Evaluation report

Generated 2026-10-22 17:10 · provider `gemini` · 21 questions

| Metric | Result |
|---|---|
| Tool-selection accuracy | 95% |
| Answer correctness | 95% |
| Latency p50 / p95 | 19.1s / 24.2s |
| Avg tokens per question (in + out) | 2192 + 54 |

## By category

| Category | n | Tool selection | Answer correct |
|---|---|---|---|
| data | 10 | 10/10 | 10/10 |
| process | 7 | 7/7 | 7/7 |
| multi | 4 | 3/4 | 3/4 |

## Per question

| ID | Tools called | Tools OK | Answer OK | Latency | Note |
|---|---|---|---|---|---|
| d01 | search_leads | ✅ | ✅ | 21.39s | expected 13 |
| d02 | search_leads | ✅ | ✅ | 17.97s | expected 13 |
| d03 | search_leads | ✅ | ✅ | 24.02s | expected 10 |
| d04 | get_pipeline_summary | ✅ | ✅ | 17.48s | expected 39 |
| d05 | get_pipeline_summary | ✅ | ✅ | 21.78s | expected 731044.0 |
| d06 | search_sales_orders | ✅ | ✅ | 24.2s | expected 15 |
| d07 | search_sales_orders | ✅ | ✅ | 22.25s | expected 4 |
| d08 | search_sales_orders | ✅ | ✅ | 20.6s | expected 20321.11 |
| d09 | get_customer_profile | ✅ | ✅ | 20.08s | expected 'john.b@tech.info' |
| d10 | get_pipeline_summary | ✅ | ✅ | 19.15s | expected 'Mitchell Admin' |
| p01 | search_process_docs | ✅ | ✅ | 79.07s | The assistant correctly identified that the sales manager must approve the refund and included the c |
| p02 | search_process_docs | ✅ | ✅ | 22.09s | The assistant correctly states the refund period as 30 days from the invoice date, matching the refe |
| p03 | search_process_docs | ✅ | ✅ | 21.18s | The assistant correctly identified that the sales manager approves a 15% discount, matching the refe |
| p04 | search_process_docs | ✅ | ✅ | 16.69s | The assistant correctly identifies all pipeline stages and provides the exact definition for 'Qualif |
| p05 | search_process_docs | ✅ | ✅ | 17.38s | The assistant correctly identified the Enterprise team and included the threshold of more than 250 e |
| p06 | search_process_docs | ✅ | ✅ | 15.89s | The assistant correctly stated that quotations are valid for 30 days by default. |
| p07 | search_process_docs | ✅ | ✅ | 17.05s | The assistant correctly states that the linked opportunity moves to the Won stage when a sales order |
| m01 | search_leads, search_process_docs | ✅ | ✅ | 15.71s | The assistant accurately states both the number of leads in the Qualified stage and their default wi |
| m02 | search_sales_orders, search_process_docs | ✅ | ✅ | 17.35s | The assistant correctly identified that there are 4 draft quotations and that a 25% discount require |
| m03 | get_pipeline_summary, search_process_docs | ✅ | ✅ | 16.18s | The assistant correctly identified both the expected revenue in the New stage and the correct team f |
| m04 | get_customer_profile, search_process_docs | ❌ | ❌ | 15.27s | The assistant stated there are 10 sales orders, whereas the reference answer states there are 13. |

_Tokens are agent usage only (judge calls excluded). Numbers: exact match (0.5 tolerance for currency sums). Text: LLM-as-judge._
