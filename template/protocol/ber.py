import sys, logging, math, codecs, operator, builtins, itertools, functools
import ptypes, ptypes.bitmap as bitmap, ptypes.utils as utils
from ptypes import *
integer_types, string_types = ptypes.integer_types, ptypes.string_types

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### Primitive types for records
class IdentifierLong(pbinary.terminatedarray):
    class _object_(pbinary.struct):
        _fields_ = [
            (1, 'continue'),
            (7, 'integer'),
        ]

    def isTerminator(self, value):
        return value['continue'] == 0

    def int(self):
        '''Return the integer from the structure'''
        return functools.reduce(lambda t, item: (t * pow(2,7)) | item['integer'], self, 0)

    def set(self, *integer, **fields):
        '''Apply the specified integer to the structure'''
        if len(integer) == 1 and isinstance(integer[0], integer_types):
            integer, = integer

            # calculate the number of 7-bit pieces for our integer
            res = math.floor(math.log(integer) / math.log(pow(2,7)) + 1)
            length = fields.pop('length', math.trunc(res))

            # slice the integer into 7-bit pieces. we could use ptypes.bitmap, but
            # that requires reading documentation and things. so let's avoid that.
            res = []
            while integer > 0:
                res.insert(0, integer & (pow(2,7) - 1))
                integer >>= 7

            # append any extra zeroes in order to pad the list to the specified length
            res = [0] * (length - len(res)) + res
            return self.alloc(length=length).set([[1, item] for item in res[:-1]] + [[0, res[-1]]])
        return super(IdentifierLong, self).set(*integer, **fields)

class Length(pbinary.struct):
    '''Indefinite Length (short form) 8.1.3.3'''
    def __value(self):
        return (8 * self['count']) if self['form'] else 0

    _fields_ = [
        (1, 'form'),
        (7, 'count'),
        (__value, 'value'),
    ]

    def int(self):
        '''Return the length from the structure'''
        return self['value'] if self['form'] else self['count']

    def set(self, *integer, **fields):
        '''Apply the specified length to the structure'''
        if len(integer) == 1 and isinstance(integer[0], integer_types):
            integer, = integer

            # if our integer can be fit within 7 bits, then just assign it to 'count'
            if integer < pow(2,7):
                return self.alloc(form=0).set(count=integer)

            # otherwise, figure out how many bytes we need to allocate and then
            # simply assign the integer to them
            res = math.floor(math.log(integer) / math.log(pow(2,8)) + 1)
            return self.alloc(form=1, count=math.trunc(res)).set(value=integer)
        return super(Length, self).set(*integer, **fields)

    def IndefiniteQ(self):
        '''Return whether the contents will be terminated by an EOC tag.'''
        if not self.initializedQ():
            raise ptypes.error.InitializationError(self, 'IndefiniteQ')
        return (self['form'], self['count']) == (1, 0)

    def summary(self):
        res = self.int()
        return '{:d} ({:#x}) -- {:s}'.format(res, res, super(Length, self).summary()) + (' Indefinite' if self.IndefiniteQ() else '')

class Tag(pbinary.struct):
    def __TagLong(self):
        return IdentifierLong if self['TagShort'] == 0x1f else dyn.clone(IdentifierLong, length=0)

    _fields_ = [
        (5, 'TagShort'),
        (__TagLong, 'TagLong'),
    ]

    def int(self):
        '''Return the tag number based on the values in our fields'''
        if self['TagShort'] < pow(2,5) - 1:
            return self['TagShort']
        return self['TagLong'].int()

    def set(self, *integer, **fields):
        '''Apply the tag number to the structure'''
        if len(integer) == 1 and isinstance(integer[0], integer_types):
            integer, = integer
            return self.alloc(TagShort=integer) if integer < pow(2,5) - 1 else self.alloc(TagShort=pow(2,5) - 1).set(TagLong=integer)
        return super(Tag, self).set(*integer, **fields)

    def summary(self):
        res = self.int()
        return '{:d} ({:#x}) -- {:s}'.format(res, res, super(Tag, self).summary())

class Type(pbinary.struct):
    _fields_ = [
        (2, 'Class'),
        (1, 'Constructed'),
        (Tag, 'Tag'),
    ]

    def summary(self):
        klass, constructedQ, tag = self['Class'], self['Constructed'], self['Tag'].int()
        return 'class:{:d} tag:{:d} {:s}'.format(klass, tag, 'Constructed' if constructedQ else 'Universal')

