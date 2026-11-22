# Judgment Framework

This document outlines the collaborative system architecture between **Artificial Intelligence (LLM)**, **Deterministic Code (Python)**, and **Human Supervisors (Event Organizers)**.

## Overview Table

| Tool Component | What AI Does | What Python Does | What Could Go Wrong | Human Checkpoint |
| :--- | :--- | :--- | :--- | :--- |
| **1. Ingestion & Reading** | None. | Reads raw rows from CSV via `read_entry()` using UTF-8 handling and standard dictionary parsing. | Corrupted CSV formatting, unreadable encoding, or malformed quotes. | Organizer verifies that the incoming CSV file was exported properly from Google Forms/Sheets. |
| **2. Unstructured Extraction** | Parses free-text strings into JSON fields (`name`, `phone`, `email`, `year`, `branch`). Ignores conversational noise and weird delimiters. | Passes strict system prompts with few-shot exemplars; falls back to regex parser if API is down. | AI hallucination: LLM might guess missing digits or auto-complete broken emails. | Prompt constraints enforce zero-invention; `check_facts()` verifies extracted tokens against raw entry. |
| **3. Phone Number Processing** | Extracts raw phone substring as typed by the student. | Strips `+91`, `0`, spaces, and dashes; validates 10 digits; verifies starting digit in `[6, 7, 8, 9]`. | Student entered fewer than 10 digits or entered a landline number starting with 044. | Python marks record as `needs_fix`. Event team calls or checks identity card before manually updating. |
| **4. Email Processing** | Extracts email string. | Enforces lowercase, exactly one `@`, valid domain containing dot (`.`), and forbids whitespace. | Student made a typo like `user@gmaill` or omitted domain entirely (`meera@domain`). | Flagged in `problems.csv`. Team never auto-guesses the domain; they contact the attendee via alternate channels. |
| **5. Year & Branch Normalization** | Extracts year phrases ("3rd yr", "final year", "III") and branch text ("Computer Science"). | Maps recognized strings to integers `1..4` and branches to `['CSE', 'IT', 'AIDS', 'ECE', 'EEE', 'MECH', 'CIVIL', 'other']`. | Unknown branch names (e.g. "Biotechnology") or invalid academic years (e.g. 5th year). | Categorized into `other` or flagged as `needs_fix`. Team can review and re-assign branch category. |
| **6. Duplicate Detection** | None. (LLM cannot reliably compare cross-row state across large datasets). | Normalizes contact keys and queries hash maps (`seen_phones` and `seen_emails`) across all prior rows. | Legitimate multiple attendees sharing one phone number (e.g. siblings, lab coordinators). | Marked as `duplicate` in `problems.csv`. Never silently deleted; organizers decide which ticket to retain. |
| **7. Reporting & Audit Trail** | None. | Generates `clean_list.csv`, `problems.csv`, and `summary.txt` with transparent problem explanations. | File write failure, disk permission issues, or data truncation. | Organizers inspect `summary.txt` before sending confirmations or printing ID badges. |

---

## The Human Checkpoint Policy

> [!IMPORTANT]
> **Mandatory Rule for Event Organizers:**
> The event operations team **must directly contact participants whose registrations appear in `problems.csv`** before modifying, updating, or deleting any contact details. 
> 
> - **Never Auto-Correct Contact Info**: An automated tool must never guess an attendee's phone number or email domain. Even a single changed digit routes confidential ticket information to an unrelated stranger.
> - **Verification Before Confirmation**: If an entry has a status of `needs_fix`, an organizer reaches out via phone (if email is broken) or college portal ID to verify details.
> - **Fairness for Duplicate Submissions**: If a student submitted twice due to an internet glitch, the team verifies timestamps and keeps the most recent valid record while canceling the redundant duplicate.
