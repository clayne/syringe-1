import ptypes
from ptypes import *
# ripped from https://common.helixcommunity.org/2003/HCS_SDK_r5/htmfiles/rmff.htm

class UINT32( pint.bigendian(pint.uint32_t) ): pass
class UINT16( pint.bigendian(pint.uint16_t) ): pass
class UINT8( pint.bigendian(pint.uint8_t) ): pass
class INT32( pint.bigendian(pint.int32_t) ): pass
class ULONG32( pint.bigendian(pint.uint32_t) ): pass

class Str8(pstruct.type):
    _fields_ = [
        (UINT8, 'len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['len'].l)), 's')
    ]
    def __str__(self):
        return str(self['s'])

### General Types
class RealMedia_Header(pstruct.type):
    def getobject(self):
        id = self['object_id'].l.serialize()
        ver = int(self['object_version'].l)

        lookup = globals()['RealMedia_Header_Lookup']
        try:
            res = lookup[ (id,ver) ]
        except KeyError:
            res = dyn.block( int(self['size'].l) - 10 )
        return res

    def figureextra(s):
        l = int(s['size'].l)
        s = s['object'].size() + 4 + 4 + 2
        if l > s:
            print 'hit some untested code'
            return dyn.block( l - s )
        return dyn.block(0)

    def size(self):
        l = int(self['size'])
        return l

    _fields_ = [
        (UINT32, 'object_id'),
        (UINT32, 'size'),
        (UINT16, 'object_version'),
        (getobject, 'object'),
        (figureextra, 'extra')
    ]

class RealMedia_Header_Type(object): pass

class RealMedia_Structure(pstruct.type):
    def getobject(self):
        ver = int(self['object_version'].l)
        return self._object_[ver]

    _fields_ = [
        (ULONG32, 'size'),
        (UINT16, 'object_version'),
        (getobject, 'object'),
    ]

class RealMedia_Record(pstruct.type):
    def getobject(self):
        ver = int(self['object_version'].l)
        return self._object_[ver]

    _fields_ = [
        (UINT16, 'object_version'),
        (getobject, 'object')
    ]

### non general types
## type specific
# http://git.ffmpeg.org/?p=ffmpeg;a=blob;f=libavformat/rmdec.c;h=436a7e08f2a593735d50e15ba38ed34c5f8eede1;hb=HEAD

class Type_Specific_v3(pstruct.type):
    object_verison = 3
    _fields_ = [
        (dyn.block(14), 'unknown[1]'),  # XXX: this might not be right
        (Str8, 'metadata'),
        (UINT8, 'unknown[3]'),
        (Str8, 'fourcc'),
    ]

class Type_Specific_v4(pstruct.type):
    object_version = 4
    _fields_ = [
        (UINT16, 'unused[0]'),
        (UINT32, '.ra4'),
        (UINT32, 'data_size'),
        (UINT16, 'version2'),
        (UINT32, 'header_size'),
        (UINT16, 'flavor'),
        (UINT32, 'coded_frame_size'),
        (UINT32, 'unknown[7]'),
        (UINT32, 'unknown[8]'),
        (UINT32, 'unknown[9]'),
        (UINT16, 'sub_packet_h'),
        (UINT16, 'frame_size'),
        (UINT16, 'sub_packet_size'),
        (UINT16, 'unknown[d]'),
        (UINT16, 'sample_rate'),
        (UINT32, 'unknown[f]'),
        (UINT16, 'channels'),
        (Str8, 'desc1'),
        (Str8, 'desc2'),
    ]

class Type_Specific_vAny(Type_Specific_v4): pass

class Type_Specific_v5(pstruct.type):
    object_version = 5
    _fields_ = [
        (UINT16, 'unused[0]'),
        (UINT32, '.ra5'),
        (UINT32, 'data_size'),
        (UINT16, 'version2'),
        (UINT32, 'header_size'),
        (UINT16, 'flavor'),
        (UINT32, 'coded_frame_size'),
        (UINT32, 'unknown[7]'),
        (UINT32, 'unknown[8]'),
        (UINT32, 'unknown[9]'),
        (UINT16, 'sub_packet_h'),
        (UINT16, 'frame_size'),
        (UINT16, 'sub_packet_size'),
        (UINT16, 'unknown[d]'),
        (UINT16, 'unknown[e]'),
        (UINT16, 'unknown[f]'),
        (UINT16, 'unknown[10]'),
        (UINT16, 'sample_rate'),
        (UINT32, 'unknown[12]'),
        (UINT16, 'channels'),
        (UINT32, 'unknown[14]'),
        (dyn.block(4), 'buffer'),
    ]

class Type_Specific(pstruct.type):
    _object_ = {
        0 : Type_Specific_vAny,
        3 : Type_Specific_v3,
        4 : Type_Specific_v4,
        5 : Type_Specific_v5
    }

    def getobject(self):
        ver = int(self['object_version'].l)
        try:
            return self._object_[ver]
        except KeyError:
            pass
        return ptype.type

    def figurecodec(s):
        h = s.getparent(RealMedia_Header_Type)
        l = int(h['type_specific_len'].l)
        if l > 0:
            return dyn.block( l - (s['object'].size()+6) )
        return dyn.block(0)

    _fields_ = [
        (UINT32, 'object_id'),
        (UINT16, 'object_version'),
        (getobject, 'object'),
#        (lambda s: dyn.block( int(s['object'].l['header_size']) - (s['object'].size() + 6)), 'codec?')
        (figurecodec, 'codec?')
    ]

### sub-headers
class RealMedia_File_Header_v0(pstruct.type, RealMedia_Header_Type):
    object_id = '.RMF'
    object_version = 0
    _fields_ = [
        (UINT32, 'file_version'),
        (UINT32, 'num_headers'),
    ]
    
class RealMedia_File_Header_v1(RealMedia_File_Header_v0):
    object_version = 1

class RealMedia_Properties_Header_v0(pstruct.type, RealMedia_Header_Type):
    object_id = 'PROP'
    object_version = 0
    _fields_ = [
        (UINT32, 'max_bit_rate'),
        (UINT32, 'avg_bit_rate'),
        (UINT32, 'max_packet_size'),
        (UINT32, 'avg_packet_size'),
        (UINT32, 'num_packets'),
        (UINT32, 'duration'),
        (UINT32, 'preroll'),
        (UINT32, 'index_offset'),
        (UINT32, 'data_offset'),
        (UINT16, 'num_streams'),
        (UINT16, 'flags'),
    ]

class RealMedia_MediaProperties_Header_v0(pstruct.type, RealMedia_Header_Type):
    object_id = 'MDPR'
    object_version = 0
    _fields_ = [
        (UINT16, 'stream_number'),
        (UINT32, 'max_bit_rate'),
        (UINT32, 'avg_bit_rate'),
        (UINT32, 'max_packet_size'),
        (UINT32, 'avg_packet_size'),
        (UINT32, 'start_time'),
        (UINT32, 'preroll'),
        (UINT32, 'duration'),
        (UINT8, 'stream_name_size'),
        (lambda s: dyn.clone(pstr.string, length=int(s['stream_name_size'].l)), 'stream_name'),
        (UINT8, 'mime_type_size'),
        (lambda s: dyn.clone(pstr.string, length=int(s['mime_type_size'].l)), 'mime_type'),
        (UINT32, 'type_specific_len'),
#        (lambda s: dyn.block(int(s['type_specific_len'].l)), 'type_specific_data'),
        (Type_Specific, 'type_specific_data')
    ]

class RealMedia_Content_Description_Header(pstruct.type, RealMedia_Header_Type):
    object_id = 'CONT'
    object_version = 0

    _fields_ = [
        (UINT16, 'title_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['title_len'].l)), 'title'),
        (UINT16, 'author_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['author_len'].l)), 'author'),
        (UINT16, 'copyright_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['copyright_len'].l)), 'copyright'),
        (UINT16, 'comment_len'),
        (lambda s: dyn.clone(pstr.string, length=int(s['comment_len'].l)), 'comment'),
    ]

class RealMedia_Data_Chunk_Header(pstruct.type, RealMedia_Header_Type):
    object_id = 'DATA'
    object_version = -1
    _fields_ = [
        (UINT32, 'num_packets'),
        (UINT32, 'next_data_header'),
        (lambda s: dyn.array( Media_Packet_Header_v0, int(s['num_packets'].l) ), 'packets')
    ]

class RealMedia_Index_Chunk_Header(pstruct.type, RealMedia_Header_Type):
    object_id = 'INDX'
    object_version = 0
    _fields_ = [
        (UINT32, 'num_indices'),
        (UINT16, 'stream_number'),
        (UINT32, 'next_index_header'),
        (lambda s: dyn.array( IndexRecord, int(s['num_indices'].l) ), 'packets')
    ]

### logical stream structures
class LogicalStream_v0(RealMedia_Structure):
    object_version = 0
    _fields_ = [
        (UINT16, 'num_physical_streams'),
        (lambda s: dyn.array(UINT16, int(s['num_physical_streams'].l)), 'physical_stream_numbers'),
        (lambda s: dyn.array(ULONG32, int(s['num_physical_streams'].l)), 'data_offsets'),
        (UINT16, 'num_rules'),
        (lambda s: dyn.array(UINT16, int(s['num_rules'].l)), 'rule_to_physical_stream_number_map'),
        (UINT16, 'num_properties'),
        (lambda s: dyn.array(NameValueProperty, int(s['num_properties'].l)), 'properties'),
    ]

class LogicalStream(RealMedia_Structure):
    _object_ = { 0 : LogicalStream_v0 }

class NameValueProperty_v0(pstruct.type):
    _fields_ = [
        (UINT8, 'name_length'),
        (lambda s: dyn.clone(pstr.string, length=int(s['name_length'].l)), 'name'),
        (INT32, 'type'),
        (UINT16, 'value_length'),
        (lambda s: dyn.block(int(s['value_length'])), 'value_data')
    ]

class NameValueProperty(RealMedia_Structure):
    _object_ = { 0 : NameValueProperty_v0 }

### data packets
class Media_Packet_Header_v0(pstruct.type):
    _fields_ = [
        (UINT16, 'length'),
        (UINT16, 'stream_number'),
        (UINT32, 'timestamp'),
        (UINT8, 'packet_group'),
        (UINT8, 'flags'),
        (lambda s: dyn.block( int(s['length'].l) ), 'data'),
    ]

class Media_Packet_Header_v1(pstruct.type):
    _fields_ = [
        (UINT16, 'length'),
        (UINT16, 'stream_number'),
        (UINT32, 'timestamp'),
        (UINT16, 'asm_rule'),
        (UINT8, 'asm_flags'),
        (lambda s: dyn.block( int(s['length'].l) ), 'data'),
    ]

class Media_Packet_Header(RealMedia_Record):
    _object_ = { 0 : Media_Packet_Header_v0, 1 : Media_Packet_Header_v1 }

### index records
class IndexRecord_v0(pstruct.type):
    _fields_ = [
        (UINT32, 'timestamp'),
        (UINT32, 'offset'),
        (UINT32, 'packet_count_for_this_packet'),
    ]

class IndexRecord(RealMedia_Record):
    _object_ = { 0 : IndexRecord_v0 }

### make search lists
def getparentclasslookup(parent, key):
    import inspect
    res = {}
    for cls in globals().values():
        if inspect.isclass(cls) and cls is not parent and issubclass(cls, parent):
            res[ key(cls) ] = cls
        continue
    return res

RealMedia_Header_Lookup = getparentclasslookup(RealMedia_Header_Type, lambda cls: (cls.object_id, cls.object_version))

###
class File(parray.terminated):
    _object_ = RealMedia_Header

    def isTerminator(self, value):
        l = len(self.value)
        if l > 0:
            return l > int(self.value[0]['object']['num_headers']) + 1
        return False

if __name__ == '__main__':
    ptypes.setsource( provider.file('./poc.rma', mode='rb') )

    self = File()   
    self.l
    print len(self.value)

    offset = 0x16f
    print self.at(offset)

    typespecific = self[3]['object']['type_specific_data']
