import six, ptypes, osi.network.inet4, osi.network.inet6
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class u8(pint.uint8_t): pass
class s8(pint.sint8_t): pass
class u16(pint.uint16_t): pass
class s16(pint.sint16_t): pass
class u32(pint.uint32_t): pass
class s32(pint.sint32_t): pass

class Name(pstruct.type):
    def __string(self):
        octet = self['length'].li
        if octet.int() & 0xc0:
            return pint.uint8_t
        return dyn.block(octet.int())

    _fields_ = [
        (u8, 'length'),
        (__string, 'string'),
    ]

    def CompressedQ(self):
        length = self['length'].int()
        return True if length & 0xc0 else False

    def str(self):
        if self.CompressedQ():
            raise TypeError("{:s} : Name is compressed".format(self.instance()))
        res = self['string'].serialize()
        return res.decode('ascii')

    def int(self):
        if self.CompressedQ():
            offset = self.cast(u16)
            return offset.int() & 0x3fff
        raise TypeError("{:s} : Name is not compressed".format(self.instance()))

    def summary(self):
        if self.CompressedQ():
            offset = self.int()
            return "OFFSET: {:+#x}".format(offset)
        res = self['length'].int()
        return "({:d}) {:s}".format(res, self.str())

    def repr(self):
        return self.summary()

    def set(self, value):
        if isinstance(value, six.integer_types):
            res = pint.uint16_t().set(0xc000 | value)
            return self.load(source=ptypes.prov.bytes(res.serialize()))
        elif isinstance(value, bytes) and len(value) < 0x40:
            return self.alloc(length=len(value), string=value)
        elif isinstance(value, six.string_types) and len(value) < 0x40:
            return self.alloc(length=len(value), string=value.encode('ascii'))
        elif isinstance(value, six.string_types) and len(value) < 0xc0:
            raise ValueError(value)
        raise ValueError(value)

class String(pstruct.type):
    def __string(self):
        res = self['length'].li
        return dyn.clone(pstr.string, length=res.int())

    _fields_ = [
        (u8, 'length'),
        (__string, 'string'),
    ]

    def str(self):
        return self['string'].str()

    def summary(self):
        res = self['length']
        return "({:d}) {:s}".format(res.int(), self.str())

    def repr(self):
        return self.summary()

class Label(parray.terminated):
    # XXX: Feeling kind of lazy now that all this data-entry is done, and
    #      this doesn't support message-compression at the moment even
    #      though the `Name` object does.
    _object_ = Name

    def isTerminator(self, item):
        return item.CompressedQ() or item['length'].int() == 0

    def str(self):
        items = ["{:+#x}".format(item.int()) if item.CompressedQ() else item.str() for item in self]
        return '.'.join(items)

    def alloc(self, items):
        name = items
        if isinstance(name, six.string_types):
            items = name.split('.') if name.endswith('.') else (name + '.').split('.')
            return super(Label, self).alloc(items)
        return super(Label, self).alloc(items)

    def summary(self):
        return "({:d}) {:s}".format(len(self), self.str())

class TYPE(pint.enum, pint.uint16_t):
    _values_ = [
        ('A', 1),
        ('NS', 2),
        ('MD', 3),
        ('MF', 4),
        ('CNAME', 5),
        ('SOA', 6),
        ('MB', 7),
        ('MG', 8),
        ('MR', 9),
        ('NULL', 10),
        ('WKS', 11),
        ('PTR', 12),
        ('HINFO', 13),
        ('MINFO', 14),
        ('MX', 15),
        ('TXT', 16),
        ('RP', 17),
        ('AFSDB', 18),
        ('X25', 19),
        ('ISDN', 20),
        ('RT', 21),
        ('NSAP', 22),
        ('SIG', 24),
        ('KEY', 25),
        ('PX', 26),
        ('AAAA', 28),
        ('LOC', 29),
        ('NXT', 30),
        ('SRV', 33),
        ('NAPTR', 35),
        ('KX', 36),
        ('CERT', 37),
        ('A6', 38),
        ('DNAME', 39),
        ('DS', 43),
        ('SSHFP', 44),
        ('IPSECKEY', 45),
        ('RRSIG', 46),
        ('NSEC', 47),
        ('DNSKEY', 48),
        ('DHCID', 49),
        ('SPF', 99),
    ]

