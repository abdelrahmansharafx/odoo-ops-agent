# Evaluation report

Generated 2026-10-22 20:33 · provider `gemini` · 21 questions

| Metric | Result |
|---|---|
| Tool-selection accuracy | 95% |
| Answer correctness | 95% |
| Latency p50 / p95 | 29.9s / 111.7s |
| Avg tokens per question (in + out) | 2081 + 56 |

## By category

| Category | n | Tool selection | Answer correct |
|---|---|---|---|
| data | 10 | 9/10 | 9/10 |
| process | 7 | 7/7 | 7/7 |
| multi | 4 | 4/4 | 4/4 |

## Per question

| ID | Tools called | Tools OK | Answer OK | Latency | Note |
|---|---|---|---|---|---|
| d01 | search_leads | ✅ | ✅ | 31.02s | expected 13 |
| d02 | search_leads | ✅ | ✅ | 37.19s | expected 13 |
| d03 | search_leads | ✅ | ✅ | 67.32s | expected 10 |
| d04 | get_pipeline_summary | ✅ | ✅ | 49.09s | expected 39 |
| d05 | get_pipeline_summary | ✅ | ✅ | 117.22s | expected 731044.0 |
| d06 | - | ❌ | ❌ | 0.0s | ERROR RemoteProtocolError: Server disconnected without sending a response. |
| d07 | search_sales_orders | ✅ | ✅ | 29.59s | expected 4 |
| d08 | search_sales_orders | ✅ | ✅ | 22.91s | expected 20321.11 |
| d09 | get_customer_profile | ✅ | ✅ | 89.24s | expected 'john.b@tech.info' |
| d10 | get_pipeline_summary | ✅ | ✅ | 86.94s | expected 'Mitchell Admin' |
| p01 | search_process_docs | ✅ | ✅ | 28.66s | The assistant correctly identified that the sales manager must approve refunds over 500 EUR, perfect |
| p02 | search_process_docs | ✅ | ✅ | 15.5s | The assistant accurately stated the refund period as 30 days from the invoice date, matching the ref |
| p03 | search_process_docs | ✅ | ✅ | 111.7s | The assistant correctly identifies that the sales manager approves a 15% discount, matching the refe |
| p04 | search_process_docs | ✅ | ✅ | 29.91s | The assistant correctly identifies all pipeline stages and defines Qualified in accordance with the  |
| p05 | search_process_docs | ✅ | ✅ | 108.6s | The assistant correctly identified the Enterprise team based on the criteria for companies with more |
| p06 | search_process_docs | ✅ | ✅ | 8.07s | The assistant correctly stated that quotations are valid for 30 days by default. |
| p07 | search_process_docs | ✅ | ✅ | 10.94s | The assistant accurately conveys that confirming the order moves the linked opportunity to the Won s |
| m01 | search_leads, search_process_docs | ✅ | ✅ | 11.67s | The assistant accurately stated both the number of leads in the Qualified stage and the default win  |
| m02 | search_sales_orders, search_process_docs | ✅ | ✅ | 9.95s | The assistant correctly identifies that there are 4 draft quotations and that a 25% discount require |
| m03 | get_pipeline_summary, search_process_docs | ✅ | ✅ | 11.17s | The assistant correctly identified the expected revenue in the New stage and the correct team for a  |
| m04 | get_customer_profile, search_process_docs | ✅ | ✅ | 48.31s | The assistant accurately provides both the number of sales orders and the exact refund window mentio |

_Tokens are agent usage only (judge calls excluded). Numbers: exact match (0.5 tolerance for currency sums). Text: LLM-as-judge._
