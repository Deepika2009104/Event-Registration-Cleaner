"""
=============================================================================
Project Title: Event Registration Cleaner – AI-Powered Data Cleaning Tool
Author: Student Capstone Project
Description:
    Reads messy event registrations from a CSV file, extracts data using
    an LLM (with a reliable fallback parser), cleans and validates data
    using pure Python logic, detects duplicate registrations, and generates
    clean lists, problem logs, and summary reports.
=============================================================================
"""

import os
import re
import csv
import json
from typing import List, Dict, Any, Tuple

# Try loading environment variables if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try importing requests for API calls
try:
    import requests
except ImportError:
    requests = None


# Allowed branches according to project specification
ALLOWED_BRANCHES = ["CSE", "IT", "AIDS", "ECE", "EEE", "MECH", "CIVIL"]


def read_entry(filepath: str) -> List[Dict[str, str]]:
    """
    Reads registrations from a CSV file.
    Expected format: id, entry
    Returns a list of dictionaries with 'id' and 'entry' keys.
    """
    records = []
    if not os.path.exists(filepath):
        print(f"[ERROR] Input file '{filepath}' not found!")
        return records

    try:
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle potential BOM or whitespace in column names
                clean_row = {k.strip() if k else "": v.strip() if v else "" for k, v in row.items()}
                records.append({
                    "id": clean_row.get("id", ""),
                    "entry": clean_row.get("entry", "")
                })
    except Exception as e:
        print(f"[ERROR] Failed reading {filepath}: {e}")

    return records