class QTYPE(TYPE):
    _values_ = TYPE._values_ + [
        ('IXFR', 251),
        ('AXFR', 252),
        ('MAILB', 253),
        ('MAILA', 254),
        ('*', 255),
    ]

class CLASS(pint.enum, pint.uint16_t):
    _values_ = [
        ('IN', 1),
        ('CS', 2),
        ('CH', 3),
        ('HS', 4),
    ]

class QCLASS(CLASS):
    _values_ = CLASS._values_ + [
        ('*', 255),
    ]

class RDATA(ptype.definition):
    cache = {}

@RDATA.define
class A(pstruct.type):
    type = TYPE.byname('A'), CLASS.byname('IN')

    _fields_ = [
        (osi.network.inet4.in_addr, 'ADDRESS'),
    ]

    def summary(self):
        return self['ADDRESS'].summary()

@RDATA.define
class NS(pstruct.type):
    type = TYPE.byname('NS'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'NSDNAME'),
    ]

    def summary(self):
        return self['NSDNAME'].str()

@RDATA.define
class MD(pstruct.type):
    type = TYPE.byname('MD'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MADNAME'),
    ]

    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class MF(pstruct.type):
    type = TYPE.byname('MF'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MADNAME'),
    ]

    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class CNAME(pstruct.type):
    type = TYPE.byname('CNAME'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'CNAME'),
    ]

    def summary(self):
        return self['CNAME'].str()

@RDATA.define
class SOA(pstruct.type):
    type = TYPE.byname('SOA'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MNAME'),
        (Label, 'RNAME'),
        (u32, 'SERIAL'),
        (u32, 'REFRESH'),
        (u32, 'RETRY'),
        (u32, 'EXPIRE'),
        (u32, 'MINIMUM'),
    ]

    def summary(self):
        fields = ['SERIAL', 'REFRESH', 'RETRY', 'EXPIRE', 'MINIMUM']
        items = ["{:d}".format(self[fld].int()) for fld in fields]
        return ' '.join([self['MNAME'].str(), self['RNAME'].str()] + items)

@RDATA.define
class MB(pstruct.type):
    type = TYPE.byname('MB'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MADNAME'),
    ]

    def summary(self):
        return self['MADNAME'].str()

@RDATA.define
class MG(pstruct.type):
    type = TYPE.byname('MG'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'MGMNAME'),
    ]

    def summary(self):
        return self['MGMNAME'].str()

@RDATA.define
class MR(pstruct.type):
    type = TYPE.byname('MR'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'NEWNAME'),
    ]

    def summary(self):
        return self['NEWNAME'].str()

@RDATA.define
class NULL(ptype.block):
    type = TYPE.byname('NULL'), CLASS.byname('IN')

@RDATA.define
class WKS(pstruct.type):
    type = TYPE.byname('WKS'), CLASS.byname('IN')
    _fields_ = [
        (osi.network.inet4.in_addr, 'ADDRESS'),
        (u8, 'PROTOCOL'),
        (ptype.undefined, 'BITMAP'),
    ]

@RDATA.define
class PTR(pstruct.type):
    type = TYPE.byname('PTR'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'PTRDNAME'),
    ]

    def summary(self):
        return self['PTRDNAME'].str()

@RDATA.define
class HINFO(pstruct.type):
    type = TYPE.byname('HINFO'), CLASS.byname('IN')

    _fields_ = [
        (String, 'CPU'),
        (String, 'OS'),
    ]

    def summary(self):
        return "CPU={:s} OS={:s}".format(self['CPU'].str(), self['OS'].str())

@RDATA.define
class MINFO(pstruct.type):
    type = TYPE.byname('MINFO'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'RMAILBX'),
        (Label, 'EMAILBX'),
    ]

    def summary(self):
        return ' '.join([self['RMAILBX'].str(), self['EMAILBX'].str()])

@RDATA.define
class MX(pstruct.type):
    type = TYPE.byname('MX'), CLASS.byname('IN')

    _fields_ = [
        (u16, 'PREFERENCE'),
        (Label, 'EXCHANGE'),
    ]

    def summary(self):
        return "{:d} {:s}".format(self['PREFERENCE'].int(), self['EXCHANGE'].str())

@RDATA.define
class TXT(parray.block):
    type = TYPE.byname('TXT'), CLASS.byname('IN')
    _object_ = String

@RDATA.define
class RP(pstruct.type):
    type = TYPE.byname('RP'), CLASS.byname('IN')

    _fields_ = [
        (Label, 'mbox'),
        (Label, 'txt'),
    ]

