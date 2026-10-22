# Evaluation report

Generated 2026-10-22 18:18 · provider `gemini` · 21 questions

| Metric | Result |
|---|---|
| Tool-selection accuracy | 100% |
| Answer correctness | 100% |
| Latency p50 / p95 | 19.9s / 63.4s |
| Avg tokens per question (in + out) | 2212 + 60 |

## By category

| Category | n | Tool selection | Answer correct |
|---|---|---|---|
| data | 10 | 10/10 | 10/10 |
| process | 7 | 7/7 | 7/7 |
| multi | 4 | 4/4 | 4/4 |

## Per question

| ID | Tools called | Tools OK | Answer OK | Latency | Note |
|---|---|---|---|---|---|
| d01 | search_leads | ✅ | ✅ | 12.5s | expected 13 |
| d02 | search_leads | ✅ | ✅ | 12.26s | expected 13 |
| d03 | search_leads | ✅ | ✅ | 25.6s | expected 10 |
| d04 | get_pipeline_summary | ✅ | ✅ | 6.92s | expected 39 |
| d05 | get_pipeline_summary | ✅ | ✅ | 9.85s | expected 731044.0 |
| d06 | search_sales_orders | ✅ | ✅ | 111.12s | expected 15 |
| d07 | search_sales_orders | ✅ | ✅ | 9.43s | expected 4 |
| d08 | search_sales_orders | ✅ | ✅ | 63.37s | expected 20321.11 |
| d09 | get_customer_profile | ✅ | ✅ | 18.01s | expected 'john.b@tech.info' |
| d10 | get_pipeline_summary | ✅ | ✅ | 22.79s | expected 'Mitchell Admin' |
| p01 | search_process_docs | ✅ | ✅ | 7.58s | The assistant correctly identifies that the sales manager must approve refunds above 500 EUR. |
| p02 | search_process_docs | ✅ | ✅ | 19.62s | The assistant accurately stated the refund period as 30 days from the invoice date, matching the ref |
| p03 | search_process_docs | ✅ | ✅ | 12.87s | The assistant correctly identifies that a 15% discount requires approval from the sales manager, mat |
| p04 | search_process_docs | ✅ | ✅ | 26.99s | The assistant correctly identifies all pipeline stages and defines 'Qualified' in accordance with th |
| p05 | search_process_docs | ✅ | ✅ | 27.84s | The assistant correctly identified the Enterprise team and included the reasoning from the reference |
| p06 | search_process_docs | ✅ | ✅ | 18.63s | The assistant correctly stated that quotations are valid for 30 days by default. |
| p07 | search_process_docs | ✅ | ✅ | 58.96s | The assistant accurately states that confirming a sales order moves the linked opportunity to the Wo |
| m01 | search_leads, search_process_docs | ✅ | ✅ | 23.59s | The assistant correctly identified both the number of leads (13) and the default win probability (30 |
| m02 | search_sales_orders, search_process_docs | ✅ | ✅ | 25.09s | The assistant correctly identified the number of draft quotations and specified that the sales direc |
| m03 | get_pipeline_summary, search_process_docs | ✅ | ✅ | 19.93s | The assistant accurately provided the expected revenue for the New stage and correctly identified th |
| m04 | get_customer_profile, search_process_docs | ✅ | ✅ | 36.29s | The assistant accurately stated both the number of sales orders and the refund window from the refer |

_Tokens are agent usage only (judge calls excluded). Numbers: exact match (0.5 tolerance for currency sums). Text: LLM-as-judge._