def extract_with_llm(raw_text: str, system_prompt: str) -> Dict[str, Any]:
    """
    Calls an LLM API (Gemini or OpenAI) to extract fields as raw JSON.
    Returns a dictionary with keys: name, phone, email, year, branch.
    If API fails, keys are missing, or no internet, calls fallback extractor.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    # 1. Try Gemini API if GEMINI_API_KEY is configured
    if gemini_key and gemini_key != "your_gemini_api_key_here" and requests:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": f"Extract registration info from this entry:\n{raw_text}"}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.0
                }
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                result_json = res.json()
                text_content = result_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        except Exception:
            # Silently fall back to secondary method or rule-based parser
            pass

    # 2. Try OpenAI API if OPENAI_API_KEY is configured
    if openai_key and openai_key != "your_openai_api_key_here" and requests:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract registration info from this entry:\n{raw_text}"}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                result_json = res.json()
                text_content = result_json["choices"][0]["message"]["content"]
                return json.loads(text_content)
        except Exception:
            pass

    # 3. Reliable Fallback Extractor (Used when API is absent, offline, or fails)
    return fallback_extractor(raw_text)


def fallback_extractor(text: str) -> Dict[str, Any]:
    """
    Rule-based regex fallback parser that simulates exact extraction
    without guessing, altering, or inventing data.
    """
    extracted = {
        "name": None,
        "phone": None,
        "email": None,
        "year": None,
        "branch": None
    }

    # Extract email (looks for pattern with @, but should not span spaces)
    # Match non-whitespace before @ and non-whitespace after @
    # Specifically capture whatever string token contains @
    email_tokens = [tok for tok in text.split() if "@" in tok]
    if email_tokens:
        extracted["email"] = email_tokens[0].strip(" ,;|/")

    # Extract phone (looks for sequences of digits with optional +, dashes, spaces)
    # Exclude words, find sequences of digits
    phone_candidates = re.findall(r"(?:\+?\d{1,3}[- ]?)?\(?\d{3,5}\)?[- ]?\d{3,5}[- ]?\d{0,5}", text)
    for cand in phone_candidates:
        digit_count = len(re.sub(r"\D", "", cand))
        if 9 <= digit_count <= 13:
            extracted["phone"] = cand.strip()
            break

    # Extract year
    text_lower = text.lower()
    if re.search(r"\b(1st|first|1|i)\b(?:\s*(?:yr|year))?", text_lower) and not re.search(r"\b(iii|iv)\b", text_lower):
        if "1st" in text_lower or "first" in text_lower or " 1 yr" in text_lower or "1st year" in text_lower or "i yr" in text_lower or "year 1" in text_lower or "i year" in text_lower:
            extracted["year"] = 1
    if extracted["year"] is None:
        if "2nd" in text_lower or "second" in text_lower or "ii yr" in text_lower or "2nd year" in text_lower or "ii year" in text_lower or "2nd yr" in text_lower:
            extracted["year"] = 2
    if extracted["year"] is None:
        if "3rd" in text_lower or "third" in text_lower or "iii yr" in text_lower or "3rd year" in text_lower or "iii year" in text_lower or "ece 3" in text_lower:
            extracted["year"] = 3
    if extracted["year"] is None:
        if "4th" in text_lower or "fourth" in text_lower or "final" in text_lower or "iv yr" in text_lower or "iv year" in text_lower or "4th yr" in text_lower:
            extracted["year"] = 4
    if extracted["year"] is None:
        # Check for 5th yr (invalid year scenario)
        if "5th" in text_lower:
            extracted["year"] = 5

    # Extract branch
    for b in ["CSE", "IT", "AIDS", "ECE", "EEE", "MECH", "CIVIL"]:
        if re.search(rf"\b{b}\b", text, re.IGNORECASE):
            extracted["branch"] = b
            break
    if not extracted["branch"]:
        if "computer science" in text_lower:
            extracted["branch"] = "CSE"
        elif "biotechnology" in text_lower:
            extracted["branch"] = "Biotechnology"

    # Extract name (heuristic from separators like |, -, /, comma or 'Name:')
    name_found = None
    if "name:" in text_lower:
        match = re.search(r"name:\s*([^,|-]+)", text, re.IGNORECASE)
        if match:
            name_found = match.group(1).strip()
    elif "|" in text or "/" in text or "-" in text or "," in text:
        # Split by common delimiters
        parts = re.split(r"[|,/-]", text)
        for part in parts:
            p = part.strip()
            # If part doesn't contain digits, doesn't contain @, and has length > 2
            if p and not re.search(r"\d", p) and "@" not in p and len(p.split()) <= 4:
                # exclude common non-name terms
                if not any(word in p.lower() for word in ["year", "mobile", "phone", "contact", "yr", "email"]):
                    name_found = p
                    break

    extracted["name"] = name_found
    return extracted


def check_facts(raw_entry: str, extracted_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verifies that the LLM/parser extracted data honestly without
    hallucinating or inventing details not present in the original entry.
    """
    issues = []
    raw_lower = raw_entry.lower()

    # Verify email appears in raw text if present
    if extracted_dict.get("email"):
        email_val = str(extracted_dict["email"]).strip().lower()
        if email_val not in raw_lower:
            issues.append(f"Hallucination Warning: Email '{email_val}' not found in raw entry")

    # Verify phone digits appear in raw text
    if extracted_dict.get("phone"):
        raw_digits = re.sub(r"\D", "", str(extracted_dict["phone"]))
        entry_digits = re.sub(r"\D", "", raw_entry)
        if raw_digits and raw_digits not in entry_digits:
            issues.append(f"Hallucination Warning: Phone digits '{raw_digits}' not present in raw entry")

    is_factual = len(issues) == 0
    return is_factual, issues


def clean_phone(raw_phone: Any) -> Tuple[str, str]:
    """
    Cleans phone numbers according to project rules:
    - Remove spaces, dashes, parentheses, and '+'.
    - Remove leading '91' (if 12 digits) or '0' (if 11 digits).
    - Must contain exactly 10 digits.
    - Must start with 6, 7, 8, or 9.
    - Never change or invent any digits.
    Returns (cleaned_phone, error_message). If invalid, cleaned_phone is empty.
    """
    if not raw_phone:
        return "", "Missing phone number"

    # Convert to string and remove non-digit characters
    digits = re.sub(r"\D", "", str(raw_phone))

    # Strip country code / leading zeros
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    # Check length
    if len(digits) != 10:
        return "", f"Invalid phone length: expected 10 digits, got {len(digits)} ({digits})"

    # Check starting digit (must start with 6, 7, 8, or 9)
    if digits[0] not in ['6', '7', '8', '9']:
        return "", f"Invalid phone start digit: '{digits[0]}' (must begin with 6, 7, 8, or 9)"

    return digits, ""