class Constructed(parray.block):
    __object_state__ = None

    @classmethod
    def typename(cls):
        if hasattr(cls, 'type'):
            klass, tag = (Context.Class, cls.type) if isinstance(cls.type, integer_types) else cls.type
            return "{:s}<{:d},{:d}>".format(cls.__name__, getattr(klass, 'Class', klass), tag)
        return super(Constructed, cls).typename()

    def load(self, **attrs):
        cls = self.__class__

        # Allocate the lookup table so that we can assign it to ourself
        # while loading. This ties directly into the _object_ method
        # which determines each object to use.
        table, _ = self.__get_lookup_table__()
        with utils.assign(self, __object_state__=table):

            # If the isTerminator method hasn't been overwritten, then we
            # can just use the original loader for the instance.
            if ptypes.utils.callable_eq(cls, cls.isTerminator, Constructed, Constructed.isTerminator):
                result = super(Constructed, self).load(**attrs)

            # Otherwise, we want to treat this as a parray.terminated instance so
            # that the user can control when the array should stop being loaded.
            else:
                result = super(parray.block, self).load(**attrs)

        # Now our attribute ia removed, and we can return the loaded result.
        return result

    def __setvalue__(self, *args, **attrs):

        # Allocate the lookup table so that we can assign it to ourself
        # while setting. This ties directly into the _object_ method
        # which will use it to determine each element to assign with.
        table, _ = self.__get_lookup_table__()
        with utils.assign(self, __object_state__=table):

            # Call the original __setvalue__ implementation using our object
            # state that we've assigned.
            result = super(Constructed, self).__setvalue__(*args, **attrs)

        # Now we can return our result as if nothing happened.
        return result

    def classname(self):
        if hasattr(self, 'type'):
            klass, tag = (Context.Class, self.type) if isinstance(self.type, integer_types) else self.type
            protocol = self.parent.Protocol if self.parent else Protocol

            # Use the protocol to look up the Class and Tag for the type
            # that we're supposed to be.
            K = protocol.lookup(getattr(klass, 'Class', klass))
            try:
                t = K.lookup(tag)

            # If we didn't find it, then we use the same format for an
            # UnknownConstruct type.
            except KeyError:
                return self.typename()
            return t.typename()
        return super(Constructed, self).classname()

    def __get_lookup_table__(self):
        if not hasattr(self, '_fields_'):
            return {}, []

        # Iterate through all of our fields so that we can collect
        # them into a lookup table.
        res, ordered = {}, []
        for item, name in self._fields_:

            # Fail hard if the field doesn't have a type attribute
            # and has been midefined by the user.
            if not hasattr(item, 'type'):
                cls = self.__class__
                raise ValueError("Error with {:s} due to its definition for field \"{:s}\" using a type ({!s}) that is missing a \"{:s}\" attribute.".format('.'.join([cls.__module__, cls.__name__]), name, item, 'type'))

            # Now that we have the ptype, we can rip its klasstag...
            klass, tag = (Context.Class, item.type) if isinstance(item.type, integer_types) else item.type
            klasstag = getattr(klass, 'Class', klass), tag

            # ...and append it to our table for later retrieval.
            items = res.setdefault(klasstag, [])
            ordered.append((klasstag, len(items)))
            items.append( (name, item) )
        return res, ordered

    def has(self, key):
        count, klasstag = self.__get_typeindex_by_field(key)

        # Now we can look through our values for an item that matches.
        for item in self.value:
            if (item.Class(), item.Tag()) == klasstag:
                if count > 0:
                    count -= 1
                else:
                    return True
                continue
            continue
        return False

    def __get_typeindex_by_field(self, key):

        # If we're looking for a particular field name, then we need to
        # fetch the lookup table from our current fields.
        if isinstance(key, string_types):
            cls = self.__class__
            table, _ = self.__get_lookup_table__()

            # Start by building the lookup table keyed by the field name
            # and storing the klasstag for that particular field. We also
            # keep track of the index so that way we can count which
            # element the requested field is supposed to be at.
            res = {}
            for (klass, tag), items in table.items():
                for i, (name, _) in enumerate(items):
                    res[name.lower()] = i, (klass, tag)
                continue

            # Validate that the lengths match and that we didn't lose an
            # item due to a duplicate name.
            if len(res) != sum(len(items) for items in table.values()):
                logging.warning("{:s}.getitem({!s}) : Duplicate name found in fields for instance {:s}".format('.'.join([cls.__module__, cls.__name__]), key, self.instance()))

            # Now we can query our lookup table for the key.
            return res[key.lower()]

        # Otherwise, we should be being asked to look for a (Class, Tag)
        # pair which is pretty straightforward.
        if not isinstance(key, tuple):
            raise TypeError(key)

        # Verify that we have the expected number of items in the key,
        # and assign it to the variable that we use for searching. We
        # return the index 0 because this should be the only field
        # that matches.
        klass, tag = key
        return 0, (klass, tag)

    def item(self, key):
        count, klasstag = self.__get_typeindex_by_field(key)

        # Now we can look through our values for an item that matches.
        for item in self.value:
            if (item.Class(), item.Tag()) == klasstag:
                if count > 0:
                    count -= 1
                else:
                    return item
                continue
            continue
        raise KeyError(key)

    def __getitem__(self, index):
        if isinstance(index, string_types):
            return self.field(index)
        return super(Constructed, self).__getitem__(index)

    def _object_(self):
        protocol = self.parent.Protocol if self.parent else Protocol
        objectstate = self.__object_state__

        # Define the closure that we're going to assign to our child
        # elements. This way they can use us to lookup what type should
        # be used when decoding their value.
        def lookup(self, klasstag, protocol=protocol, state=objectstate):
            items = state.get(klasstag, [])
            try:
                item = items.pop(0)
                _, result = item

            # If we couldn't find the klasstag in our current state,
            # then we need to fall-back to a standard protocol lookup.
            except (IndexError, TypeError):
                klass, tag = klasstag

            # Otherwise, we found what we're looking for and can just
            # return the type that was discovered.
            else:
                return result

            # Start by looking up the protocol class, once that's found
            # then we need to lookup the type by its tag.
            K = protocol.lookup(klass)
            try:
                result = K.lookup(tag)

            # If we couldn't find a type matching the right tag number, then
            # we just return None to let the caller know that they need to
            # figure out whether to return an unknown primitive or a construct.
            except KeyError:
                result = None

            # Now we have a type for the caller to use.
            return result

        # All we need to do is return the protocol's Element type with our
        # lookup closure assigned as an attribute for it to use.
        return dyn.clone(protocol.default, Protocol=protocol, __object__=lookup)

    def __summary_items(self, table):
        for item in self.value:
            try:
                if isinstance(item, Element) and item.initializedQ():
                    klasstag = item.Class(), item.Tag()
                    items = table[klasstag]
                    name, type = items.pop(0)
                    yield "{:s}={:s}".format(name, item.__element__())
            except (KeyError, IndexError):
                yield "{:s}".format('???' if item is None else item.classname() if item.initializedQ() else item.typename())
            continue
        return

    def summary(self):
        if self.value is None:
            return '???'

        res, _ = self.__get_lookup_table__()
        iterable = self.__summary_items(res)
        return "{:s} : {{ {:s} }}".format(self.__element__(), ', '.join(iterable))

    def alloc(self, *args, **fields):
        cls, protocol = self.__class__, getattr(self.parent, 'Protocol', Protocol)
        items = []
        table, ordered = self.__get_lookup_table__()

        # First we need to figure out what positional fields we were
        # given so that we use them to empty out our lookup table, and
        # also preserve them when allocating our array later.
        args, = args if args else ([],)
        for fld in args:
            klasstag = getattr(fld, 'type', (fld.Class(), fld.Tag()))
            matched = table.get(klasstag, [])
            matched.pop(0) if len(matched) else matched
            items.append(fld)

        # Now that we've used up some of the names for the positional
        # fields we were given, if we have some explicit fields that
        # were specified then we need to reshape our lookup table so
        # that we can preserve the order of the fields to append.
        if hasattr(self, '_fields_') and fields:
            res = []
            for klasstag, index in ordered:
                list = table[klasstag]
                name, t = list[index]
                res.append((name, (klasstag, t)))
            nametable = res

            # Iterate through all of the names in the nametable looking
            # for fields that the caller has given us.
            for name, (klasstag, type) in nametable:
                if name not in fields:
                    continue
                item = fields.pop(name)

                # If an explicit Element instance was given to us, then
                # use it whilst updating the type.
                if isinstance(item, Element):
                    E = item.copy()
                    E['Value'].type = klasstag

                # If a ptype instance was provided, then use it as the
                # value for an Element instance.
                elif ptype.isinstance(item):
                    value = item.copy(type=klasstag)
                    E = protocol.default().alloc(Value=value)

                # If just the type was given to us, then we need to
                # instantiate it prior to assigning it as the value.
                elif ptype.istype(item):
                    value = dyn.clone(item, type=klasstag)
                    E = protocol.default().alloc(Value=value.a)

                # Otherwise, we have no idea what we're doing.
                else:
                    try:
                        value = type().alloc(item)

                    except TypeError:
                        logging.warning("{:s}.alloc(...) : Error allocating field \"{:s}\" for 0-sized type {!s} using value {!r}.".format('.'.join([cls.__module__, cls.__name__]), name, type, item))
                        logging.info("{:s}.alloc(...) : Attempting to set type {!s} with value {!r}.".format('.'.join([cls.__module__, cls.__name__]), type, item))
                        value = type().set(item)

                    if not value.size():
                        logging.fatal("{:s}.alloc(...) : The \"{:s}\" field was added as a 0-sized instance of type {!s}.".format('.'.join([cls.__module__, cls.__name__]), name, type))
                    E = protocol.default().alloc(Value=value)

                # Append the item to our current list of elements
                items.append(E)

            # Now we need to figure out what fields this array will be
            # composed of. Before doing this though, we need to iterate
            # through any explicit elements we were given and use them
            # to empty out our table.
            return super(Constructed, self).alloc(items, **fields)
        return super(Constructed, self).alloc(items, **fields)

