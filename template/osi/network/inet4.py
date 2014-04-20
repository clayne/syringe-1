import __base__
from __base__ import layer,datalink,stackable
from ptypes import *

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass
class u_long(pint.uint32_t): pass

class in_addr(u_long): pass

@layer.define
class ip4_hdr(pstruct.type, stackable):
    type = 4

    class __ip_h(pbinary.struct):
        _fields_ = [(4,'ver'),(4,'hlen')]

    _fields_ = [
#        (u_char, 'ip_h'),
        (__ip_h, 'ip_h'),
        (u_char, 'ip_tos'),
        (u_short, 'ip_len'),
        (u_short, 'ip_id'),
        (u_short, 'ip_off'),
        (u_char, 'ip_ttl'),
        (u_char, 'ip_p'),
        (u_short, 'ip_sum'),

        (in_addr, 'ip_src'),
        (in_addr, 'ip_dst'),
    ]

    def nextlayer_id(self):
        return self['ip_p'].l.num()
    def nextlayer_size(self):
        headersize = self['ip_h'].l['hlen']*4
        return self['ip_len'].l.num() - headersize

@datalink.layer.define
class datalink_ip4(ip4_hdr):
    type = 0x0800

class ip_timestamp(pstruct.type):
    def __timestamp(self):
        l = self['ipt_len'].l.int()
        raise NotImplementedError
        n = l - 4
        return dyn.array(pint.uint32_t, n)
        
    _fields_ = [
        (u_char, 'ipt_code'),
        (u_char, 'ipt_len'),
        (u_char, 'ipt_ptr'),
        (u_char, 'ipt_flg/ipt_oflw'),
        (__timestamp, 'ipt_timestamp'),
    ]
