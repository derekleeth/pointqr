"""Contact payload encoders – vCard 3.0 and MECARD.

vCard 3.0 (RFC 2426) is the default: it imports natively on iOS, Android,
Outlook and Google Contacts.  MECARD is a much shorter format for static
codes where QR density matters more than field coverage.

Both builders are pure functions of a ``ContactData`` and must stay in sync
with the client-side builder used for the editor's live preview.
"""

from __future__ import annotations

from app.schemas.qrcode import ContactData

CRLF = "\r\n"
# RFC 2426 §2.6: lines SHOULD be folded to no more than 75 octets, excluding the line break.
MAX_LINE_OCTETS = 75

_TEL_TYPES = {
    "mobile": "CELL",
    "work": "WORK,VOICE",
    "home": "HOME,VOICE",
    "fax": "FAX",
    "other": "VOICE",
}
_EMAIL_TYPES = {
    "work": "INTERNET,WORK",
    "home": "INTERNET,HOME",
    "other": "INTERNET",
}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def display_name(contact: ContactData) -> str:
    """Return the formatted name (FN): the explicit override, else the name parts, else the org."""
    if contact.display_name:
        return contact.display_name
    parts = [contact.prefix, contact.first_name, contact.last_name, contact.suffix]
    joined = " ".join(p for p in parts if p)
    # ContactData guarantees at least one of first_name / last_name / organization
    return joined if (contact.first_name or contact.last_name) else (contact.organization or "")


# ---------------------------------------------------------------------------
# vCard 3.0
# ---------------------------------------------------------------------------

def _escape_text(value: str) -> str:
    """Escape a vCard TEXT value (RFC 2426 §4)."""
    return (
        _normalize_newlines(value)
        .replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def _structured(*parts: str | None) -> str:
    """Join structured-value components with ';', escaping each one."""
    return ";".join(_escape_text(p) if p else "" for p in parts)


def _fold(line: str) -> str:
    """Fold a content line to at most 75 octets per physical line.

    Continuation lines start with a single space, which counts toward their
    75 octets.  Splits never land inside a multi-byte UTF-8 sequence.
    """
    if len(line.encode("utf-8")) <= MAX_LINE_OCTETS:
        return line

    chunks: list[str] = []
    current = ""
    current_octets = 0
    limit = MAX_LINE_OCTETS
    for char in line:
        char_octets = len(char.encode("utf-8"))
        if current_octets + char_octets > limit:
            chunks.append(current)
            current, current_octets = "", 0
            limit = MAX_LINE_OCTETS - 1  # room for the leading space
        current += char
        current_octets += char_octets
    chunks.append(current)
    return (CRLF + " ").join(chunks)


def build_vcard(contact: ContactData) -> str:
    """Encode *contact* as a vCard 3.0 string with CRLF line endings."""
    lines = ["BEGIN:VCARD", "VERSION:3.0"]

    # N and FN are mandatory in vCard 3.0, so they're always emitted.
    lines.append("N:" + _structured(
        contact.last_name, contact.first_name, None, contact.prefix, contact.suffix
    ))
    lines.append("FN:" + _escape_text(display_name(contact)))

    if contact.organization:
        lines.append("ORG:" + _escape_text(contact.organization))
    if contact.job_title:
        lines.append("TITLE:" + _escape_text(contact.job_title))

    for phone in contact.phones:
        lines.append(f"TEL;TYPE={_TEL_TYPES[phone.type]}:{phone.number}")
    for email in contact.emails:
        lines.append(f"EMAIL;TYPE={_EMAIL_TYPES[email.type]}:{email.address}")

    # URL is a URI value, not TEXT, so it isn't escaped (that would corrupt query strings).
    if contact.website:
        lines.append(f"URL:{contact.website}")

    if contact.address:
        addr = contact.address
        lines.append(f"ADR;TYPE={addr.type.upper()}:" + _structured(
            None, None, addr.street, addr.city, addr.region, addr.postal_code, addr.country
        ))

    if contact.birthday:
        lines.append(f"BDAY:{contact.birthday.isoformat()}")
    if contact.note:
        lines.append("NOTE:" + _escape_text(contact.note))

    lines.append("END:VCARD")
    return CRLF.join(_fold(line) for line in lines) + CRLF


# ---------------------------------------------------------------------------
# MECARD
# ---------------------------------------------------------------------------

def _escape_mecard(value: str) -> str:
    """Escape a MECARD field value.  Newlines aren't supported, so they become spaces."""
    value = " ".join(_normalize_newlines(value).split("\n"))
    for char in ("\\", ";", ",", ":"):
        value = value.replace(char, "\\" + char)
    return value


def build_mecard(contact: ContactData) -> str:
    """Encode *contact* as a compact MECARD string.

    MECARD has no job title, phone/email types or prefix/suffix, so those are
    dropped.  ORG isn't in the original DoCoMo spec but is widely supported.
    """
    fields: list[str] = []

    if contact.first_name or contact.last_name:
        name = ",".join(
            _escape_mecard(p) for p in (contact.last_name, contact.first_name) if p
        )
    else:
        name = _escape_mecard(display_name(contact))
    fields.append(f"N:{name}")

    if contact.organization:
        fields.append(f"ORG:{_escape_mecard(contact.organization)}")
    for phone in contact.phones:
        fields.append(f"TEL:{_escape_mecard(phone.number)}")
    for email in contact.emails:
        fields.append(f"EMAIL:{_escape_mecard(str(email.address))}")
    if contact.website:
        fields.append(f"URL:{_escape_mecard(contact.website)}")
    if contact.address:
        addr = contact.address
        # DoCoMo order: PO box, extended, street, city, region, postal code, country
        parts = ("", "", addr.street, addr.city, addr.region, addr.postal_code, addr.country)
        fields.append("ADR:" + ",".join(_escape_mecard(p) if p else "" for p in parts))
    if contact.birthday:
        fields.append(f"BDAY:{contact.birthday.strftime('%Y%m%d')}")
    if contact.note:
        fields.append(f"NOTE:{_escape_mecard(contact.note)}")

    return "MECARD:" + "".join(f + ";" for f in fields) + ";"


def build_contact_payload(contact: ContactData) -> str:
    """Return the string a static contact QR code encodes, honoring ``contact.encoding``."""
    if contact.encoding == "mecard":
        return build_mecard(contact)
    return build_vcard(contact)