@RDATA.define
class AFSDB(pstruct.type):
    type = TYPE.byname('AFSDB'), CLASS.byname('IN')

    _fields_ = [
        (u16, 'subtype'),
        (Label, 'hostname'),
    ]

@RDATA.define
class X25(pstruct.type):
    type = TYPE.byname('X25'), CLASS.byname('IN')

    _fields_ = [
        (String, 'PSDN-address'),
    ]

@RDATA.define
class ISDN(pstruct.type):
    type = TYPE.byname('ISDN'), CLASS.byname('IN')
    _fields_ = [
        (String, 'ISDN-address'),
        (String, 'sa'),
    ]

@RDATA.define
class RT(pstruct.type):
    type = TYPE.byname('RT'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'preference'),
        (Label, 'intermediate-host'),
    ]

@RDATA.define
class NSAP(pstr.string):
    type = TYPE.byname('NSAP'), CLASS.byname('IN')

@RDATA.define
class SIG(pstruct.type):
    type = TYPE.byname('SIG'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'type-covered'),
        (u8, 'algorithm'),
        (u8, 'labels'),
        (u32, 'original-ttl'),
        (u32, 'signature-expiration'),
        (u32, 'time-signed'),
        (u16, 'key-footprint'),
        (Label, 'signers-name'),
        (ptype.undefined, 'signature'),
    ]

@RDATA.define
class KEY(pstruct.type):
    type = TYPE.byname('KEY'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'flags'),
        (u8, 'protocol'),
        (u8, 'algorithm'),
        (ptype.undefined, 'public-key'),
    ]

@RDATA.define
class PX(pstruct.type):
    type = TYPE.byname('PX'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'PREFERENCE'),
        (Label, 'MAP822'),
        (Label, 'MAPX400'),
    ]

@RDATA.define
class AAAA(pstruct.type):
    type = TYPE.byname('AAAA'), CLASS.byname('IN')

    _fields_ = [
        (osi.network.inet6.in_addr, 'ADDRESS'),
    ]

    def summary(self):
        return self['ADDRESS'].summary()

@RDATA.define
class LOC(pstr.string):
    type = TYPE.byname('LOC'), CLASS.byname('IN')

    class Pow10(pbinary.struct):
        _fields_ = [
            (4, 'base'),
            (4, 'power'),
        ]

    _fields_ = [
        (u8, 'VERSION'),
        (Pow10, 'SIZE'),
        (Pow10, 'HORIZ_PRE'),
        (Pow10, 'VERT_PRE'),
        (s32, 'Latitude'),
        (s32, 'Longitude'),
        (s32, 'Altitude'),
    ]

@RDATA.define
class NXT(pstruct.type):
    type = TYPE.byname('NXT'), CLASS.byname('IN')
    _fields_ = [
        (Label, 'next-domain-name'),
        (ptype.undefined, 'type-bitmap'),
    ]

@RDATA.define
class SRV(pstruct.type):
    type = TYPE.byname('SRV'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'Priority'),
        (u16, 'Weight'),
        (u16, 'Port'),
        (Label, 'Target'),
    ]

@RDATA.define
class NAPTR(pstruct.type):
    type = TYPE.byname('NAPTR'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'ORDER'),
        (u16, 'PREFERENCE'),
        (String, 'FLAGS'),
        (String, 'REGEXP'),
        (Label, 'REPLACEMENT'),
    ]

@RDATA.define
class KX(pstruct.type):
    type = TYPE.byname('KX'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'PREFERENCE'),
        (Label, 'EXCHANGER'),
    ]

@RDATA.define
class CERT(pstruct.type):
    type = TYPE.byname('CERT'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'type'),
        (u16, 'key tag'),
        (u8, 'algorithm'),
        (ptype.undefined, 'certificate or CRL'),
    ]

@RDATA.define
class A6(pstruct.type):
    type = TYPE.byname('A6'), CLASS.byname('IN')

    def __Suffix(self):
        res = 7 + self['Prefix'].li.int()
        return dyn.block(res // 8)

    _fields_ = [
        (u8, 'Prefix'),
        (__Suffix, 'Suffix'),
        (Label, 'Name'),
    ]

@RDATA.define
class DNAME(pstruct.type):
    type = TYPE.byname('DNAME'), CLASS.byname('IN')
    _fields_ = [
        (Label, 'target'),
    ]

@RDATA.define
class DS(pstruct.type):
    type = TYPE.byname('DS'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'Key Tag'),
        (u8, 'Algorithm'),
        (u8, 'Digest Type'),
        (ptype.undefined, 'Digest'),
    ]