class U8(pint.uint8_t):
    pass

class Block(parray.block):
    _object_ = U8
    def isTerminator(self, value):
        return False

    def alloc(self, *values, **attrs):
        if not values:
            return super(Block, self).alloc(*values, **attrs)
        value, = values
        return super(Block, self).alloc(bytearray(value) if isinstance(value, bytes) else value, **attrs)

    def __setvalue__(self, *values, **attrs):
        if not values:
            return super(Block, self).__setvalue__(*values, **attrs)
        value, = values
        return super(Block, self).__setvalue__(bytearray(value) if isinstance(value, bytes) else value, **attrs)

    def summary(self):
        octets = bytearray(self.serialize())
        res = str().join(map('{:02X}'.format, octets))
        return "({:d}) {:s}".format(len(octets), res)

class String(parray.block):
    _object_ = pstr.char_t
    def str(self):
        encoding = codecs.lookup(self._object_.encoding) if isinstance(self._object_.encoding, string_types) else self._object_.encoding
        res, _ = encoding.decode(self.serialize())
        return res
    def isTerminator(self, value):
        return False
    def summary(self):
        string = self.str()
        return "({:d}) {:s}".format(self.size(), string)

class OID(ptype.type):
    def __init__(self, **attributes):
        super(OID, self).__init__(**attributes)

        # Don't bother converting them if they don't actually exist.
        if not hasattr(self, '_values_'):
            return

        # Convert our _values_ into (name, tuple) since that's now the standard format.
        values = []
        for name, oid in getattr(self, '_values_', []):
            packed = tuple((int(item, 10) for item in oid.split('.')) if isinstance(oid, string_types) else oid)
            values.append((name, packed))
        self._values_[:] = values

    def str(self):
        res = self.get()
        return '.'.join(map("{:d}".format, res))

    def description(self):
        identifier = self.get()
        iterable = (name for name, oid in getattr(self, '_values_', []) if oid == identifier)
        return next(iterable, None)

    def summary(self):
        oid, data, description = self.str(), self.serialize(), self.description()
        res = super(OID, self).summary()
        if description is None:
            return '{:s} : {:s}'.format(oid, res)
        return '{:s} ({:s}) : {:s}'.format(description, oid, res)

    def __getvalue__(self):
        iterable = iter(bytearray(self.serialize()))

        # Collect the list of all of the numbers in the identifier.
        # These are encoded like the previously defined IdentifierLong
        # type in that each component is a 7-bit integer where the
        # highest bit of each octet is used to determine when an
        # integer is done being read.
        items = []
        for octet in iterable:
            item = octet & 0x7f
            while octet & 0x80:
                item *= pow(2,7)
                octet = next(iterable)
                item += octet & 0x7f
            items.append(item)
        return tuple(items)

    def set(self, value):

        # If we received a string, then we'll try to look it up before
        # converting it to a tuple and trying again.
        if isinstance(value, string_types):
            string = value

            # If our string begins with an alpha character (a keystring from rfc3383),
            # then we need to look up the keystring in our available values.
            if string.startswith(tuple('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')):
                iterable = (oid for keystring, oid in getattr(self, '_values_', []) if keystring == string)
                oid = next(iterable, None)
                if oid is None:
                    raise KeyError(string)
                return super(OID, self).set(tuple(oid))

            # Otherwise we need split up the oid into a tuple of integers (being sure
            # to replace the empty string with 0) so that we can fall through to the
            # tuple processing case.
            result = (int(item, 10) if item else 0 for item in string.split('.'))
            return super(OID, self).set(result)

        # Otherwise let the parent figure it out.
        return super(OID, self).set(value)

    def __setvalue__(self, items):
        if isinstance(items, bytes):
            return super(OID, self).__setvalue__(items)

        # Otherwise we're a tuple, and we need to deal with it.
        iterable = iter(items)

        # Define a closure which takes an integer and breaks it down into its
        # 7-bit components so that we can manually clear the sentinel bit when
        # the end of the integer is reached. This returns its results as a stack.
        def reduce(integral):
            if integral:
                while integral > 0:
                    yield integral & 0x7f
                    integral //= pow(2, 7)
                return
            yield 0

        # Iterate through the digits that we were given, and continue to
        # break them into 7-bit components. That way we can append them
        # to our result list of octets.
        res = []
        for item in iterable:
            items = [item for item in reduce(item)][::-1]

            # Iterate through the array, and set the highest bit in
            # every element except for the last one.
            res.extend([item | 0x80 for item in items[:-1]])
            res.extend([item & 0x7f for item in items[-1:]])

        # Now we can convert our array of packed 7-bit numbers to some
        # bytes that we can use to set our instance using the super method.
        data = bytearray(res)
        return super(OID, self).__setvalue__(bytes(data))

    def __getitem__(self, value):
        '''Return true if the OID matches the specified key.'''
        if isinstance(value, tuple):
            return self.get() == value

        # If it's not a string, then we have no clue what to do here.
        elif not isinstance(value, string_types):
            raise KeyError(value)

        # If it's a name, then we need to search our values to match the tuple.
        if value.startswith(tuple('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')):
            iterable = (oid for name, oid in getattr(self, '_values_', []) if name == value)
            expected = next(iterable, None)

        # Otherwise, we can just split up what the user gave us and be good to go.
        else:
            expected = tuple(int(item, 10) for item in value.split('.'))

        # If our value is not a tuple, then we're unable to proceed.
        if value is None:
            raise KeyError(value)
        return self.get() == expected

