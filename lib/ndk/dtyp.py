import ndk
from ptypes import *
from ndk.WinNT import *

class int8(pint.sint8_t): pass
class int16(pint.sint16_t): pass
class int32(pint.sint32_t): pass
class int64(pint.sint64_t): pass

class hyper(dynamic.union):
    _fields_ = [
        (pint.sint64_t, 'signed'),
        (pint.uint64_t, 'unsigned'),
    ]

class BYTE(pint.uint8_t): pass
class UCHAR(pstr.char_t): pass
class CHAR(pstr.char_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class DWORD_PTR(PVOID): pass
class SHORT(pint.sint16_t): pass
class USHORT(pint.uint16_t): pass
class INT(pint.sint32_t): pass
class UINT(pint.uint32_t): pass
class LONG(pint.int32_t): pass
class ULONG(pint.uint32_t): pass
class LONG_PTR(PVOID): pass
class ULONG_PTR(PVOID): pass
class LONGLONG(pint.sint64_t): pass
class ULONGLONG(pint.uint64_t): pass
class INT8(pint.sint8_t): pass
class INT16(pint.sint16_t): pass
class INT32(pint.sint32_t): pass
class INT64(pint.sint64_t): pass
class UINT8(pint.uint8_t): pass
class UINT16(pint.uint16_t): pass
class UINT32(pint.uint32_t): pass
class UINT64(pint.uint64_t): pass
class LONG32(pint.sint32_t): pass
class LONG64(pint.sint64_t): pass
class ULONG32(pint.uint32_t): pass
class ULONG64(pint.uint64_t): pass
class octet(pint.uint8_t): pass
class BOOL(pint.uint32_t): pass
class BOOLEAN(BYTE): pass
class QWORD(int64): pass

class BSTR(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'length'),
        (lambda s: dyn.clone(pstr.wstring, length=s['length'].li.int()), 'string')
    ]

class DOUBLE(pfloat.double): pass
class FLOAT(pfloat.single): pass

class DWORD32(pint.uint32_t): pass
class DWORD64(pint.uint64_t): pass
class DWORDLONG(ULONGLONG): pass
class error_status_t(pint.uint32_t): pass

class HANDLE(PVOID): pass
class HCALL(DWORD): pass

class HRESULT(dynamic.union):
    class hresult(pbinary.struct):
        _fields_ = [
            (1, 'severity'),
            (4, 'reserved'),
            (11, 'facility'),
            (16, 'code'),
        ]
    _fields_ = [
        (LONG, 'result'),
        (hresult, 'hresult'),
    ]

class LMCSTR(pstr.szwstring): pass
class LMSTR(pstr.szwstring): pass
class LPCSTR(pointer(pstr.szstring)): pass
class LPCWSTR(pointer(pstr.szwstring)): pass
class LPWSTR(pointer(pstr.szwstring)): pass
class LPCVOID(PVOID): pass
class NET_API_STATUS(DWORD): pass
class NTSTATUS(LONG): pass
class PCONTEXT_HANDLE(PVOID): pass
class RPC_BINDING_HANDLE(PVOID): pass

class UNICODE(pstr.wchar_t): pass
class STRING(pstr.szstring): pass
class WCHAR(pstr.wchar_t): pass
class UNC(STRING): pass

class EVENT_DESCRIPTOR(pstruct.type):
    _fields_ = [
        (USHORT, 'Id'),
        (UCHAR, 'Version'),
        (UCHAR, 'Channel'),
        (UCHAR, 'Level'),
        (UCHAR, 'Opcode'),
        (USHORT, 'Task'),
        (ULONGLONG, 'Keyword'),
    ]

class EVENT_HEADER(pstruct.type):
    class Time(dynamic.union):
        class UserTime(pstruct.type): _fields_ = [(ULONG,name) for name in ('Kernel','User')]
        _fields_ = [
            (UserTime, 'System'),
            (ULONG64, 'Processor'),
        ]
    _fields_ = [
        (USHORT, 'Size'),
        (USHORT, 'HeaderType'),
        (USHORT, 'Flags'),
        (USHORT, 'EventProperty'),
        (ULONG, 'ThreadId'),
        (ULONG, 'ProcessId'),
        (ndk.LARGE_INTEGER, 'TimeStamp'),
        (GUID, 'ProviderId'),
        (EVENT_DESCRIPTOR, 'EventDescriptor'),
        (Time, 'Time'),
        (GUID, 'ActivityId'),
    ]

CLSID = UUID = GUID = ndk.GUID

