# Cost and Latency Analysis

This document provides a realistic breakdown of performance latency, API overhead, financial cost, and graceful degradation strategies for the **Event Registration Cleaner**.

---

## 1. API Call Requirements (20 Registrations)

- **Total Registrations**: 20 to 22 entries.
- **Number of API Calls Required**: Exactly **1 call per registration row** (sequential extraction) = **20 to 22 API calls**.
- **Alternative Batching Mode**: If grouped in batches of 10, this can be reduced to **2 API calls total**, though single-record processing offers maximum isolation against token overflow.

---

## 2. Latency Analysis

| Metric | Individual Call | Total (20 Records Sequential) | Total (Batched / Async) |
| :--- | :--- | :--- | :--- |
| **Network Round-Trip Time (RTT)** | ~150 ms – 300 ms | ~3 – 6 seconds | ~300 ms |
| **Model Inference & JSON Generation** | ~350 ms – 700 ms | ~7 – 14 seconds | ~1.5 seconds |
| **Total Latency per Call** | **~500 ms – 1.0 second** | **~10 – 20 seconds total** | **~2 seconds total** |

*Note: Latency varies based on network geography, internet bandwidth, and server load on the model provider.*

---

## 3. Estimated API Cost

> [!NOTE]
> *Disclaimer: API token prices are subject to provider changes and model choices. Below are typical enterprise estimates based on current pricing models (e.g., Google Gemini 1.5 Flash / OpenAI GPT-4o-mini).*

### Token Breakdown per Request:
- **System Prompt + Instructions**: ~250 input tokens
- **User Entry Text**: ~40 input tokens
- **Generated JSON Output**: ~50 output tokens
- **Total per registration**: ~290 input tokens + ~50 output tokens

### Cost Estimation Table (Assuming Gemini 1.5 Flash rates: ~$0.075 / 1M input tokens, ~$0.30 / 1M output tokens):
- **Cost for 20 Registrations**:
  - Input tokens: \(20 \times 290 = 5,800\) tokens \(\approx \$0.000435\)
  - Output tokens: \(20 \times 50 = 1,000\) tokens \(\approx \$0.000300\)
  - **Estimated Total Cost for 20 Records**: **Under \$0.001 (less than a tenth of one US cent)**
- **Cost for 10,000 Registrations (College Fest Scale)**:
  - Estimated total cost: **Approximately \$0.35 to \$0.75 USD** (Extremely economical).

---

## 4. How Cost and Latency Can Be Reduced

1. **Batching Requests**:
   - Instead of sending 20 single queries, combine 10 or 20 entries into a single prompt asking for a JSON array. This cuts down repetitive system prompt tokens by over 80%.
2. **Caching System Prompt**:
   - Modern LLMs offer context caching for system instructions, reducing input token charges on recurring headers.
3. **Local Hybrid Pre-Filter**:
   - Run simple regex locally first. If an entry is already well-formatted CSV (`Priya K, 9840012345, priya.k@gmail.com, 2, CSE`), skip the LLM entirely and invoke zero API calls. Only route ambiguous, chaotic text to the LLM.
4. **Use Lightweight Models**:
   - Employ fast, distilled models (e.g. Gemini 1.5 Flash, GPT-4o-mini) rather than expensive frontier models (GPT-4o or Gemini 1.5 Pro).

---

## 5. What Happens If the API Is Unavailable?

Our application is built with a **Zero-Downtime Fallback Architecture**:

1. **Missing Key Detection**:
   - If `.env` is absent or the key is set to a placeholder, the system gracefully bypasses the network call without crashing or throwing unhandled tracebacks.
2. **Network Timeout & Error Catching**:
   - All network calls are wrapped in `try-except` blocks with a 10-second timeout. If the provider experiences HTTP 429 (rate limit), HTTP 500 (server outage), or local internet loss, the error is safely intercepted.
3. **Deterministic Fallback Extractor (`fallback_extractor`)**:
   - The program seamlessly switches to an internal rule-based regex parser that extracts email addresses, phone digits, and academic keywords.
   - The college presentation can run **100% offline without an active internet connection** while demonstrating identical data cleaning and reporting workflows.