class CHOICE(Constructed):
    '''FIXME: this is a placeholder, but should probably be integrated into this template'''

### Element structure
class Protocol(ptype.definition):
    attribute, cache = 'Class', {}

    # use the following packet type for this protocol (assigned later)
    default = None

    # any elements that are unknown (or undefined) will use one of the
    # following types depending on whether it's constructed or not.
    class UnknownConstruct(Constructed):
        pass
    class UnknownPrimitive(Block):
        @classmethod
        def typename(cls):
            klass, tag = cls.type
            return "{:s}<{:d},{:d}>".format(cls.__name__, klass, tag)

class Element(pstruct.type):
    def classname(self):
        res = self.typename()
        return "{:s}<{:s}>".format(res, self['Value'].typename()) if self.value and 2 < len(self.value) else super(Element, self).classname()
        #return "{:s}<{:s}>".format(res, self['Value'].typename()) if self.value and not(len(self.value) < 3) else super(Element, self).classname()
        #return super(Element, self).classname() if len(self.value) < 3 else "{:s}<{:s}>".format(res, self['Value'].typename())

    def __element__(self):
        '''Return the typename so that it's a lot easier to read.'''

        if self.initializedQ():
            res = self['Value']

        # XXX: This is tied into the Constructed mixin
        elif hasattr(self, '_object_'):
            res = ptype.force(self._object_, self)

        # Otherwise, just figure out the correct type
        else:
            res = self.__object__(self['Type'], self['Length'])

        # Figure out how we need to represent this type.
        if isinstance(res, ptype.base):
            return res.classname()
        elif ptype.istype(res):
            return res.typename()
        return res.__name__

    def __protocol_lookup__(self, klasstag):
        protocol, (klass, tag) = self.Protocol, klasstag

        # First look up the type that we're going to need by grabbing the protocol,
        # then using it to determine the class, and then then by the actual tag.
        K = protocol.lookup(klass)
        try:
            result = K.lookup(tag)

        # If we couldn't find a type matching the right tag number, then just
        # return None to let the caller know they will just need to figure
        # things out themselves.
        except KeyError:
            return None
        return result

    def __object__(self, klasstag):
        return self.__protocol_lookup__(klasstag)

    def __Value(self):
        type, length = (self[fld].li for fld in ['Type', 'Length'])
        indefiniteQ, (klass, constructedQ, tag) = length.IndefiniteQ(), (type[fld] for fld in ['Class', 'Constructed', 'Tag'])

        # First grab the type that our Class and Tag should return.
        klasstag = klass, tag.int()
        t = self.__object__(klasstag) or self.__protocol_lookup__(klasstag)

        # If one wasn't found, then we need to figure out whether we're
        # returning an unknown constructed or an unknown primitive.
        if t is None:
            t = self.Protocol.UnknownConstruct if constructedQ else self.Protocol.UnknownPrimitive

        # Force what was discovered to a type that we can actually use.
        result = ptype.force(t, self)

        # If this is not a constructed type and not of an indefinite length,
        # then that was all we really needed to do. So prior to returning it,
        # set its blocksize and then let it go.
        if not constructedQ and not indefiniteQ:
            F = lambda _, size=length.int(): size
            return dyn.clone(result, type=klasstag, blocksize=F)

        # Next we'll need to figure out how the value's size is to be
        # determined. If it's an indefinite length, then it'll be looking
        # for the EOC terminator.
        attributes = {'type': klasstag}
        if indefiniteQ:
            F = lambda _, value, sentinel=EOC: isinstance(value['Value'], sentinel)
            attributes.setdefault('isTerminator', F)

        # Otherwise the length is defined, so we use it as the blocksize
        # and thus the actual terminator for the array type.
        else:
            F = lambda _, size=length.int(): size
            attributes.setdefault('blocksize', F)

        # If our result type is already a member of the Constructed type,
        # then we can just use it as the array to return.
        if issubclass(result, Constructed):
            return dyn.clone(result, **attributes)

        # If our result type isn't actually constructed, then this element
        # is a wrapper and we'll need to return a constructed value using
        # a copy of our element type as the object. If this is supposed to
        # be a primitive (non-constructed) type, then there's likely
        # something missing from the definition.
        return dyn.clone(Constructed, **attributes)

    def __Padding(self):
        length, value = (self[fld].li for fld in ['Length', 'Value'])
        return dyn.block(max(0, length.int() - value.size()))

    _fields_ = [
        (Type, 'Type'),
        (Length, 'Length'),
        (__Value, 'Value'),
        (__Padding, 'Padding'),
    ]

    def __alloc_value_primitive(self, result, size):
        if isinstance(result, parray.block):
            method_t = type(result.isTerminator)
            F = lambda _, cb=size: cb
            if ptypes.utils.callable_eq(result, result.isTerminator, parray.block, parray.block.isTerminator):
                result.blocksize = method_t(F, result)
        elif hasattr(result, 'length'):
            result.length = size
        return result

    def __alloc_value_indefinite(self, result):
        method_t, items = type(result.isTerminator), [String, Block]

        # If the array type is composed of integers, then we just
        # check to see if it's last element is the EOC byte.
        if isinstance(result, items):
            F = lambda _, value, sentinel=EOC.tag: value.int() == sentinel
            if any(ptypes.utils.callable_eq(result, result.isTerminator, item, item.isTerminator) for item in items):
                result.isTerminator = method_t(F, result)
            Fsentinel = result.isTerminator

        # Verify that the array is a terminated array. If it is,
        # then this might be a Constructed instance and so one of
        # its elements could be an EOC instance.
        elif isinstance(result, parray.terminated):
            F = lambda _, value, sentinel=EOC: isinstance(value['value'], sentinel)
            if ptypes.utils.callable_eq(result, result.isTerminator, parray.terminated, parray.terminated.isTerminator):
                result.isTerminator = method_t(F, result)
            Fsentinel = result.isTerminator

        # Otherwise if we're not even an array, then we need to warn
        # the user that we have no clue what to do.
        elif not isinstance(result, parray.type):
            logging.warning("{:s}.alloc : Skipping verification of terminator in {:s} with an indefinite length due to usage of a non-array type ({:s})".format('.'.join([cls.__module__, cls.__name__]), self.instance(), result.classname()))
            return result

        # This is a constant-length array type, so we need to explicitly
        # check it in order to warn the user.
        else:
            isterminator_int = lambda value, sentinel=EOC.tag: value.int() == sentinel
            isterminator_object = lambda value, sentinel=EOC: isinstance(value['value'], sentinel)
            isterminator_empty = lambda value: False
            Fsentinel = isterminator_empty if not len(result.value) else isterminator_object if isinstance(result.value[-1], Element) else isterminator_int

        # Warn the user if the terminator does not check out.
        item = result.value[-1] if len(result.value) else None
        if not Fsentinel(item):
            logging.warning("{:s}.alloc : Element {:s} with an indefinite length does not have an array instance that ends with an EOC element ({!s})".format('.'.join([cls.__module__, cls.__name__]), self.instance(), item if isinstance(item, integer_types) else item.summary()))
        return result

    def __alloc_value_construct(self, result, size):
        method_t = type(result.isTerminator)
        F = lambda _, cb=size: cb
        if ptypes.utils.callable_eq(result, result.isTerminator, parray.block, parray.block.isTerminator):
            result.blocksize = method_t(F, result)
        return result

    def __alloc_value(self, value, size, constructedQ, indefiniteQ):
        cls = self.__class__
        if not constructedQ and not indefiniteQ:
            result = self.__alloc_value_primitive(value, size)

        elif indefiniteQ:
            result = self.__alloc_value_indefinite(value)

        elif isinstance(value, Constructed):
            result = self.__alloc_value_construct(value, size)

        else:
            result.length = size
        return result

    def alloc(self, **fields):

        # If a Value was provided during allocation without the Type, then assign
        # one from the Universal/Primitive class using whatever its Tag is in .type
        value = fields.get('Value', fields.get('value', None))
        if hasattr(value, 'type'):
            klass, tag = (Context.Class, value.type) if isinstance(value.type, integer_types) else value.type
            constructedQ = 1 if (ptypes.istype(value) and issubclass(value, Constructed)) or isinstance(value, Constructed) else 0
            type = Type().alloc(Class=getattr(klass, 'Class', klass), Constructed=constructedQ)
            fields.setdefault('Type', type.set(Tag=tag))

        if 'Length' in fields:
            return super(Element, self).alloc(**fields)

        res = super(Element, self).alloc(**fields)
        res['Length'].set(res['Value'].size())
        self.__alloc_value(res['Value'], res['Value'].size(), res['Type']['Constructed'], res['Length'].IndefiniteQ())
        return res

    def Tag(self):
        t = self['Type']
        return t['Tag'].int()

    def ConstructedQ(self):
        t = self['Type']
        return t['Constructed'] == 1

    def Class(self):
        t = self['Type']
        return t['Class']

