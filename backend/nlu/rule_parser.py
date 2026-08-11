import re

EMAIL_RE = re.compile(r'[\w.\-+]+@[\w.\-]+\.\w+')
PHONE_RE = re.compile(r'\+?\d[\d\-\s]{5,}\d')
QUOTED_PHONE_RE = re.compile(r'["\']?(\+?\d[\d\-\s]{5,}\d)["\']?')


def parse(message: str) -> dict:
    """Simple keyword + regex based fallback parser."""
    text = message.strip()
    lower = text.lower()

    email_match = EMAIL_RE.search(text)
    email = email_match.group(0) if email_match else None

    # DELETE
    if re.search(r'\b(remove|delete)\b', lower):
        return {"action": "delete", "email": email, "name": None, "fields": {}}

    # ADD
    if re.search(r'\b(add|create|register)\b', lower):
        fields = {}
        phone_match = PHONE_RE.search(text)
        if phone_match:
            fields["phone"] = phone_match.group(0).strip()
        city_match = re.search(r'city\s+"?([A-Za-z\s]+)"?', text, re.IGNORECASE)
        if city_match:
            fields["city"] = city_match.group(1).strip().rstrip('"')
        name_match = re.search(r'name\s+"?([A-Za-z\s]+)"?', text, re.IGNORECASE)
        if name_match:
            fields["name"] = name_match.group(1).strip().rstrip('"')
        if email:
            fields["email"] = email
        return {"action": "add", "email": email, "name": None, "fields": fields}

    # UPDATE — e.g. "update samanthas city to Cordoba"
    update_match = re.search(
        r"update\s+([A-Za-z]+)'?s?\s+(\w+)\s+to\s+([\w.\-@\s]+)", text, re.IGNORECASE
    )
    if update_match:
        name, field, value = update_match.groups()
        return {
            "action": "update",
            "email": email,
            "name": name,
            "fields": {field.lower(): value.strip()},
        }

    if re.search(r'\b(update|change|set)\b', lower):
        field_match = re.search(r'\b(phone|city|name|email)\b', lower)
        value_match = re.search(r'to\s+["\']?([\w.\-@\s\+]+?)["\']?\s*$', text, re.IGNORECASE)
        if field_match and value_match:
            return {
                "action": "update",
                "email": email,
                "name": None,
                "fields": {field_match.group(1): value_match.group(1).strip()},
            }

    return {"action": "unknown", "email": email, "name": None, "fields": {}}