def clean_email(raw_email: Any) -> Tuple[str, str]:
    """
    Cleans email addresses according to project rules:
    - Convert to lowercase.
    - Must contain exactly one '@'.
    - Must contain a dot ('.') after '@'.
    - Must not contain spaces.
    - Never automatically correct an email.
    Returns (cleaned_email, error_message).
    """
    if not raw_email:
        return "", "Missing email address"

    email_str = str(raw_email).strip().lower()

    if " " in email_str:
        return "", "Email contains illegal spaces"

    if email_str.count("@") != 1:
        return "", "Email must contain exactly one '@' symbol"

    user_part, domain_part = email_str.split("@")
    if not user_part:
        return "", "Email username part before '@' is empty"

    if "." not in domain_part or domain_part.startswith(".") or domain_part.endswith("."):
        return "", "Email must contain a valid domain dot '.' after '@'"

    return email_str, ""


def clean(extracted_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Standardizes fields and checks structural rules.
    - Name: Title case, trim spaces, no inventing.
    - Phone: cleaned using clean_phone.
    - Email: cleaned using clean_email.
    - Year: maps 1, 2, 3, 4, converts word formats, others rejected.
    - Branch: Allowed list ['CSE', 'IT', 'AIDS', 'ECE', 'EEE', 'MECH', 'CIVIL', 'other'].
    Returns (cleaned_dict, problems_list).
    """
    cleaned = {}
    problems = []

    # 1. Clean Name
    raw_name = extracted_data.get("name")
    if raw_name and str(raw_name).strip():
        # Title case and collapse multi-spaces
        clean_name_str = " ".join(str(raw_name).strip().split()).title()
        cleaned["name"] = clean_name_str
    else:
        cleaned["name"] = ""
        problems.append("Missing name")

    # 2. Clean Phone
    raw_phone = extracted_data.get("phone")
    phone_clean, phone_err = clean_phone(raw_phone)
    cleaned["phone"] = phone_clean
    if phone_err:
        problems.append(phone_err)

    # 3. Clean Email
    raw_email = extracted_data.get("email")
    email_clean, email_err = clean_email(raw_email)
    cleaned["email"] = email_clean
    if email_err:
        problems.append(email_err)

    # 4. Clean Year
    raw_year = extracted_data.get("year")
    year_val = None
    if raw_year is not None:
        try:
            # Handle string numbers, Roman numerals, words
            yr_str = str(raw_year).strip().lower()
            if yr_str in ["1", "1st", "first", "i"]:
                year_val = 1
            elif yr_str in ["2", "2nd", "second", "ii"]:
                year_val = 2
            elif yr_str in ["3", "3rd", "third", "iii"]:
                year_val = 3
            elif yr_str in ["4", "4th", "fourth", "final", "final year", "iv"]:
                year_val = 4
            else:
                num = int(yr_str)
                if num in [1, 2, 3, 4]:
                    year_val = num
        except ValueError:
            pass

    if year_val in [1, 2, 3, 4]:
        cleaned["year"] = year_val
    else:
        cleaned["year"] = ""
        problems.append(f"Invalid or missing year: '{raw_year}' (must be 1, 2, 3, or 4)")

    # 5. Clean Branch
    raw_branch = extracted_data.get("branch")
    if raw_branch and str(raw_branch).strip():
        branch_upper = str(raw_branch).strip().upper()
        # Common synonyms mapping
        if branch_upper in ["COMPUTER SCIENCE", "CS"]:
            branch_upper = "CSE"
        elif branch_upper in ["INFORMATION TECHNOLOGY"]:
            branch_upper = "IT"

        if branch_upper in ALLOWED_BRANCHES:
            cleaned["branch"] = branch_upper
        else:
            cleaned["branch"] = "other"
    else:
        cleaned["branch"] = "other"
        problems.append("Missing branch information (defaulted to 'other')")

    return cleaned, problems


def is_valid(problems: List[str]) -> bool:
    """
    Returns True if registration has zero problems, False otherwise.
    """
    return len(problems) == 0


def process(records: List[Dict[str, str]], system_prompt: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Processes all raw records through extraction, cleaning, validation,
    and duplicate detection (comparing cleaned phone and email).
    Returns (valid_list, problems_list, summary_stats).
    """
    valid_list = []
    problems_list = []

    # Seen sets for duplicate detection (phone and email)
    seen_phones = {}  # phone -> first registration id
    seen_emails = {}  # email -> first registration id

    stats = {
        "total": len(records),
        "valid": 0,
        "needs_fix": 0,
        "duplicates": 0,
        "branch_counts": {},
        "year_counts": {}
    }

    for item in records:
        reg_id = item["id"]
        raw_entry = item["entry"]

        # 1. Extraction (AI / Fallback)
        extracted = extract_with_llm(raw_entry, system_prompt)

        # 2. Fact checking
        _, fact_warnings = check_facts(raw_entry, extracted)

        # 3. Cleaning & field validation
        cleaned_data, problems = clean(extracted)
        problems.extend(fact_warnings)

        # 4. Duplicate Check (performed AFTER cleaning)
        is_dup = False
        dup_reasons = []

        if cleaned_data["phone"]:
            if cleaned_data["phone"] in seen_phones:
                is_dup = True
                dup_reasons.append(f"Duplicate phone number (first seen in Reg ID #{seen_phones[cleaned_data['phone']]})")
            else:
                seen_phones[cleaned_data["phone"]] = reg_id

        if cleaned_data["email"]:
            if cleaned_data["email"] in seen_emails:
                is_dup = True
                dup_reasons.append(f"Duplicate email address (first seen in Reg ID #{seen_emails[cleaned_data['email']]})")
            else:
                seen_emails[cleaned_data["email"]] = reg_id

        # 5. Status Determination
        if is_dup:
            status = "duplicate"
            all_issues = dup_reasons + problems
            stats["duplicates"] += 1
            problems_list.append({
                "id": reg_id,
                "original_entry": raw_entry,
                "extracted_details": json.dumps(extracted),
                "cleaned_name": cleaned_data.get("name", ""),
                "cleaned_phone": cleaned_data.get("phone", ""),
                "cleaned_email": cleaned_data.get("email", ""),
                "cleaned_year": cleaned_data.get("year", ""),
                "cleaned_branch": cleaned_data.get("branch", ""),
                "status": status,
                "reasons": "; ".join(all_issues)
            })
        elif not is_valid(problems):
            status = "needs_fix"
            stats["needs_fix"] += 1
            problems_list.append({
                "id": reg_id,
                "original_entry": raw_entry,
                "extracted_details": json.dumps(extracted),
                "cleaned_name": cleaned_data.get("name", ""),
                "cleaned_phone": cleaned_data.get("phone", ""),
                "cleaned_email": cleaned_data.get("email", ""),
                "cleaned_year": cleaned_data.get("year", ""),
                "cleaned_branch": cleaned_data.get("branch", ""),
                "status": status,
                "reasons": "; ".join(problems)
            })
        else:
            status = "valid"
            stats["valid"] += 1
            valid_list.append({
                "id": reg_id,
                "name": cleaned_data["name"],
                "phone": cleaned_data["phone"],
                "email": cleaned_data["email"],
                "year": cleaned_data["year"],
                "branch": cleaned_data["branch"]
            })

            # Tally stats for valid entries
            branch = cleaned_data["branch"]
            yr = cleaned_data["year"]
            stats["branch_counts"][branch] = stats["branch_counts"].get(branch, 0) + 1
            stats["year_counts"][yr] = stats["year_counts"].get(yr, 0) + 1

    return valid_list, problems_list, stats


def write_reports(valid_list: List[Dict[str, Any]],
                  problems_list: List[Dict[str, Any]],
                  stats: Dict[str, Any]) -> None:
    """
    Writes output reports:
    1. clean_list.csv: Contains valid registrations.
    2. problems.csv: Contains invalid and duplicate entries with reasons.
    3. summary.txt: Text summary of totals, branch counts, year counts.
    """
    # 1. Write clean_list.csv
    try:
        with open("clean_list.csv", mode="w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "name", "phone", "email", "year", "branch"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in valid_list:
                writer.writerow(row)
        print(" -> Created: clean_list.csv")
    except Exception as e:
        print(f"[ERROR] Failed writing clean_list.csv: {e}")

    # 2. Write problems.csv
    try:
        with open("problems.csv", mode="w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "id",
                "original_entry",
                "extracted_details",
                "cleaned_name",
                "cleaned_phone",
                "cleaned_email",
                "cleaned_year",
                "cleaned_branch",
                "status",
                "reasons"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in problems_list:
                writer.writerow(row)
        print(" -> Created: problems.csv")
    except Exception as e:
        print(f"[ERROR] Failed writing problems.csv: {e}")

    # 3. Write summary.txt
    try:
        with open("summary.txt", mode="w", encoding="utf-8") as f:
            f.write("=====================================================\n")
            f.write("      EVENT REGISTRATION CLEANER - SUMMARY REPORT    \n")
            f.write("=====================================================\n\n")
            f.write(f"Total registrations processed : {stats['total']}\n")
            f.write(f"Valid registrations           : {stats['valid']}\n")
            f.write(f"Registrations needing fixing  : {stats['needs_fix']}\n")
            f.write(f"Duplicate registrations       : {stats['duplicates']}\n\n")

            f.write("--- Valid Registrations by Branch ---\n")
            for br, count in sorted(stats["branch_counts"].items()):
                f.write(f"  * {br:<10}: {count}\n")
            if not stats["branch_counts"]:
                f.write("  (No valid registrations)\n")

            f.write("\n--- Valid Registrations by Year ---\n")
            for yr, count in sorted(stats["year_counts"].items()):
                f.write(f"  * Year {yr}   : {count}\n")
            if not stats["year_counts"]:
                f.write("  (No valid registrations)\n")

            f.write("\n=====================================================\n")
            f.write("Report generated successfully.\n")
        print(" -> Created: summary.txt")
    except Exception as e:
        print(f"[ERROR] Failed writing summary.txt: {e}")


def display_ui(stats: Dict[str, Any]) -> None:
    """
    Renders an attractive, beginner-friendly console dashboard.
    """
    print("\n" + "=" * 60)
    print("      EVENT REGISTRATION CLEANER – AI DATA TOOL      ")
    print("=" * 60)
    print(f" Total records processed      : {stats['total']}")
    print(f" Number of valid records      : {stats['valid']}  [✓]")
    print(f" Needs fix (missing/invalid)  : {stats['needs_fix']}  [⚠]")
    print(f" Duplicate registrations      : {stats['duplicates']}  [⚲]")
    print("-" * 60)
    print(" Output Files Created:")
    print("   1. clean_list.csv  (Verified & Cleaned Data)")
    print("   2. problems.csv    (Duplicates & Missing Details Log)")
    print("   3. summary.txt     (College Department Statistics)")
    print("=" * 60 + "\n")


def main():
    """
    Main driver function: loads system prompt, reads CSV,
    processes records, displays console UI, and writes reports.
    """
    print("\n[INFO] Starting Event Registration Cleaner...")

    # Load system prompt
    prompt_path = "system_prompt.txt"
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    else:
        system_prompt = "You are an assistant that extracts name, phone, email, year, branch."

    input_file = "registrations.csv"
    records = read_entry(input_file)
    if not records:
        print("[!] No records found to process.")
        return

    print(f"[INFO] Processing {len(records)} entries from '{input_file}'...")
    valid_list, problems_list, stats = process(records, system_prompt)

    # Save output files
    print("\n[INFO] Writing report files...")
    write_reports(valid_list, problems_list, stats)

    # Display console dashboard
    display_ui(stats)


if __name__ == "__main__":
    main()
