#http://fxr.watson.org/fxr/source/include/linux/ipv6.h?v=linux-2.6
# used linux this time because fbsd's headers don't make immediate sense..
# http://www.ietf.org/rfc/rfc2460.txt

# FIXME: this was broken during the layer/stackable refactor.

import ptypes, functools
from ptypes import *

import ptypes.bitmap as bitmap
from . import layer, stackable, terminal, datalink
from . import address, utils

class ip6layer(layer):
    cache = {}
class ip6stackable(stackable):
    _layer_ = ip6layer

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_int32_t(pint.uint32_t): pass
class u_int16_t(pint.uint16_t): pass
class u_int8_t(pint.uint8_t): pass
class in6_addr(address.in6_addr): pass
in_addr = address.in6_addr

@layer.define(type = 41)    # protocol number
@datalink.layer.define
class ip6_hdr(pstruct.type, stackable):
    type = 0x86dd

    def __ip6_nxt(self):
        from .. import transport
        # FIXME: these enumerations could be better organized.
        class ip6_nxt(transport.layer.enum, u_int8_t):
            pass
        return ip6_nxt

    _fields_ = [
        (u_int32_t, 'ip6_flow'),
        (u_int16_t, 'ip6_plen'),
        #(u_int8_t, 'ip6_nxt'),
        (__ip6_nxt, 'ip6_nxt'),
        (u_int8_t, 'ip6_hlim'),
        (in6_addr, 'saddr'),
        (in6_addr, 'daddr'),
    ]

    def layer(self):
        layer, id, remaining = super(ip6_hdr, self).layer()
        res = self['ip6_nxt'].li
        if res == 0:
            return layer, ip6_exthdr_hop, self['ip6_plen'].int()
        return layer, res.int(), self['ip6_plen'].int()

class ip6_opt(pstruct.type):
    def __ip6_len(self):
        type = self['ip6o_type'].li.int()
        return [u_int8_t, pint.int_t][type == 0]   # for Pad0

    def __ip6o_payload(self):
        t, size = self['ip6o_type'].li.int(), self['ip6o_len'].li.int()
        return Option.withdefault(t, blocksize=lambda s:size)

    _fields_ = [
        (u_int8_t,'ip6o_type'),
        (__ip6_len,'ip6o_len'),
        (__ip6o_payload, 'ip6o_payload'),
    ]

class ip6_exthdr(pstruct.type, ip6stackable):
    type = None

    def __ip6_payload(self):
        t = self['ip6_nxt'].li.int()
        size = self['ip6_len'].li.int() - 2
        result = layer.withdefault(self.type, length=size)
        return dyn.clone(result, blocksize=lambda s:size)

    def __ip6_nxt(self):
        from .. import transport
        # FIXME: these enumerations could be better organized.
        class ip6_nxt(transport.layer.enum, u_int8_t):
            pass
        return ip6_nxt

    _fields_ = [
        #(u_int8_t, 'ip6_nxt'),
        (__ip6_nxt, 'ip6_nxt'),
        (u_int8_t, 'ip6_len'),
        (__ip6_payload, 'ip6_payload'),
    ]

    def layer(self):
        layer, id, remaining = super(ip6_hdr, self).layer()
        protocol = self['ip6_nxt'].li
        return layer, protocol, 8 + self['ip6_len'].li.int()

    def blocksize(self):
        return 8 + self['ip6_len'].li.int()

### options
if True:
    class Option(ptype.definition):
        cache = {}

    @Option.define
    class ip6_opt_pad1(ptype.block):
        type = 0
        length = 0

    @Option.define
    class ip6_opt_padN(ptype.block):
        type = 1

    @Option.define
    class ip6_opt_jumbo(pstruct.type):
        type = 0xc2
        _fields_ = [
            (dyn.array(u_int8_t,4),'ip6oj_jumbo_len')
        ]

    @Option.define
    class ip6_opt_nsap(pstruct.type):
        type = 0xc3
        _fields_ = [
            (u_int8_t, 'ip6on_src_nsap_len'),
            (u_int8_t, 'ip6on_dst_nsap_len'),
            (lambda s: dyn.block(self['ip6on_src_nsap_len'].li.int()), 'ip6on_src_nsap'),
            (lambda s: dyn.block(self['ip6on_dst_nsap_len'].li.int()), 'ip6on_dst_nsap'),
        ]

    @Option.define
    class ip6_opt_tunnel(pstruct.type):
        type = 0x04
        _fields_ = [
            (u_int8_t, 'ip6ot_encap_limit'),
        ]

    @Option.define
    class ip6_opt_router(pstruct.type):
        type = 0x05
        _fields_ = [
            (dyn.array(u_int8_t,2), 'ip6or_value'),
        ]

### extension-headers
# FIXME: some of these option headers have dynamically calculated fields,
#        but are missing the calculation in the definition for the field.
if True:
    class ip6_hbh(parray.block):
        '''hop-to-hop option array'''
        _object_ = ip6_opt

    class ip6_exthdr_hop(ip6_exthdr):
        def __ip6_payload(self):
            size = self.blocksize() - 2
            return dyn.clone(ip6_hbh, blocksize=lambda s:size)

        def __ip6_nxt(self):
            from .. import transport
            # FIXME: these enumerations could be better organized.
            class ip6_nxt(transport.layer.enum, u_int8_t):
                pass
            return ip6_nxt

        _fields_ = [
            #(u_int8_t, 'ip6_nxt'),
            (__ip6_nxt, 'ip6_nxt'),
            (u_int8_t, 'ip6_len'),
            (__ip6_payload, 'ip6_payload'),
        ]

    @ip6layer.define
    class ip6_rthdr(pstruct.type):
        type = 43
        _fields_ = [
            (u_int8_t, 'ip6r_type'),
            (u_int8_t, 'ip6r_segleft'),
        ]

    #@ip6layer.define
    #class ip6_rthdr0(pstruct.type):
    #    # XXX: this header is not in the rfc because it has been deprecated
    #    type = 43
    #    _fields_ = [
    #        (u_int8_t, 'ip6r0_type'),
    #        (u_int8_t, 'ip6r0_segleft'),
    #        (u_int32_t, 'ip6r0_reserved'),
    #    ]

    #    # XXX followed by up to 127 struct in6_addr

    @ip6layer.define
    class ip6_frag(pstruct.type):
        type = 44
        _fields_ = [
            (u_int16_t, 'ip6f_offlg'),
            (u_int32_t, 'ip6f_ident'),
        ]

    @ip6layer.define
    class ip6_nomoreheaders(ptype.type):
        type = 59

    ####
    @ip6layer.define
    class ip6_dest(parray.block):
        type = 60
        _object_ = ip6_opt

## regular ipv6 protocols
@ip6layer.define
class icmp6_hdr(pstruct.type):
    type = 58
    _fields_ = [
        (u_int8_t, 'icmp6_type'),
        (u_int8_t, 'icmp6_code'),
        (u_int16_t, 'icmp6_cksum'),
        (dyn.block(4), 'icmp6_data')
    ]

header = ip6_hdr
