"""ASCII FIX framing checks. No network access or order submission."""
import re
from collections import Counter

SOH='\x01'

def _wire(text):
    text=text.strip(' \t\r\n')
    if not text:raise ValueError('Paste one complete FIX message.')
    if '|' in text and SOH in text:raise ValueError('Use either pipes or SOH separators, not both.')
    wire=text.replace('|',SOH)
    if not wire.endswith(SOH):raise ValueError('The message must end with a delimiter after tag 10.')
    try:wire.encode('ascii')
    except UnicodeEncodeError:raise ValueError('This checker supports ASCII FIX messages only.') from None
    return wire

def inspect_fix(text):
    wire=_wire(text)
    match=re.fullmatch(r'8=(FIX\.[0-9.]+)\x019=([0-9]+)\x01(35=[\s\S]*\x01)10=([0-9]{3})\x01',wire)
    if not match:raise ValueError('Expected 8=FIX.x.x, tag 9 second, tag 35 first in the body, and a final three-digit tag 10.')
    fields=[]
    for field in wire[:-1].split(SOH):
        if '=' not in field:raise ValueError('Every FIX field must use tag=value.')
        tag,value=field.split('=',1)
        if not tag.isdigit() or not value:raise ValueError('Tags must be numeric and values must be non-empty.')
        fields.append((tag,value))
    counts=Counter(tag for tag,value in fields)
    duplicates=[tag for tag,n in counts.items() if n>1]
    calculated_length=len(match.group(3).encode('ascii'))
    checksum_start=len(wire)-len('10=000'+SOH)
    calculated_checksum=sum(wire[:checksum_start].encode('ascii'))%256
    length_ok=int(match.group(2))==calculated_length
    checksum_ok=int(match.group(4))==calculated_checksum
    return {'valid':length_ok and checksum_ok,'body_length_ok':length_ok,'checksum_ok':checksum_ok,
            'declared_body_length':int(match.group(2)),'calculated_body_length':calculated_length,
            'declared_checksum':match.group(4),'calculated_checksum':calculated_checksum,
            'message_type':fields[2][1],'duplicate_tags':duplicates,'fields':fields}

def frame_fix(body,version='FIX.4.4'):
    if version not in ('FIX.4.2','FIX.4.4'):raise ValueError('Choose FIX.4.2 or FIX.4.4.')
    wire=_wire(body)
    if not wire.startswith('35='):raise ValueError('The body must start with tag 35.')
    tags=[field.split('=',1)[0] for field in wire[:-1].split(SOH)]
    if any(tag in ('8','9','10') for tag in tags):
        raise ValueError('Remove tags 8, 9 and 10; they are calculated by the tool.')
    for field in wire[:-1].split(SOH):
        if '=' not in field or not field.split('=',1)[0].isdigit() or not field.split('=',1)[1]:
            raise ValueError('Every body field must be a numeric tag with a non-empty value.')
    prefix=f'8={version}{SOH}9={len(wire.encode("ascii"))}{SOH}'+wire
    message=prefix+f'10={sum(prefix.encode("ascii"))%256:03d}{SOH}'
    return message.replace(SOH,'|')