@RDATA.define
class SSHFP(pstruct.type):
    type = TYPE.byname('SSHFP'), CLASS.byname('IN')
    _fields_ = [
        (u8, 'algorithm'),
        (u8, 'fp type'),
        (ptype.undefined, 'fingerprint'),
    ]

@RDATA.define
class IPSECKEY(pstruct.type):
    type = TYPE.byname('IPSECKEY'), CLASS.byname('IN')

    def __gateway(self):
        res = self['gateway-type'].li
        if res.int() == 0:
            return ptype.block
        elif res.int() == 1:
            return osi.network.inet4.in_addr
        elif res.int() == 2:
            return osi.network.inet6.in_addr
        elif res.int() == 3:
            return Label
        return ptype.undefined

    _fields_ = [
        (u8, 'precedence'),
        (u8, 'gateway-type'),
        (u8, 'algorithm'),
        (__gateway, 'gateway'),
        (ptype.undefined, 'public-key'),
    ]

@RDATA.define
class RRSIG(pstruct.type):
    type = TYPE.byname('RRSIG'), CLASS.byname('IN')

    _fields_ = [
        (u16, 'Type Covered'),
        (u8, 'Algorithm'),
        (u8, 'Labels'),
        (u32, 'Original TTL'),
        (u32, 'Signature Expiration'),
        (u32, 'Signature Inception'),
        (u16, 'Key Tag'),
        (Label, 'Signers Name'),
        (ptype.undefined, 'Signature'),
    ]

@RDATA.define
class NSEC(pstruct.type):
    type = TYPE.byname('NSEC'), CLASS.byname('IN')
    _fields_ = [
        (Label, 'Next Domain Name'),
        (ptype.undefined, 'Type Bit Maps'),
    ]

@RDATA.define
class DNSKEY(pstruct.type):
    type = TYPE.byname('DNSKEY'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'Flags'),
        (u8, 'Protocol'),
        (u8, 'Algorithm'),
        (ptype.undefined, 'Public Key'),
    ]

@RDATA.define
class DHCID(pstruct.type):
    type = TYPE.byname('DHCID'), CLASS.byname('IN')
    _fields_ = [
        (u16, 'Identifier type code'),
        (u8, 'Digest type code'),
        (ptype.undefined, 'Digest'),
    ]

@RDATA.define
class SPF(parray.block):
    type = TYPE.byname('SPF'), CLASS.byname('IN')
    _object_ = String

class QR(pbinary.enum):
    _width_, _values_ = 1, [
        ('query', 0),
        ('response', 1),
    ]

class OPCODE(pbinary.enum):
    _width_, _values_ = 4, [
        ('QUERY', 0),
        ('IQUERY', 1),
        ('STATUS', 2),
        ('NOTIFY', 4),
        ('UPDATE', 5),
    ]

class RCODE(pbinary.enum):
    _width_, _values_ = 4, [
        ('NOERROR', 0),
        ('SERVFAIL', 1),
        ('NXDOMAIN', 2),
        ('NOTIMP', 3),
        ('REFUSED', 4),
        ('YXDOMAIN', 5),
        ('YXRRSET', 6),
        ('NXRRSET', 7),
        ('NOTAUTH', 8),
        ('NOTZONE', 9),
    ]

class Header(pbinary.flags):
    _fields_ = [
        (QR, 'QR'),
        (OPCODE, 'OPCODE'),
        (1, 'AA'),
        (1, 'TC'),
        (1, 'RD'),
        (1, 'RA'),
        (1, 'Z'),
        (1, 'AD'),
        (1, 'CD'),
        (RCODE, 'RCODE'),
    ]

class Q(pstruct.type):
    _fields_ = [
        (Label, 'NAME'),
        (QTYPE, 'TYPE'),
        (QCLASS, 'CLASS'),
    ]

    def summary(self):
        return "{CLASS:s} {TYPE:s} {NAME:s}".format(NAME=self['NAME'].str(), TYPE=self['TYPE'].str(), CLASS=self['CLASS'].str())