# set the defaults by connecting the Element type to the Protocol we defined.
Protocol.default, Element.Protocol = Element, Protocol

### Element classes
class ProtocolClass(ptype.definition):
    attribute = 'tag'

    @classmethod
    def __set__(cls, type, object, **kwargs):
        if isinstance(type, integer_types):
            object.type = cls.Class, type
            return super(ProtocolClass, cls).__set__(type, object)
        return super(ProtocolClass, cls).__set__(type, object)

@Protocol.define
class Universal(ProtocolClass):
    Class, cache = 0x00, {}
    class UniversalUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = UniversalUnknown
Protocol.Universal = Universal

@Protocol.define
class Application(ProtocolClass):
    Class, cache = 0x01, {}
    class ApplicationUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = ApplicationUnknown
Protocol.Application = Application

@Protocol.define
class Context(ProtocolClass):
    Class, cache = 0x02, {}
    class ContextUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = ContextUnknown
Protocol.Context = Context

@Protocol.define
class Private(ProtocolClass):
    Class, cache = 0x03, {}
    class PrivateUnknown(Protocol.UnknownPrimitive):
        pass
    unknown = PrivateUnknown
Protocol.Private = Private

### Tag definitions (X.208)
@Universal.define
class EOC(ptype.type):
    tag = 0x00
    # Required only if the length field specifies it

@Universal.define
class BOOLEAN(pint.uint_t):
    tag = 0x01

    def bool(self):
        res = self.int()
        return not(res == 0)

    def summary(self):
        res = "{!s}".format(self.bool())
        return ' : '.join([super(BOOLEAN, self).summary(), res.upper()])

@Universal.define
class INTEGER(pint.sint_t):
    tag = 0x02

@Universal.define
class BIT_STRING(pstruct.type):
    tag = 0x03
    _object_ = Block
    def __string(self):
        cls, t = self.__class__, self._object_
        if ptypes.utils.callable_eq(cls, cls.blocksize, BIT_STRING, BIT_STRING.blocksize):
            return t
        total, res = self.blocksize(), sum(self[fld].li.size() for fld in ['unused'])
        return dyn.clone(t, blocksize=lambda _, cb=max(0, total - res): cb)

    def __padding(self):
        cls = self.__class__
        if ptypes.utils.callable_eq(cls, cls.blocksize, BIT_STRING, BIT_STRING.blocksize):
            return dyn.block(0)
        total, res = self.blocksize(), sum(self[fld].li.size() for fld in ['unused', 'string'])
        return dyn.block(max(0, total - res))

    _fields_ = [
        (U8, 'unused'),
        (__string, 'string'),
        (__padding, 'padding(string)'),
    ]

    def bitstring(self):
        return self['string']

    def summary(self):
        if self.blocksize() > 0:
            unused, string = (self[fld] for fld in ['unused', 'string'])
            return "unused={:d} string={:s}".format(unused.int(), string.summary())
        return '...'

