import six, functools, ptypes
from ptypes import *
ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class pQTInt(pint.bigendian(pint.uint32_t)): pass
class pQTType(pQTInt):
    def summary(self):
        if self.value:
            return "%s '%c%c%c%c' (%08x)"% ( self.name(), self.value[0], self.value[1], self.value[2], self.value[3], int(self) )
        return "%s uninitialized"%(self.name())

    def __cmp__(self, x):
        if isinstance(x, six.string_types):
            return cmp('%c%c%c%c'% tuple(self.value[:4]), x)
        return cmp(int(self), x)

    def set(self, value):
        return super(pQTType,self).set( functools.reduce(lambda x,y:x*0x100+ord(y), value, 0) )

class Fixed(pfloat.ufixed_t):
    fractional,length = 16,4

class Matrix(pstruct.type):
    _fields_ = [
        (Fixed, 'a'),
        (Fixed, 'b'),
        (Fixed, 'u'),
        (Fixed, 'c'),
        (Fixed, 'd'),
        (Fixed, 'v'),
        (Fixed, 'Tx'),
        (Fixed, 'Ty'),
        (Fixed, 'w'),
    ]

class pQTString(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'c'),
        (lambda s: dyn.clone(pstr.string, length=int(s['c'].li)), 's'),
    ]

    def str(self):
        return self['s'].str()
