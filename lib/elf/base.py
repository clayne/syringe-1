import ptypes
from ptypes import ptype,parray,pstruct,pint,pstr,dyn,pbinary
ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

### header markers
class ElfXX_File(ptype.boundary): pass
class ElfXX_Header(ptype.boundary): pass
class ElfXX_Ehdr(ElfXX_Header): pass

### base
class uchar(pint.uint8_t): pass
class ElfXX_Off(ptype.rpointer_t):
    _object_ = ptype.undefined
    def _baseobject_(self):
        return self.getparent(ElfXX_File)
    @classmethod
    def typename(cls):
        return cls.__name__
    def classname(self):
        try: type = self.d.classname() if self.initializedQ() else self._object_().classname()
        except: pass
        else: return "{:s}<{:s}>".format(self.typename(), type)

        try: type = self._object_.typename() if ptype.istype(self._object_) else self._object_().classname()
        except: pass
        else: return "{:s}<{:s}>".format(self.typename(), type)

        type = self._object_.__name__
        return "{:s}<{:s}>".format(self.typename(), type)

class ULEB128(pbinary.terminatedarray):
    class septet(pbinary.struct):
        _fields_ = [
            (1, 'more'),
            (7, 'value'),
        ]
    _object_ = septet
    def isTerminator(self, value):
        return not bool(value['more'])

    def int(self): return self.get()
    def get(self):
        res = 0
        for n in reversed(self):
            res = (res << 7) | n['value']
        return res
    def set(self, value):
        result = []
        while value > 0:
            result.append( self.new(self.septet).set((1, value & (2**7-1))) )
            value //= 2**7
        result[-1].set(more=0)
        self.value[:] = result[:]
        return self

    def summary(self):
        res = self.int()
        return "{:s} : {:d} : ({:#x}, {:d})".format(self.__element__(), res, res, 7*len(self))

### elf32
class Elf32_Addr(pint.uint32_t): pass
class Elf32_Half(pint.uint16_t): pass
class Elf32_Off(ElfXX_Off):
    _value_ = Elf32_Addr
class Elf32_Sword(pint.int32_t): pass
class Elf32_Word(pint.uint32_t): pass

### elf64
class Elf64_Addr(pint.uint64_t): pass
class Elf64_Off(ElfXX_Off):
    _value_ = Elf64_Addr
class Elf64_Half(Elf32_Half): pass
class Elf64_Word(Elf32_Word): pass
class Elf64_Sword(Elf32_Sword): pass
class Elf64_Xword(pint.uint64_t): pass
class Elf64_Sxword(pint.int64_t): pass
