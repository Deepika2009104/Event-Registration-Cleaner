# AI Decision Journal

This journal documents the architectural and engineering rationale behind delegating specific responsibilities to **AI (LLM)** versus **Deterministic Code (Python)**, along with the essential role of **Human Review**.

---

## Decision Matrix

| Decision Area | Why AI Was Used | Why Python Was Used | Human Involvement |
| :--- | :--- | :--- | :--- |
| **1. Unstructured Text Parsing** | Student input entries have random formats (slashes, pipes, dashes, commas, conversational labels like *"ph:"* or *"mobile:"*). LLMs excel at natural language understanding and unstructured entity identification. | Python alone would require hundreds of fragile, easily broken regular expressions for every new delimiter pattern. | Evaluates edge cases where students input multiple people's names or unconventional notes. |
| **2. Data Cleaning & Digit Sanitization** | **Not used.** LLMs are non-deterministic and prone to "helpfully hallucinating" or modifying digits (e.g., turning 9 digits into 10). | Python code executes deterministic arithmetic, stripping symbols (`+`, `-`, spaces), enforcing exact digit counts, and verifying prefix rules (`[6-9]`). | No direct human intervention needed during cleaning; rules are clearly specified by policy. |
| **3. Email Format Validation** | **Not used.** LLMs might auto-correct an email typo (e.g. changing `gnail.com` to `gmail.com`), creating legal/privacy violations. | Python strictly checks string invariants: exactly one `@`, absence of spaces, and existence of a valid dot `.` in the domain. | When an email fails validation, humans look up college roll numbers or call the phone number to confirm the correct email. |
| **4. Academic Year & Branch Normalization** | AI extracts ambiguous vernacular (e.g., "final year", "sophomore", "III yr", "Computer Science"). | Python maps synonyms deterministically to integers `1..4` and approved branch codes (`CSE`, `IT`, `AIDS`, etc.), standardizing unknown branches to `'other'`. | Reviewers inspect `summary.txt` to see how many attendees were categorized into `'other'` and can add new official branches. |
| **5. Cross-Record Duplicate Detection** | **Not used.** LLMs cannot reliably maintain state across thousands of rows and hallucinate matches when given large context windows. | Python uses hash tables (`dict`/`set`) for instant \(O(1)\) lookup of cleaned phone numbers and emails across all processed rows. | Humans review flagged duplicate pairs in `problems.csv` to ensure siblings or teammates using one contact are handled appropriately. |
| **6. Contact Detail Correction** | **Strictly forbidden.** AI must never fabricate, guess, or synthesize contact information. | Python halts processing on defective records and logs them into `problems.csv`. | **Mandatory human touchpoint**: Organizers contact the attendee directly before manually updating records in the database. |

---

## Key Takeaway for Capstone Defense

> "Use Artificial Intelligence for **flexible interpretation and parsing of human messiness**, but use Deterministic Python for **strict validation, mathematical integrity, duplicate detection, and rule enforcement**."