@Universal.define
class OCTET_STRING(Block):
    tag = 0x04
    def summary(self):
        octets = bytearray(self.serialize())
        iterable = map('{:02X}'.format, octets)
        return "({:d}) {:s}".format(self.size(), str().join(iterable))

@Universal.define
class NULL(ptype.block):
    tag = 0x05

@Universal.define
class OBJECT_IDENTIFIER(OID):
    tag = 0x06

    def __setvalue__(self, items):
        if isinstance(items, bytes):
            return super(OBJECT_IDENTIFIER, self).__setvalue__(items)

        iterable = iter(items)

        # Consume the oid identifier prefix, and combine it into the very
        # first octet according to the X.690 specification. If there's not
        # enough numbers provided, then we pad the expression with zeroes
        # since the oid identifier prefix is required.
        X, Y = next(iterable, 0), next(iterable, None)
        item = X * 40 + (Y or 0)

        # If we emptied our iterator already, then there's no data to
        # serialize, so we can just assign some empty bytes right here.
        if Y is None:
            result = b''

        # Otherwise, we'll want to prefix the iterable we were using with
        # the item we calculated for the first two octets.
        else:
            result = itertools.chain([item], iterable)
        return super(OBJECT_IDENTIFIER, self).__setvalue__(result)

    def __getvalue__(self):
        items = super(OBJECT_IDENTIFIER, self).__getvalue__()

        # Figure out the first identifier component. This is related
        # to that (X*40)+Y expression, and the other article where the
        # author claims that this is unambiguous. What they really
        # mean by that is that you need to assume that X is contrained
        # to either 0, 1, 2 and that you need to explicitly figure this
        # part out yourself.
        item = items[0] if items else 0
        res = 0 if item < 40 else 1 if item < 80 else 2

        # Now that we've figured out the identifier, use it as the prefix,
        # that we return to the caller. The number of identifiers should be
        # one less than the number of components, so if there's no items
        # left, then we end up returning just the single identifier.
        return tuple([res] + ([item - res * 40] if len(items) else []) + [subIdentifier for subIdentifier in items[1:]])

@Universal.define
class EXTERNAL(ptype.block):
    tag = 0x08

@Universal.define
class REAL(ptype.block):
    '''FIXME: Section 8.5 of X.690 explains how to decode these numerical types.'''
    tag = 0x09

@Universal.define
class ENUMERATED(pint.enum):
    tag = 0x0a

@Universal.define
class UTF8String(String):
    tag = 0x0c
    class _object_(pstr.char_t):
        encoding = codecs.lookup('utf-8')

@Universal.define
class RELATIVE_OID(OID):
    tag = 0x0d

@Universal.define
class TIME(UTF8String):
    tag = 0x0e

@Universal.define
class SEQUENCE(Constructed):
    tag = 0x10

@Universal.define
class SET(Constructed):
    tag = 0x11

@Universal.define
class NumericString(ptype.block):
    tag = 0x12

@Universal.define
class PrintableString(String):
    tag = 0x13

@Universal.define
class T61String(String):
    tag = 0x14

@Universal.define
class VideotexString(String):
    tag = 0x15

@Universal.define
class IA5String(String):
    tag = 0x16

@Universal.define
class UTCTime(String):
    tag = 0x17

@Universal.define
class GeneralizedTime(String):
    tag = 0x18

@Universal.define
class GraphicString(String):
    tag = 0x19

@Universal.define
class VisibleString(String):
    tag = 0x1a

@Universal.define
class GeneralString(String):
    tag = 0x1b

@Universal.define
class UniversalString(String):
    tag = 0x1c

@Universal.define
class CHARACTER_STRING(String):
    tag = 0x1d

@Universal.define
class BMPString(String):
    tag = 0x1e

@Universal.define
class DATE(UTF8String):
    tag = 0x1f

@Universal.define
class TIME_OF_DAY(UTF8String):
    tag = 0x20

@Universal.define
class DATE_TIME(UTF8String):
    tag = 0x21

@Universal.define
class DURATION(UTF8String):
    tag = 0x22

@Universal.define
class OID_IRI(UTF8String):
    tag = 0x23

@Universal.define
class RELATIVE_OID_IRI(UTF8String):
    tag = 0x24

### End of Universal definitions

### Base structures
class Packet(Element):
    byteorder = ptypes.config.byteorder.bigendian

class File(Element):
    byteorder = ptypes.config.byteorder.bigendian

