from . import ptype,parray,pstruct,pbinary,pint,pfloat,pstr,config,utils,dyn,provider
prov = provider

## globally changing the ptype provider
def setsource(prov):
    '''Sets the default ptype provider to the one specified'''
#    assert issubclass(prov.__class__, prov.provider), 'Needs to be of type %s'% repr(prov.provider)
    prov.seek
    prov.consume
    prov.store
    ptype.type.source = prov

## globally changing the byte order
bigendian,littleendian = config.byteorder.bigendian,config.byteorder.littleendian
def setbyteorder(endianness):
    '''
        _Globally_ sets the integer byte order to the endianness specified.
        can be either config.byteorder.bigendian or config.byteorder.littleendian
    '''
    ptype.setbyteorder(endianness)
    pint.setbyteorder(endianness)
    pbinary.setbyteorder(endianness)

## some things people people might find useful
from ptype import debug,debugrecurse
from ptype import istype,iscontainer

from provider import file,memory
from utils import hexdump

## default to byte order detected by python
setbyteorder( config.defaults.integer.order )

if __name__ == '__main__':
    import __init__ as ptypes
    class a(ptypes.ptype.type):
        length = 4

    data = '\x41\x41\x41\x41'

    import ctypes
    b = ctypes.cast(ctypes.pointer(ctypes.c_buffer(data,4)), ctypes.c_void_p)

    ptypes.setsource(ptypes.prov.memory())
    print 'ptype-class-memory', type(ptypes.ptype.type.source) == ptypes.prov.memory
    print 'ptype-instance-memory', type(ptypes.ptype.type().source) == ptypes.prov.memory
    c = a(offset=b.value).l
    print 'type-instance-memory', c.serialize() == data

    ptypes.setsource(ptypes.prov.empty())
    print 'ptype-class-empty', type(ptypes.ptype.type.source) == ptypes.prov.empty
    print 'ptype-instance-empty', type(ptypes.ptype.type().source) == ptypes.prov.empty
    c = a(offset=b.value).l
    print 'type-instance-empty', c.serialize() == '\x00\x00\x00\x00'
    ptypes.setsource(ptypes.prov.memory())