class RR(pstruct.type):
    def __RDATA(self):
        res, klass = (self[fld].li.int() for fld in ['TYPE', 'CLASS'])
        try:
            t = RDATA.lookup((res, klass))

        except KeyError:
            res = self['RDLENGTH'].li
            return dyn.block(res.int())

        if issubclass(t, parray.block):
            res = self['RDLENGTH'].li
            return dyn.clone(t, blocksize=lambda _, cb=res.int(): cb)

        elif issubclass(t, (ptype.block, pstr.string)):
            return dyn.clone(t, length=self['RDLENGTH'].li.int())
        return t

    def __Padding_RDATA(self):
        res, field = self['RDLENGTH'].li, self['RDATA'].li
        return dyn.block(max(0, res.int() - field.size()))

    _fields_ = [
        (Label, 'NAME'),
        (TYPE, 'TYPE'),
        (CLASS, 'CLASS'),
        (u32, 'TTL'),
        (u16, 'RDLENGTH'),
        (__RDATA, 'RDATA'),
        (__Padding_RDATA, 'Padding(RDATA)'),
    ]

    def alloc(self, **fields):
        fields.setdefault('CLASS', 'IN')
        res = super(RR, self).alloc(**fields)
        return res.set(RDLENGtH=res['RDATA'].size())

class RRcount(pstruct.type):
    _fields_ = [
        (u16, 'QDCOUNT'),
        (u16, 'ANCOUNT'),
        (u16, 'NSCOUNT'),
        (u16, 'ARCOUNT'),
    ]

    def summary(self):
        fields = ['qd', 'an', 'ns', 'ar']
        return ', '.join("{:s}={:d}".format(name, self[fld].int()) for name, fld in zip(fields, self))

class RRset(parray.type):
    _object_ = RR

class Message(pstruct.type):
    class _Question(parray.type):
        _object_ = Q

        def summary(self):
            iterable = (item.summary() for item in self)
            return "({:d}) {:s}".format(len(self), ', '.join(iterable))

    def __Question(self):
        res = self['Counts'].li
        count = res['QDCOUNT'].int()
        return dyn.clone(self._Question, length=count)

    def __Response(field):
        def field(self, field=field):
            res = self['Counts'].li
            count = res[field].int()
            return dyn.clone(RRset, length=count)
        return field

    _fields_ = [
        (u16, 'Id'),
        (Header, 'Header'),
        (RRcount, 'Counts'),
        (__Question, 'Question'),
        (__Response('ANCOUNT'), 'Answer'),
        (__Response('NSCOUNT'), 'Authority'),
        (__Response('ARCOUNT'), 'Additional'),
        (ptype.block, 'Padding'),
    ]

class MessageTCP(pstruct.type):
    def __padding_message(self):
        res, message = (self[fld].li for fld in ['length', 'message'])
        return dyn.block(max(0, res.int() - message.size()))

    _fields_ = [
        (u16, 'length'),
        (Message, 'message'),
        (__padding_message, 'padding(message)'),
    ]

class Stream(parray.infinite):
    _object_ = MessageTCP