if __name__ == '__main__':
    import sys, operator
    import ptypes, protocol.ber as ber
    from ptypes import bitmap
    from ptypes import *

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    def test_length():
        data = b'\x38'
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(data)).l
        assert(res.int() == 0x38)

        data = b'\x81\xc9'
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(data)).l
        assert(res.int() == 201)

        data = bitmap.zero
        data = bitmap.push(data, (0, 1))
        data = bitmap.push(data, (38, 7))
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(bitmap.data(data))).l
        assert(res.int() == 38)

        data = bitmap.zero
        data = bitmap.push(data, (0x81,8))
        data = bitmap.push(data, (0xc9,8))
        res = pbinary.new(ber.Length, source=ptypes.prov.bytes(bitmap.data(data))).l
        assert(res.int() == 201)
    test_length()

    def test_tag():
        data = bitmap.new(0x1e, 5)
        res = pbinary.new(ber.Tag, source=ptypes.prov.string(bitmap.data(data))).l
        assert(res.int() == 0x1e)

        data = bitmap.zero
        data = bitmap.push(data, (0x1f, 5))
        data = bitmap.push(data, (0x1, 1))
        data = bitmap.push(data, (0x10, 7))
        data = bitmap.push(data, (0x1, 0))
        data = bitmap.push(data, (0x0, 7))
        res = pbinary.new(ber.Tag, source=ptypes.prov.string(bitmap.data(data))).l
        assert(res['TagLong'][0].int() == 0x90)
        assert(res.int() == 0x800)
    test_tag()

    def t_dsa_sig():
        data = bytearray([ 0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 1)
        assert(z['value'][0]['value'].int() == 0x1)
        assert(z['value'][1]['value'].size() == 1)
        assert(z['value'][1]['value'].int() == 0x2)
    t_dsa_sig()

    def t_dsa_sig_extra():
        data = bytearray([0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02, 0x05, 0x00])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() + 2 == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 1)
        assert(z['value'][0]['value'].int() == 0x1)
        assert(z['value'][1]['value'].size() == 1)
        assert(z['value'][1]['value'].int() == 0x2)
    t_dsa_sig_extra()

    def t_dsa_sig_msb():
        data = bytearray([ 0x30, 0x08, 0x02, 0x02, 0x00, 0x81, 0x02, 0x02, 0x00, 0x82 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 2)
        assert(z['value'][0]['value'].int() == 0x81)
        assert(z['value'][1]['value'].size() == 2)
        assert(z['value'][1]['value'].int() == 0x82)
    t_dsa_sig_msb()

    def t_dsa_sig_two():
        data = bytearray([ 0x30, 0x08, 0x02, 0x02, 0x01, 0x00, 0x02, 0x02, 0x02, 0x00 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].size() == 2)
        assert(z['value'][0]['value'].int() == 0x100)
        assert(z['value'][1]['value'].size() == 2)
        assert(z['value'][1]['value'].int() == 0x200)
    t_dsa_sig_two()

    def t_invalid_int_zero():
        data = bytearray([ 0x30, 0x05, 0x02, 0x00, 0x02, 0x01, 0x2a ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0x0)
        assert(z['value'][1]['value'].int() == 0x2a)
    t_invalid_int_zero()

    def t_invalid_int():
        data = bytearray([ 0x30, 0x07, 0x02, 0x02, 0x00, 0x7f, 0x02, 0x01, 0x2a ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0x7f)
        assert(z['value'][1]['value'].int() == 0x2a)
    t_invalid_int()

    def t_neg_int():
        data = bytearray([ 0x30, 0x06, 0x02, 0x01, 0xaa, 0x02, 0x01, 0x2a ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0xaa - 0x100)
        assert(z['value'][1]['value'].int() == 0x2a)
    t_neg_int()

    def t_trunc_der():
        data = bytearray([ 0x30, 0x08, 0x02, 0x02, 0x00, 0x81, 0x02, 0x02, 0x00 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        try: z=z.l
        except: pass
        assert(z.size() < z.source.size())
        assert(isinstance(z['value'], ber.Constructed))
        assert(len(z['value']) == 1)
        assert(z['value'][0].size() == 4)
        assert(isinstance(z['value'][0]['value'], ber.INTEGER))
    t_trunc_der()

    def t_trunc_seq():
        data = bytearray([ 0x30, 0x07, 0x02, 0x02, 0x00, 0x81, 0x02, 0x02, 0x00, 0x82 ])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        try: z=z.l
        except: pass
        assert(z.size() < z.source.size())
        assert(z['length'].int() == z['value'].size())
        assert(len(z['value']) == 2)
        assert(z['value'][0].initializedQ())
        assert(z['value'][0]['value'].size() == 2)
        assert(z['value'][0]['value'].int() == 0x81)
        assert(not z['value'][1].initializedQ())
        assert(z['value'][1]['value'].size() == 1)
        assert(isinstance(z['value'][1]['value'], ber.INTEGER))
    t_trunc_seq()

    def t_invalid_zero():
        data = bytearray([0x30, 0x02, 0x02, 0x00])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 2)
        assert(len(z['value']) == 1)
        assert(all(isinstance(item['value'], ber.INTEGER) for item in z['value']))
        assert(z['value'][0]['value'].int() == 0)
    t_invalid_zero()

    def t_invalid_template():
        data = bytearray([0x30, 0x03, 0x0c, 0x01, 0x41])
        z = ber.Packet(source=ptypes.prov.bytes(bytes(data)))
        z=z.l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 3)
        assert(len(z['value']) == 1)
        assert(all(isinstance(item['value'], ber.UTF8String) for item in z['value']))
        assert(z['value'][0]['value'].str() == u'A')
    t_invalid_template()

    def test_x690_spec_0():
        data = '0307040A3B5F291CD0'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 7)
        assert(isinstance(z['value'], ber.BIT_STRING))
        assert(z['value'].serialize() == fromhex('040a3b5f291cd0'))
    test_x690_spec_0()

    def test_x690_spec_1():
        data = '23800305045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 2)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(isinstance(z['value'][0]['value'], ber.BIT_STRING))
        assert(z['value'][0]['value'].serialize() == b'\x04\x5f\x29\x1c\xd0')
    test_x690_spec_1()

    def test_indef_cons():
        data = '23800403000a3b0405045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 3)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
    test_indef_cons()

    def test_indef_cons_cons():
        data = '23802380030200010302010200000302040f0000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 3)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        z = z['value'][0]
        assert(z['length'].IndefiniteQ())
        assert(len(z['value']) == 3)
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
    test_indef_cons_cons()

    def test_cons():
        data = '230c03020001030200010302040f'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 12)
        assert(len(z['value']) == 3)
        assert(all(isinstance(item, ber.Element) for item in z['value']))
        assert([item['value'].serialize() for item in z['value']] == [b'\0\1', b'\0\1', b'\4\x0f'])
    test_cons()

    def test_indef_bit_bit():
        data = '23800303000a3b0305045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(all(isinstance(item, ber.Element) for item in z['value']))
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert([item['value'].serialize() for item in z['value'][:-1]] == [fromhex('000a3b'), fromhex('045f291cd0')])
    test_indef_bit_bit()

    def test_empty_bit_cons():
        data = '2300'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(len(z['value']) == 0)
        assert(isinstance(z['value'].alloc(length=1)[0], ber.Element))
    test_empty_bit_cons()

    def test_empty_bit_prim():
        data = '0300'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(z['value'].size() == 0)
        assert(isinstance(z['value'], ber.BIT_STRING))
    test_empty_bit_prim()

    def test_cons_octetbit():
        data = '24800303000a3b0305045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(z['value'].type == (0, 4))
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(all(isinstance(item['value'], ber.BIT_STRING) for item in z['value'][:-1]))
        assert([item['value'].serialize() for item in z['value'][:-1]] == [fromhex('000a3b'), fromhex('045f291cd0')])
    test_cons_octetbit()

    def test_indef_incomplete():
        data = '24800403000405045f291cd00000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data)))
        try: z.l
        except: pass
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(z['value'].type == (0, 4))
        assert(len(z['value']) == 2)
        assert(all(isinstance(item['value'], ber.OCTET_STRING) for item in z['value']))
    # This testcase is supposed to generate a non-critical LoadError.
    #test_indef_incomplete()

    def test_empty_prim_oct():
        data = '0400'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(z['value'].type == (0, 4))
        assert(len(z['value']) == 0)
        assert(isinstance(z['value'].alloc(length=1)[0], ber.U8))
    test_empty_prim_oct()

    def test_empty_cons_oct():
        data = '2400'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == 0)
        assert(z['value'].type == (0, 4))
        assert(len(z['value']) == 0)
        assert(isinstance(z['value'].alloc(length=1)[0], ber.Element))
    test_empty_cons_oct()

    def test_consdef_bit():
        data = '230e030200010000030200010302040f'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].int() == z['value'].size())
        assert(len(z['value']) == 4)
        assert(all(isinstance(item['value'], t) for item, t in zip(z['value'], [ber.BIT_STRING, ber.EOC, ber.BIT_STRING, ber.BIT_STRING])))
        assert([item['value'].serialize() for item in z['value']] == [b'\0\1', b'', b'\0\1', b'\4\x0F'])
    test_consdef_bit()

    def test_consindef_bit():
        data = '2380030200010302000103020f0f0000'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(all(isinstance(item['value'], ber.BIT_STRING) for item in z['value'][:-1]))
        assert(z['value'][-1]['value'].size() == 0)
    test_consindef_bit()

    def test_consindef_bit_nonzeroeoc():
        data = '2380030200010302000103020f0f000120'
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.size() == z.source.size())
        assert(z['length'].IndefiniteQ())
        assert(isinstance(z['value'][-1]['value'], ber.EOC))
        assert(all(isinstance(item['value'], ber.BIT_STRING) for item in z['value'][:-1]))
        assert(z['value'][-1]['value'].size() == 1)
    test_consindef_bit_nonzeroeoc()

    def test_object_identifier_0():
        data = '0603 813403'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(z.size() == z.source.size())
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 3)
    test_object_identifier_0()

    def test_object_identifier_1():
        data = '0603 813403'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 3)

        expected = (2,100,3)
        assert(z['value'].get() == expected)
    test_object_identifier_1()

    def test_object_identifier_set_2():
        data = '0603 813403'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 3)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([2,100,3])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_2()

    def test_object_identifier_3():
        data = '0609 2b0601040182371514'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 9)

        expected = (1,3,6,1,4,1,311,21,20)
        assert(z['value'].get() == expected)
    test_object_identifier_3()

    def test_object_identifier_set_4():
        data = '0609 2b0601040182371514'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 9)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([1,3,6,1,4,1,311,21,20])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_4()

    def test_object_identifier_5():
        data = '0603 818403'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 3)

        expected = (2,16819)
        assert(z['value'].get() == expected)
    test_object_identifier_5()

    def test_object_identifier_set_6():
        data = '0603 818403'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 3)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([2,16819])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_6()

    def test_object_identifier_7():
        data = '0604 ffffff00'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 4)

        expected = (2,268435248)
        assert(z['value'].get() == expected)
    test_object_identifier_7()

    def test_object_identifier_set_8():
        data = '0604 ffffff00'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 4)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([2,268435248])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_8()

    def test_object_identifier_9():
        data = '0604 ffffff7f'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 4)

        expected = (2,268435375)
        assert(z['value'].get() == expected)
    test_object_identifier_9()

    def test_object_identifier_set_10():
        data = '0604 ffffff7f'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 4)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([2,268435375])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_10()

    def test_object_identifier_11():
        data = '0604 00ffff00'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 4)

        expected = (0,0,2097024)
        assert(z['value'].get() == expected)
    test_object_identifier_11()

    def test_object_identifier_set_12():
        data = '0604 00ffff00'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 4)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([0,0,2097024])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_12()

    def test_object_identifier_13():
        data = '0601 7f'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = (2,47)
        assert(z['value'].get() == expected)
    test_object_identifier_13()

    def test_object_identifier_set_14():
        data = '0601 7f'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([2,47])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_14()

    def test_object_identifier_15():
        data = '0602 8000'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 2)

        expected = (0,0)
        assert(z['value'].get() == expected)
    test_object_identifier_15()

    def test_object_identifier_16():
        data = '0608 8000000000000000'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 8)

        expected = (0,0,0,0,0,0,0,0)
        assert(z['value'].get() == expected)
    test_object_identifier_16()

    def test_object_identifier_17():
        data = '0601 28'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = (1,0)
        assert(z['value'].get() == expected)
    test_object_identifier_17()

    def test_object_identifier_set_18():
        data = '0601 28'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([1,0])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_18()

    def test_object_identifier_19():
        data = '0601 27'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = (0,39)
        assert(z['value'].get() == expected)
    test_object_identifier_19()

    def test_object_identifier_set_20():
        data = '0601 27'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([0,39])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_20()

    def test_object_identifier_21():
        data = '0601 00'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = (0,0)
        assert(z['value'].get() == expected)
    test_object_identifier_21()

    def test_object_identifier_set_22():
        data = '0601 00'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([0,0])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_22()

    def test_object_identifier_23():
        data = '0600'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 0)

        expected = (0,)
        assert(z['value'].get() == expected)
    test_object_identifier_23()

    def test_object_identifier_set_24():
        data = '0600'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 0)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set([0])
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_24()

    def test_object_identifier_set_25():
        data = '06028120'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 2)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set('2.80')
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_25()

    def test_object_identifier_set_26():
        data = '060128'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.OBJECT_IDENTIFIER))
        assert(z['value'].size() == 1)

        expected = z['value']
        res = ber.OBJECT_IDENTIFIER().set('1.')
        assert(res.serialize() == expected.serialize())
    test_object_identifier_set_26()

    def test_relative_object_identifier_27():
        data = '0D04C27B0302'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.RELATIVE_OID))
        assert(z['value'].size() == 4)

        expected = (8571,3,2)
        assert(z['value'].get() == expected)
    test_relative_object_identifier_27()

    def test_relative_object_identifier_set_28():
        data = '0D04C27B0302'.replace(' ', '')
        z = ber.Packet(source=ptypes.prov.bytes(fromhex(data))).l
        assert(z.serialize() == z.source.value)
        assert(isinstance(z['value'], ber.RELATIVE_OID))
        assert(z['value'].size() == 4)

        expected = z['value']
        res = ber.RELATIVE_OID().set([8571,3,2])
        assert(res.serialize() == expected.serialize())
    test_relative_object_identifier_set_28()

if __name__ == '__main__':
    import sys, ptypes
    if len(sys.argv) < 2:
        sys.exit(0)

    source = ptypes.prov.file(sys.argv[1], 'rb')
    source = ptypes.setsource(source)

    z = ber.File(source=source)
    z=z.l
