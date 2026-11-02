"""Unit tests for the vCard / MECARD contact encoders."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.qrcode import ContactData
from app.services.vcard import (
    build_contact_payload,
    build_mecard,
    build_vcard,
    display_name,
)


def _contact(**kwargs) -> ContactData:
    return ContactData.model_validate({"first_name": "Ada", "last_name": "Lovelace", **kwargs})


def _unfold(vcard: str) -> list[str]:
    """Undo RFC 2426 line folding and split into logical lines."""
    return vcard.replace("\r\n ", "").split("\r\n")


# ---------------------------------------------------------------------------
# vCard structure
# ---------------------------------------------------------------------------

def test_minimal_vcard_structure() -> None:
    vcard = build_vcard(_contact())
    assert vcard == (
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        "N:Lovelace;Ada;;;\r\n"
        "FN:Ada Lovelace\r\n"
        "END:VCARD\r\n"
    )


def test_lines_end_with_crlf_only() -> None:
    vcard = build_vcard(_contact(note="line one\nline two\r\nline three\rfour"))
    assert vcard.endswith("\r\n")
    # Every \n must be part of a CRLF pair, and no bare \r may remain
    assert vcard.count("\n") == vcard.count("\r\n")
    assert vcard.count("\r") == vcard.count("\r\n")


def test_full_contact_emits_all_properties() -> None:
    contact = _contact(
        prefix="Dr.",
        suffix="PhD",
        organization="Analytical Engines",
        job_title="Programmer",
        phones=[
            {"type": "mobile", "number": "+1 555 0100"},
            {"type": "work", "number": "(555) 010-0200 x12"},
            {"type": "fax", "number": "555.0300"},
        ],
        emails=[{"type": "home", "address": "ada@example.com"}],
        website="https://example.com/ada?ref=qr,1",
        address={"type": "home", "street": "12 St James's Sq", "city": "London",
                 "postal_code": "SW1Y 4JH", "country": "UK"},
        birthday="1815-12-10",
        note="First programmer",
    )
    lines = _unfold(build_vcard(contact))
    assert "N:Lovelace;Ada;;Dr.;PhD" in lines
    assert "FN:Dr. Ada Lovelace PhD" in lines
    assert "ORG:Analytical Engines" in lines
    assert "TITLE:Programmer" in lines
    assert "TEL;TYPE=CELL:+1 555 0100" in lines
    assert "TEL;TYPE=WORK,VOICE:(555) 010-0200 x12" in lines
    assert "TEL;TYPE=FAX:555.0300" in lines
    assert "EMAIL;TYPE=INTERNET,HOME:ada@example.com" in lines
    # URL is a URI value – commas in it must not be escaped
    assert "URL:https://example.com/ada?ref=qr,1" in lines
    assert "ADR;TYPE=HOME:;;12 St James's Sq;London;;SW1Y 4JH;UK" in lines
    assert "BDAY:1815-12-10" in lines
    assert "NOTE:First programmer" in lines


# ---------------------------------------------------------------------------
# Escaping
# ---------------------------------------------------------------------------

def test_escapes_special_characters_in_text() -> None:
    contact = _contact(
        organization="Smith, Jones; Partners",
        note="C:\\path\\file, done; ok\nnext line",
    )
    lines = _unfold(build_vcard(contact))
    assert "ORG:Smith\\, Jones\\; Partners" in lines
    assert "NOTE:C:\\\\path\\\\file\\, done\\; ok\\nnext line" in lines


def test_escapes_inside_structured_components() -> None:
    contact = ContactData(first_name="Jean;Luc", last_name="Picard, Jr.")
    lines = _unfold(build_vcard(contact))
    # Component separators stay raw; separators inside values are escaped
    assert "N:Picard\\, Jr.;Jean\\;Luc;;;" in lines


# ---------------------------------------------------------------------------
# Folding
# ---------------------------------------------------------------------------

def test_short_lines_are_not_folded() -> None:
    assert "\r\n " not in build_vcard(_contact(note="x" * 60))


def test_long_lines_fold_at_75_octets() -> None:
    note = "x" * 300
    vcard = build_vcard(_contact(note=note))
    for physical in vcard.split("\r\n"):
        assert len(physical.encode("utf-8")) <= 75
    assert f"NOTE:{note}" in _unfold(vcard)


def test_folding_counts_utf8_bytes_and_never_splits_a_character() -> None:
    # "é" and "ñ" are 2 bytes each, "😀" is 4 – a character count would overrun 75 octets
    note = "Café Ñúñez 😀 " * 20
    vcard = build_vcard(_contact(note=note))
    physical_lines = vcard.split("\r\n")
    for physical in physical_lines:
        assert len(physical.encode("utf-8")) <= 75
    assert any(physical.startswith(" ") for physical in physical_lines)
    # Each physical line decodes on its own, so no multi-byte sequence was split
    for physical in physical_lines:
        physical.encode("utf-8").decode("utf-8")
    assert f"NOTE:{note.strip()}" in _unfold(vcard)


def test_utf8_names_round_trip() -> None:
    contact = ContactData(first_name="José", last_name="Ñúñez", organization="Café, S.A.")
    lines = _unfold(build_vcard(contact))
    assert "N:Ñúñez;José;;;" in lines
    assert "FN:José Ñúñez" in lines
    assert "ORG:Café\\, S.A." in lines


# ---------------------------------------------------------------------------
# Empty-field omission
# ---------------------------------------------------------------------------

def test_empty_fields_are_omitted() -> None:
    contact = ContactData.model_validate({
        "first_name": "Ada",
        "last_name": "  ",
        "organization": "",
        "job_title": None,
        "website": "",
        "note": "   ",
        "address": {"type": "work", "street": "", "city": None},
    })
    vcard = build_vcard(contact)
    for prop in ("ORG", "TITLE", "TEL", "EMAIL", "URL", "ADR", "NOTE", "BDAY"):
        assert f"\r\n{prop}" not in vcard
    assert "N:;Ada;;;" in _unfold(vcard)


# ---------------------------------------------------------------------------
# FN derivation
# ---------------------------------------------------------------------------

def test_fn_uses_display_name_override() -> None:
    contact = _contact(display_name="Countess of Lovelace")
    assert "FN:Countess of Lovelace" in _unfold(build_vcard(contact))


def test_fn_from_single_name_part() -> None:
    assert display_name(ContactData(last_name="Lovelace")) == "Lovelace"
    assert display_name(ContactData(first_name="Ada")) == "Ada"


def test_fn_falls_back_to_organization() -> None:
    contact = ContactData(organization="Acme, Inc.")
    lines = _unfold(build_vcard(contact))
    assert "N:;;;;" in lines
    assert "FN:Acme\\, Inc." in lines


# ---------------------------------------------------------------------------
# MECARD
# ---------------------------------------------------------------------------

def test_mecard_format() -> None:
    contact = _contact(
        organization="Smith, Jones",
        job_title="Ignored in MECARD",
        phones=[{"type": "mobile", "number": "+1 555 0100"}],
        emails=[{"address": "ada@example.com"}],
        website="https://example.com",
        birthday=date(1815, 12, 10),
        note="two\nlines",
    )
    assert build_mecard(contact) == (
        "MECARD:N:Lovelace,Ada;ORG:Smith\\, Jones;TEL:+1 555 0100;"
        "EMAIL:ada@example.com;URL:https\\://example.com;BDAY:18151210;NOTE:two lines;;"
    )


def test_mecard_org_only_name() -> None:
    assert build_mecard(ContactData(organization="Acme")) == "MECARD:N:Acme;ORG:Acme;;"


def test_mecard_is_shorter_than_vcard() -> None:
    contact = _contact(phones=[{"number": "+1 555 0100"}], emails=[{"address": "ada@example.com"}])
    assert len(build_mecard(contact)) < len(build_vcard(contact))


def test_build_contact_payload_honours_encoding() -> None:
    assert build_contact_payload(_contact()).startswith("BEGIN:VCARD")
    assert build_contact_payload(_contact(encoding="mecard")).startswith("MECARD:")


# ---------------------------------------------------------------------------
# ContactData validation
# ---------------------------------------------------------------------------

def test_requires_a_name_or_organization() -> None:
    with pytest.raises(ValidationError, match="at least one of"):
        ContactData(job_title="Programmer")


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://example.com", "example.com", "data:text/html,hi"])
def test_rejects_non_http_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        _contact(website=url)
    with pytest.raises(ValidationError):
        _contact(social_links=[{"label": "x", "url": url}])


@pytest.mark.parametrize("number", ["abc", "12", "+1 555 <script>", "555-0100; DROP"])
def test_rejects_invalid_phone_numbers(number: str) -> None:
    with pytest.raises(ValidationError):
        _contact(phones=[{"number": number}])


def test_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        _contact(emails=[{"address": "not-an-email"}])


def test_list_caps() -> None:
    with pytest.raises(ValidationError):
        _contact(phones=[{"number": "555 0100"}] * 6)
    with pytest.raises(ValidationError):
        _contact(emails=[{"address": "a@example.com"}] * 4)


def test_note_length_cap() -> None:
    with pytest.raises(ValidationError):
        _contact(note="x" * 501)


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        _contact(nickname="Ada")


def test_photo_url_allows_own_static_storage() -> None:
    assert _contact(photo_url="/static/logos/u/q/photo.png").photo_url == "/static/logos/u/q/photo.png"
    with pytest.raises(ValidationError):
        _contact(photo_url="/etc/passwd")