if __name__ == '__main__':
    import importlib
    dns = importlib.reload(dns)

    import ptypes, protocol.dns as dns
    res = 'fce2 0100 0001 0000 0000 0000 0670 6861 7474 7905 6c6f 6361 6c00 0006 0001               '
    res = 'fce2 8183 0001 0000 0001 0000 0670 6861 7474 7905 6c6f 6361 6c00 0006 0001 0000 0600 0100 000e 1000 4001 610c 726f 6f74 2d73 6572 7665 7273 036e 6574 0005 6e73 746c 640c 7665 7269 7369 676e 2d67 7273 0363 6f6d 0078 67b1 a200 0007 0800 0003 8400 093a 8000 0151 80                           '

    data = bytes.fromhex(res)

    a = dns.Message(source=ptypes.prov.bytes(data))
    a=a.l

    print(a['question'])
    print(a['question'][0]['name'])
    print(a['authority'][0])
    x = a['authority'][0]
    print(x['RDATA'])

    data = b''
    data += b"\x00\x34\xba\x0e\x00\x20\x00\x01\x00\x00\x00\x00\x00\x01\x07\x65"
    data += b"\x78\x61\x6d\x70\x6c\x65\x03\x63\x6f\x6d\x00\x00\xfc\x00\x01\x00"
    data += b"\x00\x29\x10\x00\x00\x00\x00\x00\x00\x0c\x00\x0a\x00\x08\x95\x93"
    data += b"\xf7\x69\xe7\x3f\xe5\x48"
    data += b"\x02\x1d\xba\x0e\x84\x80\x00\x01\x00\x14\x00\x00\x00\x01\x07\x65"
    data += b"\x78\x61\x6d\x70\x6c\x65\x03\x63\x6f\x6d\x00\x00\xfc\x00\x01\xc0"
    data += b"\x0c\x00\x06\x00\x01\x00\x01\x51\x80\x00\x28\x04\x64\x6e\x73\x31"
    data += b"\xc0\x0c\x0a\x68\x6f\x73\x74\x6d\x61\x73\x74\x65\x72\xc0\x0c\x77"
    data += b"\x45\xca\x65\x00\x00\x54\x60\x00\x00\x0e\x10\x00\x09\x3a\x80\x00"
    data += b"\x01\x51\x80\xc0\x0c\x00\x02\x00\x01\x00\x01\x51\x80\x00\x02\xc0"
    data += b"\x29\xc0\x0c\x00\x02\x00\x01\x00\x01\x51\x80\x00\x07\x04\x64\x6e"
    data += b"\x73\x32\xc0\x0c\xc0\x0c\x00\x0f\x00\x01\x00\x01\x51\x80\x00\x09"
    data += b"\x00\x0a\x04\x6d\x61\x69\x6c\xc0\x0c\xc0\x0c\x00\x0f\x00\x01\x00"
    data += b"\x01\x51\x80\x00\x0a\x00\x14\x05\x6d\x61\x69\x6c\x32\xc0\x0c\xc0"
    data += b"\x29\x00\x01\x00\x01\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x01\xc0"
    data += b"\x29\x00\x1c\x00\x01\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00"
    data += b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xc0\x6b\x00\x01\x00"
    data += b"\x01\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x02\xc0\x6b\x00\x1c\x00"
    data += b"\x01\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00\x00\x00\x00\x00"
    data += b"\x00\x00\x00\x00\x00\x00\x02\x03\x66\x74\x70\xc0\x0c\x00\x05\x00"
    data += b"\x01\x00\x01\x51\x80\x00\x0b\x08\x73\x65\x72\x76\x69\x63\x65\x73"
    data += b"\xc0\x0c\xc0\x80\x00\x01\x00\x01\x00\x01\x51\x80\x00\x04\x0a\x00"
    data += b"\x01\x05\xc0\x80\x00\x1c\x00\x01\x00\x01\x51\x80\x00\x10\xaa\xaa"
    data += b"\xbb\xbb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\xc0\x95"
    data += b"\x00\x01\x00\x01\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x06\xc0\x95"
    data += b"\x00\x1c\x00\x01\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00\x00"
    data += b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\xc1\x05\x00\x01\x00\x01"
    data += b"\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x0a\xc1\x05\x00\x01\x00\x01"
    data += b"\x00\x01\x51\x80\x00\x04\x0a\x00\x01\x0b\xc1\x05\x00\x1c\x00\x01"
    data += b"\x00\x01\x51\x80\x00\x10\xaa\xaa\xbb\xbb\x00\x00\x00\x00\x00\x00"
    data += b"\x00\x00\x00\x00\x00\x10\xc1\x05\x00\x1c\x00\x01\x00\x01\x51\x80"
    data += b"\x00\x10\xaa\xaa\xbb\xbb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    data += b"\x00\x11\x03\x77\x77\x77\xc0\x0c\x00\x05\x00\x01\x00\x01\x51\x80"
    data += b"\x00\x02\xc1\x05\xc0\x0c\x00\x06\x00\x01\x00\x01\x51\x80\x00\x18"
    data += b"\xc0\x29\xc0\x30\x77\x45\xca\x65\x00\x00\x54\x60\x00\x00\x0e\x10"
    data += b"\x00\x09\x3a\x80\x00\x01\x51\x80\x00\x00\x29\x10\x00\x00\x00\x00"
    data += b"\x00\x00\x1c\x00\x0a\x00\x18\x95\x93\xf7\x69\xe7\x3f\xe5\x48\x01"
    data += b"\x00\x00\x00\x5e\xe9\xba\x4a\x3e\x33\x62\x66\xee\x4a\xfc\xde"

    ptypes.setsource(ptypes.prov.bytes(data))
    z = dns.Stream()
    z=z.l

    print(z.size())
    print(z[1]['length'])
    print(z[1]['message'])
    print(z[1]['message'].size())
    x = z[1]['message']
    print(x)

    print(x['question'][0])
    print(x['answer'][20])