class FILETIME(pstruct.type):
    _fields_ = [
        (DWORD, 'dwLowDateTime'),
        (DWORD, 'dwHighDateTime')
    ]
    def timestamp(self):
        low, high = self['dwLowDateTime'].int(), self['dwHighDateTime'].int()
        return high * 0x100000000 | + low
    def datetime(self):
        epoch = datetime.datetime(1601, 1, 1)
        return epoch + datetime.timedelta(microseconds=self.timestamp() / 10.0)
    def summary(self):
        epoch, ts = datetime.datetime(1601, 1, 1), self.timestamp()
        ts_s, ts_hns = ts // 1e7, ts % 1e7
        ts_ns = ts_hns * 1e-7

        res = epoch + datetime.timedelta(seconds=ts_s)
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:s} ({:#x})".format(res.year, res.month, res.day, res.hour, res.minute, "{:02.9f}".format(res.second + ts_ns).zfill(12), ts)

class LARGE_INTEGER(pstruct.type):
    _fields_ = [
        (pint.sint64_t, 'QuadPart'),
    ]

class ACCESS_MASK(pbinary.struct):
    _fields_ = [
        (1, 'Generic Read (GR)'),
        (1, 'Generic Write (GW)'),
        (1, 'Generic Execute (GX)'),
        (1, 'Generic All (GA)'),
        (2, 'Reserved'),
        (1, 'Maximum Allowed (MA)'),
        (1, 'Access System Security (AS)'),
        (3, 'Reserved'),
        (1, 'Synchronize (SY)'),
        (1, 'Write Owner (WO)'),
        (1, 'Write DACL (WD)'),
        (1, 'Read Control (RC)'),
        (1, 'Delete (DE)'),
        (16, 'Implementation'),
    ]

class LCID(DWORD): pass

class LUID(pstruct.type):
    _fields_ = [
        (DWORD, 'LowPart'),
        (DWORD, 'HighPart'),
    ]

class MULTI_SZ(pstruct.type):
    class StringsValue(parray.block):
        _object_ = pstr.szwstring
        def isTerminator(self, value):
            return value.str() == ''
        def blocksize(self):
            res = self.getparent(MULTI_SZ)
            return res['nChar'].li.int()
    _fields_ = [
        (pointer(lambda s: s.getparent(MULTI_SZ).StringsValue), 'Value'),
        (DWORD, 'nChar'),
    ]

class OBJECT_TYPE_LIST(pstruct.type):
    _fields_ = [
        (WORD, 'Level'),
        (ACCESS_MASK, 'Remaining'),
        (pointer(GUID), 'ObjectType'),
    ]

class SYSTEMTIME(pstruct.type):
    _fields_ = [
        (WORD, 'wYear'),
        (WORD, 'wMonth'),
        (WORD, 'wDayOfWeek'),
        (WORD, 'wDay'),
        (WORD, 'wHour'),
        (WORD, 'wMinute'),
        (WORD, 'wSecond'),
        (WORD, 'wMilliseconds'),
    ]

class UINT128(pstruct.type):
    _fields_ = [
        (UINT64, 'lower'),
        (UINT64, 'upper'),
    ]

class ULARGE_INTEGER(pstruct.type):
    _fields_ = [
        (pint.uint64_t, 'QuadPart'),
        (UINT64, 'upper'),
    ]

### Security Descriptor Related Things
class SID_IDENTIFIER_AUTHORITY(parray.type):
    length = 6
    _object_ = pint.uint8_t

    def summary(self):
        return '{' + ','.join(str(x.int()) for x in self) + '}'

class SID(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'Revision'),
        (pint.uint8_t, 'SubAuthorityCount'),
        (SID_IDENTIFIER_AUTHORITY, 'IdentifierAuthority'),
        (lambda s: dyn.array(pint.uint32_t,s['SubAuthorityCount'].li.int()), 'SubAuthority'),
    ]

class ACE_HEADER(pstruct.type):
    class AceType(pint.enum, pint.uint8_t): _values_ = []
    class AceFlags(pbinary.flags): _fields_ = [(32,'Flags')]
    _fields_ = [
        (AceType, 'AceType'),
        (AceFlags, 'AceFlags'),
        (pint.uint16_t, 'AceSize'),
    ]

class ACCESS_ALLOWED_ACE(pstruct.type):
    _fields_ = [
        (ACE_HEADER, 'Header'),
        (ACCESS_MASK ,'Mask'),
        (SID, 'Sid'),
    ]

class ACCESS_ALLOWED_OBJECT_ACE(pstruct.type):
    _fields_ = [
        (ACE_HEADER, 'Header'),
        (ACCESS_MASK ,'Mask'),
        (pint.uint32_t, 'Flags'),
        (GUID, 'ObjectType'),
        (GUID, 'InheritedObjectType'),
        (SID, 'Sid'),
    ]

class ACCESS_DENIED_ACE(pstruct.type):
    _fields_ = [
        (ACE_HEADER, 'Header'),
        (ACCESS_MASK ,'Mask'),
        (SID, 'Sid'),
    ]

class ACCESS_DENIED_OBJECT_ACE(pstruct.type):
    _fields_ = [
        (ACE_HEADER, 'Header'),
        (ACCESS_MASK ,'Mask'),
        (pint.uint32_t, 'Flags'),
        (GUID, 'ObjectType'),
        (GUID, 'InheritedObjectType'),
        (SID, 'Sid'),
    ]

class ACCESS_ALLOWED_CALLBACK_ACE(pstruct.type):
    _fields_ = [
        (ACE_HEADER, 'Header'),
        (ACCESS_MASK ,'Mask'),
        (SID, 'Sid'),
        (lambda s: dyn.block(s['Header'].li['AceSize'].int()), 'ApplicationData'),
    ]

# TODO: Implement the rest of the ACCESS_ and SYSTEM_ constructed security types