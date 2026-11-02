/**
 * Contact payload helpers for the editor.
 *
 * buildVCard / buildMecard mirror backend/app/services/vcard.py so the live
 * preview matches what the server saves. Change them together.
 */

import type { ContactAddress, ContactData } from '@/api/qrcodes'

/** Editor state: same shape as ContactData, but the address is always present. */
export type ContactFormState = ContactData & { address: ContactAddress }

export const MAX_PHONES = 5
export const MAX_EMAILS = 3
export const MAX_SOCIAL_LINKS = 10

const CRLF = '\r\n'
const MAX_LINE_OCTETS = 75

const TEL_TYPES = {
  mobile: 'CELL',
  work: 'WORK,VOICE',
  home: 'HOME,VOICE',
  fax: 'FAX',
  other: 'VOICE',
} as const

const EMAIL_TYPES = {
  work: 'INTERNET,WORK',
  home: 'INTERNET,HOME',
  other: 'INTERNET',
} as const

// Same patterns as ContactData in backend/app/schemas/qrcode.py
const PHONE_PATTERN = /^\+?[0-9 ()./-]+(?:\s*(?:x|ext\.?)\s*[0-9]+)?$/i
const HTTP_URL_PATTERN = /^https?:\/\/[^\s/$.?#][^\s]*$/i
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const encoder = new TextEncoder()

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------

function clean(value: string | null | undefined): string | null {
  return value?.trim() || null
}

/** A blank form. One empty phone and email row are shown up front. */
export function emptyContact(): ContactFormState {
  return {
    prefix: null,
    first_name: null,
    last_name: null,
    suffix: null,
    display_name: null,
    organization: null,
    job_title: null,
    phones: [{ type: 'mobile', number: '' }],
    emails: [{ type: 'work', address: '' }],
    website: null,
    address: {
      type: 'work',
      street: null,
      city: null,
      region: null,
      postal_code: null,
      country: null,
    },
    note: null,
    birthday: null,
    encoding: 'vcard',
    social_links: [],
    photo_url: null,
    theme_color: null,
  }
}

/** Build editor state from a saved content_data value. */
export function contactFromServer(data: ContactData | null): ContactFormState {
  const empty = emptyContact()
  if (!data) return empty
  return {
    ...empty,
    ...data,
    phones: data.phones.length ? data.phones.map((p) => ({ ...p })) : empty.phones,
    emails: data.emails.length ? data.emails.map((e) => ({ ...e })) : empty.emails,
    address: { ...empty.address, ...(data.address ?? {}) },
    social_links: data.social_links.map((l) => ({ ...l })),
  }
}

/** Trim everything and drop blank rows, giving the value that is encoded and saved. */
export function normalizeContact(form: ContactFormState): ContactData {
  const { address } = form
  const street = clean(address.street)
  const city = clean(address.city)
  const region = clean(address.region)
  const postalCode = clean(address.postal_code)
  const country = clean(address.country)
  const hasAddress = street || city || region || postalCode || country

  return {
    ...form,
    prefix: clean(form.prefix),
    first_name: clean(form.first_name),
    last_name: clean(form.last_name),
    suffix: clean(form.suffix),
    display_name: clean(form.display_name),
    organization: clean(form.organization),
    job_title: clean(form.job_title),
    phones: form.phones
      .map((p) => ({ type: p.type, number: p.number.trim() }))
      .filter((p) => p.number),
    emails: form.emails
      .map((e) => ({ type: e.type, address: e.address.trim() }))
      .filter((e) => e.address),
    website: clean(form.website),
    address: hasAddress
      ? { type: address.type, street, city, region, postal_code: postalCode, country }
      : null,
    note: clean(form.note),
    birthday: clean(form.birthday),
    social_links: form.social_links
      .map((l) => ({ label: l.label.trim(), url: l.url.trim() }))
      .filter((l) => l.label || l.url),
  }
}

/** Static codes have no hosted page, so the fields only that page uses don't apply. */
export function withoutHostedFields(contact: ContactData): ContactData {
  return { ...contact, social_links: [], photo_url: null, theme_color: null }
}

export function hasContactName(form: ContactFormState): boolean {
  return !!(clean(form.first_name) || clean(form.last_name) || clean(form.organization))
}

export interface ContactErrors {
  phones: Record<number, string>
  emails: Record<number, string>
  website?: string
  socialLinks: Record<number, string>
}

/** Field errors keyed by form row. Blank rows are ignored, since they are never saved. */
export function validateContact(form: ContactFormState): ContactErrors {
  const errors: ContactErrors = { phones: {}, emails: {}, socialLinks: {} }

  form.phones.forEach((phone, i) => {
    const number = phone.number.trim()
    if (!number) return
    const digits = number.replace(/\D/g, '').length
    if (!PHONE_PATTERN.test(number) || digits < 3) {
      errors.phones[i] = 'Enter a valid phone number.'
    }
  })
  form.emails.forEach((email, i) => {
    const address = email.address.trim()
    if (address && !EMAIL_PATTERN.test(address)) {
      errors.emails[i] = 'Enter a valid email address.'
    }
  })
  const website = clean(form.website)
  if (website && !HTTP_URL_PATTERN.test(website)) {
    errors.website = 'Enter a full URL starting with http:// or https://.'
  }
  form.social_links.forEach((link, i) => {
    const label = link.label.trim()
    const url = link.url.trim()
    if (!label && !url) return
    if (!label) {
      errors.socialLinks[i] = 'Enter a label for this link.'
    } else if (!HTTP_URL_PATTERN.test(url)) {
      errors.socialLinks[i] = 'Enter a full URL starting with http:// or https://.'
    }
  })
  return errors
}

export function hasContactErrors(errors: ContactErrors): boolean {
  return (
    Object.keys(errors.phones).length > 0 ||
    Object.keys(errors.emails).length > 0 ||
    !!errors.website ||
    Object.keys(errors.socialLinks).length > 0
  )
}

// ---------------------------------------------------------------------------
// Encoding
// ---------------------------------------------------------------------------

function normalizeNewlines(value: string): string {
  return value.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
}

/** The formatted name: the explicit override, else the name parts, else the org. */
export function contactDisplayName(contact: ContactData): string {
  if (contact.display_name) return contact.display_name
  if (!contact.first_name && !contact.last_name) return contact.organization ?? ''
  return [contact.prefix, contact.first_name, contact.last_name, contact.suffix]
    .filter(Boolean)
    .join(' ')
}

function escapeText(value: string): string {
  return normalizeNewlines(value)
    .replace(/\\/g, '\\\\')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;')
    .replace(/\n/g, '\\n')
}

function structured(...parts: (string | null | undefined)[]): string {
  return parts.map((p) => (p ? escapeText(p) : '')).join(';')
}

/** Fold to 75 octets per physical line, never splitting a multi-byte character. */
function fold(line: string): string {
  if (encoder.encode(line).length <= MAX_LINE_OCTETS) return line

  const chunks: string[] = []
  let current = ''
  let currentOctets = 0
  let limit = MAX_LINE_OCTETS
  for (const char of line) {
    const charOctets = encoder.encode(char).length
    if (currentOctets + charOctets > limit) {
      chunks.push(current)
      current = ''
      currentOctets = 0
      limit = MAX_LINE_OCTETS - 1 // room for the leading space
    }
    current += char
    currentOctets += charOctets
  }
  chunks.push(current)
  return chunks.join(`${CRLF} `)
}

export function buildVCard(contact: ContactData): string {
  const lines = ['BEGIN:VCARD', 'VERSION:3.0']

  lines.push(
    `N:${structured(contact.last_name, contact.first_name, null, contact.prefix, contact.suffix)}`,
  )
  lines.push(`FN:${escapeText(contactDisplayName(contact))}`)

  if (contact.organization) lines.push(`ORG:${escapeText(contact.organization)}`)
  if (contact.job_title) lines.push(`TITLE:${escapeText(contact.job_title)}`)

  for (const phone of contact.phones) lines.push(`TEL;TYPE=${TEL_TYPES[phone.type]}:${phone.number}`)
  for (const email of contact.emails) {
    lines.push(`EMAIL;TYPE=${EMAIL_TYPES[email.type]}:${email.address}`)
  }

  // URL is a URI value, not TEXT, so it isn't escaped
  if (contact.website) lines.push(`URL:${contact.website}`)
  for (const link of contact.social_links) {
    const label = link.label.replace(/[^A-Za-z0-9]/g, '').toUpperCase()
    lines.push(label ? `URL;TYPE=${label}:${link.url}` : `URL:${link.url}`)
  }

  if (contact.address) {
    const addr = contact.address
    lines.push(
      `ADR;TYPE=${addr.type.toUpperCase()}:` +
        structured(null, null, addr.street, addr.city, addr.region, addr.postal_code, addr.country),
    )
  }

  if (contact.birthday) lines.push(`BDAY:${contact.birthday}`)
  if (contact.note) lines.push(`NOTE:${escapeText(contact.note)}`)

  lines.push('END:VCARD')
  return lines.map(fold).join(CRLF) + CRLF
}

function escapeMecard(value: string): string {
  return normalizeNewlines(value).replace(/\n/g, ' ').replace(/[\\;,:]/g, '\\$&')
}

export function buildMecard(contact: ContactData): string {
  const fields: string[] = []

  const name =
    contact.first_name || contact.last_name
      ? [contact.last_name, contact.first_name]
          .filter((p): p is string => !!p)
          .map(escapeMecard)
          .join(',')
      : escapeMecard(contactDisplayName(contact))
  fields.push(`N:${name}`)

  if (contact.organization) fields.push(`ORG:${escapeMecard(contact.organization)}`)
  for (const phone of contact.phones) fields.push(`TEL:${escapeMecard(phone.number)}`)
  for (const email of contact.emails) fields.push(`EMAIL:${escapeMecard(email.address)}`)
  if (contact.website) fields.push(`URL:${escapeMecard(contact.website)}`)
  if (contact.address) {
    const addr = contact.address
    const parts = ['', '', addr.street, addr.city, addr.region, addr.postal_code, addr.country]
    fields.push(`ADR:${parts.map((p) => (p ? escapeMecard(p) : '')).join(',')}`)
  }
  if (contact.birthday) fields.push(`BDAY:${contact.birthday.replace(/-/g, '')}`)
  if (contact.note) fields.push(`NOTE:${escapeMecard(contact.note)}`)

  return `MECARD:${fields.map((f) => `${f};`).join('')};`
}

export function buildContactPayload(contact: ContactData): string {
  return contact.encoding === 'mecard' ? buildMecard(contact) : buildVCard(contact)
}
