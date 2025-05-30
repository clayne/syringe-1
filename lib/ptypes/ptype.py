"""Core primitives used by all ptypes.

All programs are based on various types of complex data structures. Ptypes aims
to be able to describe these data structures and assist a user with creating and
navigating through these structures. In order to do this, a ptype is used to
describe the different types within aa structure. Ptypes are composed of two basic
types of structures. One of which is an atomic type, or rather a ptype.type, and
another which is a container type, or rather a ptype.container.

Both of these types provide a number of methods for determining the relationships
between the different fields in a complex data structure. Each of these methods
are responsible for loading or storing data to a ptypes.provider or exploring
and shifting the bounds of each component of the structure. The basic methods
that define the boundaries of each type are as follows:

    def setoffset(self, offset):
        '''Change the offset of ``self`` to ``offset``'''
    def getoffset(self):
        '''Return the current offset of ``self``'''
    def blocksize(self):
        '''Return the expected size of ``self``'''
    def size(self):
        '''Return the actual size of ``self``'''
    def contains(self, offset):
        '''Returns True if ``offset`` is contained within the bounds of ``self``.'''

    .offset -- offset of ptype

Another aspect of each type is their state and position relative to other types.
These can be discovered by the following methods and properties:

    def initializedQ(self):
        '''Returns True or False based on whether or not ``self`` is initialized.'''
    def serialize(self):
        '''Return ``self`` serialized to byte-form'''
    def field(self, offset):
        '''Return the sub-element at the given ``offset`` relative to the beginning of ``self``'''
    def at(self, offset):
        '''Return the sub-element at the given ``offset``.'''
    def getparent(self, type):
        '''Traverse upwards looking for a parent type of the specified ``type``'''
    def traverse(self, edges, filter):
        '''A generator that can be used to navigate through ``self``'''

    .parent -- Return the parent instance
    .value -- Return the value of the instance

Each instance has various methods that are used for managing the state of a
of an instance and how it may modify the attributes of another given instance.
In order to assist with dynamic contruction and modification of attributes, most
of these methods contain keyword arguments. These keyword arguments are exposed
to the user in that they allow one to apply them to the newly constructed type or
instance returned by a method by modifying it's result's attributes. Another
aspect of these keyword arguments is a specific keyword, 'recurse',
modify the attributes of any sub-elements of the specific instance. The 'recurse'
keyword will be used whenever an instance creates a sub-element via the .new()
method and allows a user to customize the attributes of an instance or any
instances created by that instance.

Example:
# return a type where type.attr1 == value, and type.method() returns 'result'
    def method(self, **attrs): return type
    type = self.method(attr1=value, method1=lambda:result)
    assert type.attr1 == value and type().method() == result

# return an instance where instance.attr1 == value, and instance.method1() returns result.
    def method(self, **attrs): return instance
    instance = self.method(attr1=value, method1=lambda self: True)
    assert instance.attr1 == value and instance.method1() == True

# return an instance where any elements spawned by `self` have their attr1 set to True.
    def method(self, **attrs): return instance
    instance = self.method(recurse={'attr1':True})
    assert instance.new(type).attr1 == True

The .load and .commit methods have their ``attrs`` applied temporarily whilst
loading/committing the ptype from it's source. The other methods that implement
this style of keyword-attribute updating are as follows:

    def new(self, type, **attrs):
        '''Create an instance of ``type`` with the specified ``attrs`` applied.'''
    def cast(self, type, **attrs):
        '''Cast ``self`` to ``type`` with the specified ``attrs`` applied.'''
    def copy(self, **attrs):
        '''Return a copy of self with the value of ``attrs`` applied to it's attributes'''
    def load(self, **attrs):
        '''Initialize ``self`` with the contents of the provider.'''
    def commit(self, **attrs):
        '''Commit the contents of ``self`` to the provider.'''
    def alloc(self, **attrs):
        '''Initialize ``self`` with '\\x00' bytes.'''

To shorten the user from having to type a few very common methods, each ptype
has some aliases that point directly to methods. A list of these aliases are:

    instance.v -- alias to instance.value
    instance.p -- parent element of instance
    instance.a -- re-allocate instance with zeroes
    instance.c -- commit to default source
    instance.l -- load from default source
    instance.li -- load if uninitialized from default source
    instance.d -- dereference from instance
    instance.ref -- reference object to instance

A ptype.type interface is considered the base atomic type of the complex data
structure, and contains only one propery..it's length. The .length property affects
the result returned from the .blocksize() method. A ptype.type has the following
interface:

    class interface(ptype.type):
        length = size-of-ptype
        source = provider-of-data

        def set(self, value):
            '''Sets the contents of ``self`` to ``value``'''
        def get(self):
            '''Returns the value of ``self`` to a value that can be assigned to /.set/'''
        def summary(self):
            '''Returns a single-line description of ``self``'''
        def details(self):
            '''Returns a multi-line description of ``self``'''
        def repr(self):
            '''Returns the default description of ``self``'''

A ptype.container interface is a basic type that contains other ptype instances.
This type is intended to be a base type for other more complex types. Some of
the methods that it provides are:

    class interface(ptype.container):
        def __getitem__(self, key):
            '''Return the instance identified by ``key``.'''
        def __setitem__(self, index, value):
            '''Assign ``value`` to index ``index`` of ``self``.'''
        def append(self, object):
            '''Appends ``object`` to the end of the ``self`` container.'''
        def set(self, *iterable):
            '''Changes ``self`` to the values specified in ``iterable``'''
        def get(self):
            '''Return an iterable that can be passed to /.set/''''

Within this module, some primitive types are provided that a user can include
within their definition of a complex data structure. These types are:

    boundary -- A "marker" that can be applied to a type so that .getparent can
                be used to fetch it.

    block -- A type that defines a block of unknown data. The .length property
             specifies it's bytesize.

    undefined -- A type that defines undefined data. It's .length specifies the
                 size. This type is used when a user doesn't know or care about
                 the type.

There are certain complex-structures that contain a field that is used to refer
to another part or different field. To dereference a pointer, one simply has to
call the .dereference method to return the new instance. If one wants to assign
a reference to an object to the pointer, one may call .reference with the ptype
as it's argument. In order to expose these various pointer types, this moduel
contains the following types:

    pointer_t -- A integral type that points to another type. The target type is
                 defined by the ._object_ attribute.

    rpointer_t -- A integral type that points to another type relative to another
                  object. Similar to pointer_t.

    opointer_t -- A integral type that is used to calculate the offset to another
                  instance. Similar to pointer_t.

    setbyteorder -- A function that is used to set the default byteorder of all
                    the pointer_t. Can use the values defined in config.byteorder.

Some other utility types provided by this module are the following:

    wrapper_t -- A type that wraps an alternative type. Any loads or commits
                 made to/from this type will use the contents of the alternative type.

    encoded_t -- A type that allows the user to encode/decode the data before
                 loading or committing.

    definition -- A utility class that allows one to look up a particular type
                  by an identifier.

One aspect of ptypes that would be prudent to describe is that during any
instance a user is allowed to specify a type, one can include a closure. This
closure takes one argument which is the ``self`` instance. From this closure,
a user can figure which type to return at which point ptypes will instantiate
the returned type.

Example core usage:
# define a ptype that's 8 bytes in length
    from ptypes import ptype
    class type(ptype.type):
        length = 8

# instantiate a ptype using a different source
    from ptypes import provider
    instance = type(source=provider.example)

# instantiate a ptype at the specified offset
    instance = type(offset=57005)

# move an instance to the specified offset
    instance.setoffset(57005)

# fetch the parent of a given instance
    parent = instance.getparent()

# determine the instance at the specified offset of instance
    subinstance = instance.at(57005, recurse=True)

Example pointer_t usage:
# define a pointer to a uint32_t
    from ptypes import ptype, pint
    class type(ptype.pointer_t):
        _object_ = pint.uint32_t

# define a pointer relative to the parent object
    from ptypes import ptype, pint
    class type(ptype.rpointer_t):
        _object_ = pint.uint32_t
        _baseobject_ = rootobject

# define a pointer that adds 0x100 to a pointer and then returns a pint.uint32_t
    class type(ptype.opointer_t):
        _object_ = pint.uint32_t
        def _calculate_(self, number):
            return number + 0x100
"""
import sys, builtins, functools, itertools, types, operator
import time

from . import bitmap, provider, utils, error

__all__ = 'istype,iscontainer,isrelated,type,container,undefined,block,definition,encoded_t,pointer_t,rpointer_t,opointer_t,boundary,clone,setbyteorder'.split(',')

from . import config
Config = config.defaults
Log = config.logging.getLogger('.'.join([Config.log.name, 'ptype']))

# Setup some version-agnostic utilities that we can perform checks with
__izip_longest__ = utils.izip_longest

## this is all a horrible and slow way to do this...
def isiterator(t):
    """True if type ``t`` is iterable"""
    # FIXME: also insure that it's not a class with these attributes
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def iscallable(t):
    """True if type ``t`` is a code object that can be called"""
    return builtins.callable(t) and hasattr(t, '__call__')

@utils.memoize('t')
def isinstance(t):
    return builtins.isinstance(t, generic)

if sys.version_info[0] < 3:
    @utils.memoize('t')
    def istype(t):
        """True if type ``t`` inherits from ptype.type"""
        return t.__class__ is t.__class__.__class__ and not isresolveable(t) and (builtins.isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, generic)
else:
    @utils.memoize('t')
    def istype(t):
        """True if type ``t`` inherits from ptype.type"""
        return t.__class__ is t.__class__.__class__ and not isresolveable(t) and issubclass(t, generic)

@utils.memoize('t')
def iscontainer(t):
    """True if type ``t`` inherits from ptype.container """
    return (istype(t) and issubclass(t, container)) or pbinary.istype(t)

@utils.memoize('t')
def isresolveable(t):
    """True if type ``t`` can be descended into"""
    return builtins.isinstance(t, (types.FunctionType, types.MethodType))    # or isiterator(t)

def isrelated(t, t2):
    """True if type ``t`` is related to ``t2``"""
    def getbases(result, bases):
        for t in bases:
            if not istype(t) or t in (type, container):
                continue
            result.add(t)
            getbases(result, t.__bases__)
        return result
    return getbases(set(), t.__bases__).intersection( getbases(set(), t.__bases__) )

def force(t, self, chain=[]):
    """Resolve type ``t`` into a ptype.type for the provided object ``self``"""
    chain = chain[:]
    chain.append(t)

    ## First check if we're inserting types into our tree

    # if type is a pbinary type, we insert a partial node into the tree
    if pbinary.istype(t):
        Log.debug("{:s}.force : {:s} : Implicitly promoting binary type `{:s}` to partial for storing in non-binary container.".format(__name__, self.instance(), t.typename()))
        return clone(pbinary.partial, _object_=t)

    # if type is a straight-up ptype
    elif istype(t):
        return t

    ## Next we'll check instances (for setting and allocating)

    # if type is a pbinary instance
    if builtins.isinstance(t, pbinary.base):
        return pbinary.new(t)

    # if type is just a regular ptype instance
    elif builtins.isinstance(t, base):
        return t

    ## Now we'll try callables and see if it's one of those

    # functions
    if builtins.isinstance(t, types.FunctionType):
        res = t(self)
        return force(res, self, chain)

    # bound methods
    elif builtins.isinstance(t, types.MethodType):
        return force(t(), self, chain)

    # disabling generators for compatibility with micropython
    #elif inspect.isgenerator(t):
    #    return force(next(t), self, chain)

    # and lastly iterators (unsupported)
    #if False:
    #    if isiterator(t):
    #        return force(next(t), self, chain)

    path = str().join(map("<{:s}>".format, self.backtrace()))
    raise error.TypeError(self, "force<ptype>', message='chain={!r} : Refusing request to resolve {!r} to a type that does not inherit from ptype.type : {{{:s}}}".format(chain, t, path))

source = provider.default()
class __interface__(object):
    # XXX: this class should implement
    #           attribute inheritance
    #           addition and removal of elements to trie
    #           initial attribute creation
    #           attributes not propagated during creation
    #           XXX meta-related information
    #           instance tree navigation

    __slots__ = {}  #('__source__', 'attributes', 'ignored', 'parent', 'value', 'position')

    # FIXME: it'd probably be a good idea to have this not depend on globals.source,
    #        and instead have globals.source depend on this.
    __slots__['__source__'] = None      # ptype.prov
    @property
    def source(self):
        if self.parent is None:
            global source
            return source if self.__source__ is None else self.__source__
        return self.parent.source if self.__source__ is None else self.__source__
    @source.setter
    def source(self, value):
        self.__source__ = value

    __slots__['attributes'] = None        # {...}
    __slots__['ignored'] = {'source', 'parent', 'attributes', 'value', '__name__', 'position', 'offset'}

    __slots__['parent'] = None       # ptype.base
    p = property(lambda self: self.parent)   # abbr to get to .parent

    __slots__['value'] = None        # _
    v = property(lambda self: self.value)   # abbr to get to .value

    def __init__(self, **attrs):
        """Create a new instance of object. Will assign provided named arguments to self.attributes"""
        # As python3 seems to have broken the way that slots work, we simulate
        # the assignment of the default values for each slot attribute by
        # walking the __slots__ dictionary, and assigning its values to our
        # instance.
        for attribute, default in self.__slots__.items():
            if not hasattr(self, attribute):
                setattr(self, attribute, default)
            continue

        # Make a copy of our current attributes for our new instance, and then
        # update ourselves with the attributes provided by the caller.
        self.attributes = {} if self.attributes is None else dict(self.attributes)
        [setattr(self, attribute, value) for attribute, value in self.attributes.items()]
        self.__update__(attrs)

    ## offset
    def setoffset(self, offset, **_):
        raise error.ImplementationError(self, 'generic.setoffset')
    def getoffset(self, **_):
        raise error.ImplementationError(self, 'generic.setoffset')
    offset = property((lambda self: self.getoffset()), (lambda self, value: self.setoffset(value)))

    ## position
    def setposition(self, position, **_):
        raise error.ImplementationError(self, 'generic.setposition')
    def getposition(self):
        raise error.ImplementationError(self, 'generic.getposition')

    @property
    def position(self):
        return self.getposition()
    @position.setter
    def position(self, value):
        return self.setposition(value)

    def __update__(self, attrs={}, **moreattrs):
        """Update the attributes that will be assigned to object.

        Any attributes defined under the 'recurse' key will be propagated to any
        sub-elements.
        """
        attrs = dict(attrs)
        attrs.update(moreattrs)
        recurse = dict(attrs.pop('recurse', {}))
        ignored = self.ignored

        # update self with all attributes
        res = {}
        res.update(recurse)
        res.update(attrs)
        for k, v in res.items():
            setattr(self, k, v)

        # filter out ignored attributes from the recurse dictionary
        recurse = {k : v for k, v in recurse.items() if k not in ignored}

        # update self (for instantiated elements)
        self.attributes.update(recurse)

        # update sub-elements with recursive attributes
        if recurse and issubclass(self.__class__, container) and self.value is not None:
            [item.__update__(recurse, recurse=recurse) for item in self.value]
        return self

    def properties(self):
        '''Return a dictionary of properties or characteristics about the current state of the object.'''
        return self.__properties__()

    def __properties__(self):
        '''Internal implementation of the __interface__.properties() method.'''
        result = {}

        # Validate that we weren't constructed with a name per a field assignment,
        # or explicitly specifying the name via a property. If the name is empty,
        # then we are simply unnamed.
        if not getattr(self, '__name__', ''):
            result['unnamed'] = True

        # Do an immediate uninitialization check
        if self.value is None:
            result['uninitialized'] = True
            return result

        # Otherwise we need to check the sizes in order to determine
        # whether we're underloaded (blocksize too small) or if we're
        # overcommitted (actual size too large).
        try:
            size = self.size()

        # If we can't get our size because of an InitializationError, then
        # there's no reason to check our load/commit state
        except error.InitializationError:
            pass

        # We finally got a valid size, and we need to figure out whether the type is
        # either overcommited (size > blocksize) or it's underloaded (size < blocksize)
        else:
            key = 'overcommit'  if self.blocksize() < size else 'underload' if self.blocksize() > size else None
            if key: result[key] = True
        return result

    def traverse(self, edges, filter=lambda node: True, **kwds):
        """Will walk the elements returned by the generator ``edges -> node -> ptype.type``

        This will iterate in a top-down approach.
        """
        for self in edges(self, **kwds):
            if not isinstance(self):
                continue

            # Check to see if our current instance is filtered, and yield it
            # if it is.
            if filter(self):
                yield self

            # Recurse into each of our edges to see if any items are requested
            # by the caller and need to be yielded
            for item in self.traverse(edges=edges, filter=filter, **kwds):
                yield item
            continue
        return

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        try:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().items())

        # If we got an InitializationError while fetching the properties (due to
        # a bunk user implementation), then we simply fall back to the internal
        # implementation.
        except error.InitializationError:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.__properties__().items())

        result = self.repr()

        # multiline
        if result.count('\n') > 0:
            result = result.rstrip('\n') # remove trailing newlines
            if prop:
                return u"{:s} '{:s}' {{{:s}}}\n{:s}".format(utils.repr_class(self.classname()), self.name(), prop, result)
            return u"{:s} '{:s}'\n{:s}".format(utils.repr_class(self.classname()), self.name(), result)

        _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        # single-line
        descr = u"{:s} '{:s}'".format(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(), self.name())
        if prop:
            return u"[{:s}] {:s} {{{:s}}} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, prop, result)
        return u"[{:s}] {:s} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, result)

    def __format__(self, spec):
        prefix, spec = spec[:-1], spec[-1:]
        if spec:
            if spec in 'I':
                offset, name = self.getoffset(), self.name()
                format = functools.partial("[{:#x}] {:s}".format, offset) if '#' in prefix else "{:s}".format
                if self.value is None:
                    cls = self.__class__
                    return format(utils.repr_class(cls.typename() if istype(cls) else cls.__name__))
                return format(utils.repr_instance(self.classname(), name))

            elif spec in 'P':
                format = "{{{:s}}}".format if '#' in prefix else "{:s}".format
                properties = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().items())
                return format(properties) if properties else u''

            elif self.value is None:
                raise error.InitializationError(self, '__interface__.__format__')
            return super(__interface__, self).__format__(spec)

        # Grab the properties, similar to self.__repr__()
        try:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().items())

        except error.InitializationError:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.__properties__().items())

        # Render with self.repr() and check for newlines. If there are any, then
        # we fall back to using self.summary() because we're being formatted.
        # Render with self.summary which should pretty much always work.
        try:
            result = self.summary()

        # If it doesn't, though, because maybe the data is uninitialized then
        # we fall back to self.repr() while stripping out the last newline.
        except Exception:
            result = self.repr().rstrip('\n')

        # Format the whole thing as a single line (similar to self.__repr__).
        _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        descr = u"{:s} '{:s}'".format(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(), self.name())
        if prop:
            return u"[{:s}] {:s} {{{:s}}} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, prop, result)
        return u"[{:s}] {:s} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, result)

    # naming
    @classmethod
    def typename(cls):
        """Return the name of the ptype"""
        module, qualname = getattr(cls, '__module__', ''), getattr(cls, '__qualname__', cls.__name__) or cls.__name__
        if module:
            if Config.display.show_module_name:
                return '.'.join([module, qualname])
            return '.'.join([module.rsplit('.', 1)[-1], qualname])
        return qualname
    def classname(self):
        """Return the dynamic classname. Can be overwritten."""
        return self.typename()
    def shortname(self):
        return getattr(self, '__name__', '') or "unnamed_{:x}".format(id(self))
    def name(self):
        """Return the loaded name of the instance"""
        name = self.shortname()
        if Config.display.show_parent_name and self.parent is not None:
            return '.'.join([self.parent.name(), name])
        return name
    def instance(self):
        """Returns a minimal string describing the type and it's location"""
        name, ofs = self.classname(), self.getoffset()
        return "{:s}[{:x}:+???]".format(name, ofs)

    def hexdump(self, **options):
        """Return a hexdump of the type using utils.hexdump(**options)

        Options can provide formatting specifiers
        terse -- display the hexdump tersely if larger than a specific threshold
        threshold -- maximum number of rows to display
        """
        offset, width = options.pop('offset', self.getoffset()), options.pop('width', Config.display.hexdump.width)
        return utils.hexdump(self.serialize(), offset=offset, width=width, **options)

    def __details_size__(self, size):
        """Return details of the object clamped to the specified size. This can be displayed in multiple-lines."""
        if not self.initializedQ():
            return u"???"

        buf = self.serialize()
        offset, width = self.getoffset(), Config.display.hexdump.width

        # if larger than threshold...
        threshold, message = Config.display.threshold.details, Config.display.threshold.details_message
        if threshold > 0 and size / width > threshold:
            return '\n'.join(utils.emit_hexrows(buf, threshold, message, offset=offset, width=width))
        return utils.hexdump(buf, offset=offset, width=width)

    def __summary_size__(self, size):
        """Return a summary of the object clamped to the specified size. This can be displayed on a single-line."""
        if self.value is None:
            return u"???"

        #threshold = options.pop('threshold', Config.display.threshold.summary)
        #message = options.pop('threshold_message', Config.display.threshold.summary_message)
        threshold, message = Config.display.threshold.summary, Config.display.threshold.summary_message
        #threshold = options.pop('width', threshold) # 'threshold' maps to 'width' for emit_repr
        offset = self.getoffset()

        if threshold < 0 or size < threshold:
            data = self.serialize()
            return u'"{:s}"'.format(utils.emit_repr(data[:size]))

        # If the size is much smaller than the threshold, then we can use it.
        if size < threshold:
            data = self.serialize() if self.initializedQ() else self.value
            res = utils.emit_repr(data, threshold, message, offset=offset)
            return u'"{:s}"'.format(res)

        # Otherwise, we're a single element and we can trust emit_repr to handle it.
        elif builtins.isinstance(self.value, bytes):
            data = self.serialize() if self.initializedQ() else self.value
            res = utils.emit_repr(data, threshold, message, offset=offset, size=size)
            return u'"{:s}"'.format(res)

        # if there's too much data, the slice it together from both sides.
        lefti, righti = utils.valueaccumulate(self.value, +1), utils.valueaccumulate(self.value, -1)
        _, leftbytes = next(lefti, (0, b''))
        leftitems = [leftbytes] + [item for _, item in itertools.takewhile(lambda offset_data: offset_data[0] < threshold, lefti)]
        _, rightbytes = next(righti, (0, b''))
        rightitems = [rightbytes] + [item for _, item in itertools.takewhile(lambda offset_data: offset_data[0] < threshold, righti)]
        data = bytes().join([bytes().join(leftitems), bytes().join([item for item in rightitems][::-1])])

        # if larger than threshold...
        assert(threshold > 0 and size >= threshold), (size, threshold)
        res = utils.emit_repr(data, threshold, message, offset=offset, size=size)
        return u'"{:s}"'.format(res)

    def details(self):
        try: size = self.size()
        except Exception: size = self.blocksize()
        return self.__details_size__(size)

    def summary(self):
        try: size = self.size()
        except Exception: size = self.blocksize()
        return self.__summary_size__(size)

    #@utils.memoize('self', self='parent', args=lambda item: (item[0],) if len(item) > 0 else (), kwds=lambda item: item.get('type', ()))
    @utils.memoize_method(self='parent', args=frozenset, kwds=lambda item: (item.get('type', ()), item.get('default', ())))
    def getparent(self, *args, **kwds):
        """Returns the creator of the current type.

        If nothing is specified, return the parent element.

        If the ``type`` argument is specified, recursively descend into .parent
        elements until encountering an instance that inherits from the one specified.

        If any arguments are provided, return the element whom either inherits
        from a type provided, or whose .parent matches the requested instance.
        """
        if not len(args) and 'type' not in kwds:
            return kwds.get('default', self.parent) if self.parent is None else self.parent

        # figure out whether we're doing an exact match or a type match
        [query] = args if args else [kwds['type']]
        if isinstance(query) or query is None:
            match = lambda self: lambda query: self.parent is query
        else:
            match = lambda self: lambda query: builtins.isinstance(self, query)

        # check to see if user actually queried for self
        if match(self)(query):
            return self

        # now walk upwards till we find what the user is looking for
        def parents(node):
            return () if node.parent is None else (node.parent,)

        for node in self.traverse(edges=parents):
            if match(node)(query):
                return node
            continue

        # if default was specified in our keywords, then just return that.
        if 'default' in kwds:
            return kwds['default']

        # otherwise, we can bail since it wasn't found.
        raise error.ItemNotFoundError(self, 'base.getparent', message="The requested match ({!r}) was not found while traversing from {:s}.".format(query, self.instance()))
    def backtrace(self, fn=utils.operator.methodcaller('instance')):
        """
        Return a backtrace to the root element applying ``fn`` to each parent

        By default this returns a string describing the type and location of
        each structure.
        """
        path = self.traverse(edges=lambda node: (node.parent for edge in [None] if node.parent is not None))
        path = [ fn(item) for item in path ]
        return list(reversed(path))

    def new(self, t, **attributes):
        """Create a new instance of ``ptype`` with the provided ``attributes``

        If any ``attributes`` are provided, this will assign them to the new instance.
        The newly created instance will inherit the current object's .source and
        any .attributes designated by the current instance.
        """

        recursive = self.attributes.copy()
        recursive.update(attributes.pop('recurse', {}))

        attrs = recursive.copy() if recursive else {}
        attrs.update(attributes)
        attrs.setdefault('recurse', recursive) if recursive else None
        attrs.setdefault('parent', self)

        # instantiate an instance if we're given a type
        if not(istype(t) or isinstance(t)):
            raise error.TypeError(self, 'base.new', message="{!r} is not a ptype class".format(t.__class__))

        # if it's a type, then instantiate it
        if istype(t):
            t = t(**attrs)

        # if already instantiated, then update it's attributes
        elif isinstance(t):
            t.__update__(**attrs)

        # give the instance a default name
        if '__name__' in attrs:
            t.__name__ = attrs['__name__']
        return t

class generic(__interface__):
    '''A class shared between both pbinary.*, ptype.*'''
    def __hash__(self):
        raise error.ImplementationError(self, 'generic.__hash__')
    def initializedQ(self):
        raise error.ImplementationError(self, 'generic.initializedQ')
    def __contains__(haystack, needle):
        raise error.ImplementationError(haystack, 'generic.__contains__')

    def __eq__(self, other):
        '''x.__eq__(y) <==> x==y'''
        return id(self) == id(other)
    def __ne__(self, other):
        '''x.__ne__(y) <==> x!=y'''
        return not(self == other)
    def __bool__(self):
        return True
    __nonzero__ = __bool__
    def __getstate__(self):
        return ()
    def __setstate__(self, state):
        return

    def repr(self):
        """The output that __repr__ displays"""
        raise error.ImplementationError(self, 'generic.repr')

    def __deserialize_block__(self, block):
        """
        This method should only be able to raise exceptions of the types:

            - error.ProviderError
                - error.ConsumeError
                - error.StoreError
            - StopIteration
        """
        raise error.ImplementationError(self, 'generic.__deserialize_block__', message="Subclass {:s} must implement deserialize_block".format(self.classname()))

    def serialize(self):
        raise error.ImplementationError(self, 'generic.serialize')

    def load(self, **attrs):
        raise error.ImplementationError(self, 'generic.load')
    def commit(self, **attrs):
        raise error.ImplementationError(self, 'generic.commit')
    def alloc(self, *values, **attrs):
        """Will zero the ptype instance with the provided ``attrs``.

        This can be overloaded in order to allocate physical space for the new ptype.
        """
        attrs.setdefault('source', provider.empty())
        if values:
            return self.load(**attrs).set(*values)
        return self.load(**attrs)

    # abbreviations
    a = property(lambda self: self.alloc())  # alloc
    c = property(lambda self: self.commit()) # commit
    l = property(lambda self: self.load())   # load
    li = property(lambda self: self.load() if self.value is None else self) # load if uninitialized

    def get(self):
        """Return a representation of a type.

        This value should be able to be passed to .set
        """
        return self.__getvalue__()

    def set(self, *args, **kwds):
        """Set value of type to ``value``.

        Should be the same value as returned by .get
        """
        return self.__setvalue__(*args, **kwds)

    def copy(self):
        """Return a new instance of self"""
        raise error.ImplementationError(self, 'generic.copy')

    def same(self, other):
        """Returns if the other instance occupies the same location of self."""
        if not isinstance(other):
            raise TypeError(other.__class__)
        if self.initializedQ() == other.initializedQ():
            return (self.getposition(), self.serialize()) == (other.getposition(), other.serialize())
        elif self.initializedQ() != other.initializedQ():
            raise error.InitializationError(other if self.initializedQ() else self, 'generic.same')
        return (self.getposition(), self.blocksize()) == (other.getposition(), other.blocksize())

class base(generic):
    padding = utils.padding.source.zero()

    @classmethod
    def __hash__(cls):
        return hash(cls)

    def setoffset(self, offset, **options):
        """Changes the current offset to ``offset``"""
        return self.setposition((offset,), **options)[0]
    def getoffset(self, **options):
        """Returns the current offset"""
        return self.getposition(**options)[0]

    __position__ = 0,
    def setposition(self, position, **kwds):
        (self.__position__, res) = position, (self.__position__) or (0,)
        return res[:]
    def getposition(self):
        return self.__position__[:]

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin + self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    def copy(self, **attrs):
        """Return a duplicate instance of the current one."""
        result = self.new(self.__class__, position=self.getposition())
        if hasattr(self, '__name__'): attrs.setdefault('__name__', self.__name__)
        attrs.setdefault('parent', self.parent)
        if 'value' not in attrs:
            if not builtins.isinstance(self.value, (bytes, builtins.type(None))):
                raise error.AssertionError(self, 'base.copy', message="Invalid type of .value while trying to duplicate object : {!r}".format(self.value.__class__))
            attrs['value'] = None if self.value is None else self.value[:]
        result.__update__(attrs)
        if result.parent is None:
            result.source = self.source
        return result

    def compare(self, other):
        """Returns an iterable containing the difference between ``self`` and ``other``

        Each value in the iterable is composed of (index,(self.serialize(),other.serialize()))
        """
        if False in (self.initializedQ(), other.initializedQ()):
            Log.fatal("base.compare : {:s} : Instance not initialized ({:s})".format(self.instance(), self.instance() if not self.initializedQ() else other.instance()))
            return

        s, o = self.serialize(), other.serialize()
        if s == o:
            return

        comparison = (bool(x^y) for x, y in zip(bytearray(s), bytearray(o)))
        result = [(different, len(list(times))) for different, times in itertools.groupby(comparison)]
        index = 0
        for diff, length in result:
            #if diff: yield index, length
            if diff: yield index, (s[index:index+length], o[index:index+length])
            index += length

        if len(s) != len(o):
            #yield index, max(len(s), len(o))-index
            yield index, (s[index:], '') if len(s) > len(o) else ('', o[index:])
        return

    def cast(self, t, **attrs):
        """Cast the contents of the current instance into a differing ptype"""
        data, size = self.serialize(), self.size()

        # copy attributes that make the new instantiation similar
        attrs.setdefault('offset', self.getoffset())
        attrs.setdefault('parent', self.parent)

        # create the new type with the attributes from our parameters,
        # and extract the blocksize so we can check it if necessary.
        result = self.new(t, **attrs)

        # try and load the contents using the correct blocksize
        try:
            result = result.load(offset=0, source=provider.proxy(self), blocksize=lambda: size)
            result.setoffset(result.getoffset(), recurse=True)

        # this exception occurs when the object we're casting to is
        # larger than the object we're casting from. we actually know
        # this is going to happen as a number of partially initialized
        # types are within our container, but there's no data available
        # to fill them. just in case that this is surprising to the user,
        # tho, we issue a warning.
        except error.ProviderError as E:
            Log.warning("base.cast : {:s} : {:s} : Cast has resulted in a partially initialized instance ({:d} < {:d}) : {!r}".format(self.classname(), t.typename(), result.size(), size, E), exc_info=False)

        # if we get another exception, then it should be a LoadError.
        # this will only happen if the type that we're loading with
        # is actually smaller than what we're loading from. we get
        # a LoadError because there's no way to consume the rest of
        # the data that's available because there's no place to put
        # it. we verify this is the case by checking that the blocksize,
        # of the result is smaller than the size of our source object.
        # if this is the case, then we raise an exception because this
        # scenario should've been caught by ProviderError. If we're in
        # LoadError and the result load size is smaller than what was
        # supposed to have been loaded, then this is an error.
        except error.LoadError as E:
            if result.blocksize() < size:
                raise
            Log.warning("base.cast : {:s} : {:s} : Error during cast resulted in a partially initialized instance : {!r}".format(self.classname(), t.typename(), E), exc_info=True)

        # force partial or overcommited initializations
        try: result = result.__deserialize_block__(data)
        except (StopIteration, error.ProviderError): pass

        # log whether our size has changed somehow
        a, b = self.size(), result.size()
        if a > b:
            Log.info("base.cast : {:s} : Result {:s} size is smaller than source type : {:#x} < {:#x}".format(self.classname(), result.classname(), result.size(), self.size()))
        elif a < b:
            Log.warning("base.cast : {:s} : Result {:s} is partially initialized : {:#x} > {:#x}".format(self.classname(), result.classname(), result.size(), self.size()))
        return result

    def traverse(self, edges=lambda node:tuple(node.value) if builtins.isinstance(node, container) else (), filter=lambda node:True, **kwds):
        """
        This will traverse a tree in a top-down approach.

        By default this will traverse every sub-element from a given object.
        """
        return super(base, self).traverse(edges, filter, **kwds)

    def new(self, ptype, **attrs):
        res = force(ptype, self)
        return super(base, self).new(res, **attrs)

    def load(self, **attrs):
        """Synchronize the current instance with data from the .source attributes"""
        with utils.assign(self, **attrs):
            source, offset, blocksize = self.source, self.getoffset(), self.blocksize()

            # seek to the correct offset that we'll be consuming from.
            source.seek(offset)
            try:
                block = source.consume(blocksize)
                self = self.__deserialize_block__(block)

            # if we got an exception from the provider, then recast it
            # as a load error since the block was not read completely.
            except error.ConsumeError as E:
                source.seek(offset + blocksize)
                provider, offset, requested, successful = E.consumed
                raise error.LoadError(self, successful, offset=offset)

            # if we got an exception while deserializing, then recast it
            # as a load error since the block was interrupted.
            except (StopIteration, error.ProviderError):
                source.seek(offset + blocksize)
                raise error.LoadError(self, consumed=blocksize)
        return self

    def commit(self, **attrs):
        """Commit the current state back to the .source attribute"""
        try:
            with utils.assign(self, **attrs):
                source, ofs, data = self.source, self.getoffset(), self.serialize()
                source.seek(ofs)
                source.store(data)
            return self

        except error.StoreError as E:
            provider, offset, requested, successful = E.stored
            raise error.CommitError(self, successful, offset=offset)

        except (StopIteration, error.ProviderError):
            raise error.CommitError(self)

    def collect(self, *args, **kwds):
        global encoded_t
        class parentTester(object):
            def __eq__(self, other):
                return other.parent is None or builtins.isinstance(other, encoded_t)
        parentTester = parentTester()

        #edges = lambda node:tuple(node.value) if iscontainer(node.__class__) else ()
        #encoded = lambda node: (node.d,) if builtins.isinstance(node, encoded_t) else ()
        #itertools.chain(self.traverse(edges, filter=filter, *args, **kwds), self.traverse(encoded, filter=filter, *args, **kwds)):
        duplicates = set()
        if parentTester == self:
            yield self
        duplicates.add(self)
        for item in self.traverse(filter=lambda n: parentTester == n):
            if item.parent is None:
                if item not in duplicates:
                    yield item
                    duplicates.add(item)
                continue
            try:
                result = item.d.l
            except Exception:
                continue
            if result not in duplicates:
                yield result
                duplicates.add(result)
            for item in result.collect():
                result = item.getparent(parentTester)
                if result not in duplicates:
                    yield result
                    duplicates.add(result)
                continue
            continue
        return

class type(base):
    """The most atomical type.. all container types are composed of these.

    Contains the following settable properties:
        length:int<w>
            size of ptype
        source:ptypes.provider<rw>
            source of input for ptype

    Readable properties:
        value:str<r>
            contents of ptype

        parent:subclass(ptype.type)<r>
            the ptype that created us

        initialized:bool(r)
            if ptype has been initialized yet
    """
    ignored = generic.__slots__['ignored'] | {'length'}

    def __hash__(self):
        return super(type, self).__hash__() ^ hash(self.value)

    def copy(self, **attrs):
        result = super(type, self).copy(**attrs)

        # Explicitly copy the length if it wasn't copied properly. We
        # check its value first because "length" might be a property.
        if hasattr(self, 'length') and result.length != self.length:
            result.length = self.length
        return result

    def instance(self):
        """Returns a minimal string describing the type and it's location"""
        name, ofs = self.classname(), self.getoffset()
        if self.value is None:
            return super(type, self).instance()
        bs = self.blocksize()
        return "{:s}[{:x}:{:+x}]".format(name, ofs, bs)

    def initializedQ(self):
        return True if self.value is not None and len(self.value) >= self.blocksize() else False

    ## byte stream input/output
    def __deserialize_block__(self, block):
        """Load type using the string provided by ``block``"""
        blocksize = self.blocksize()
        if len(block) < blocksize:
            self.value = block[:blocksize]
            raise StopIteration(self, len(block), blocksize)

        # all is good.
        self.value = block[:blocksize]
        return self

    def serialize(self):
        """Return contents of type as a string"""

        # if we're not initialized, then return a padded value up to the blocksize
        if self.value is None or not self.initializedQ():
            res = self.blocksize()

            # FIXME: this should definitely be clamped to a maximum size
            try:
                parent = self.getparent(encoded_t)
            except error.ItemNotFoundError:
                parent = self.getparent(None)

            # check if child element is child of encoded_t or we're a proxy since neither needs to get checked since the types aren't guaranteed to be related
            if builtins.isinstance(parent, encoded_t) or builtins.isinstance(self.source, provider.proxy):
                pass

            # check that child element is actually within bounds of parent
            elif parent is not None and parent.getoffset() > self.getoffset():
                Log.info("type.serialize : {:s} : child element is outside the bounds of parent element {:s}. : {:#x} > {:#x}".format(self.instance(), parent.instance(), parent.getoffset(), self.getoffset()))

            # clamp the blocksize if it pushes the child element outside the bounds of the parent
            elif builtins.isinstance(parent, container):
                parentSize = parent.blocksize()
                childOffset = self.getoffset() - parent.getoffset()
                maxElementSize = parentSize - childOffset
                if res > maxElementSize:
                    Log.warning("type.serialize : {:s} : blocksize is outside the bounds of parent element {:s}. Clamping according to parent's maximum : {:#x} > {:#x} : {:#x}".format(self.instance(), parent.instance(), res, maxElementSize, parentSize))
                    res = maxElementSize

            if res > sys.maxsize:
                Log.fatal("type.serialize : {:s} : blocksize is larger than maximum size. Refusing to add padding : {:#x} > {:#x}".format(self.instance(), res, sys.maxsize))
                return b''

            # generate padding up to the blocksize
            needed = res - len(self.value or b'')
            if needed:
                Log.debug("type.serialize : {:s} : Padding data by {:+#x} bytes due to element being uninitialized during serialization.".format(self.instance(), needed))
            padding = utils.padding.fill(needed if needed > 0 else 0, self.padding)

            # prefix beginning of padding with any data that element contains
            return padding if self.value is None else self.value + padding

        # take the current value as a string, which should match up to .size()
        data = self.value

        # pad up to the .blocksize() if our length doesn't meet the minimum
        res = self.blocksize()
        if len(data) < res:
            Log.debug("type.serialize : {:s} : Padding data by {:+#x} bytes due to element being partially initialized during serialization ({:d} < {:d}).".format(self.instance(), res, len(data), res))
            padding = utils.padding.fill(res-len(data), self.padding)
            data += padding
        return data

    ## set/get
    def __setvalue__(self, *values, **attrs):
        """Set entire type equal to ``value`` if defined."""
        if not values: return self

        [value] = values
        if not builtins.isinstance(value, (bytes, bytearray)):
            raise error.TypeError(self, 'type.set', message="provided value {!r} is not serialized data".format(value.__class__))

        # get the trim length from attrs or our own attributes if it's there.
        length = attrs.get('length', getattr(self, 'length', None))
        data = bytes(value) if builtins.isinstance(value, bytearray) else value[:]
        if length is None:
            self.value = data

        # pad the setting if it's necessary
        else:
            padding = utils.padding.fill(length, self.padding)
            self.value = data + padding[len(data):]

        return self

    def __getvalue__(self):
        return self.serialize()

    ## size boundaries
    def size(self):
        """Returns the number of bytes that have been loaded into the type.

        This excludes any required padding that is included during serialization.
        If type is uninitialized, issue a warning and return 0.
        """
        length = getattr(self, 'length', None)
        if self.value is not None:
            return len(self.value) if length is None else len(self.value)
        Log.info("type.size : {:s} : Unable to determine (real) size with {!s}, as object is still uninitialized.".format(self.instance(), type.typename()))
        return 0

    def __blocksize_originalQ__(self):
        '''Return whether the instance's blocksize has been rewritten by a definition.'''
        cls = self.__class__
        return utils.callable_eq(self, self.blocksize, cls, cls.blocksize) and utils.callable_eq(cls, cls.blocksize, type, type.blocksize)
    def blocksize(self):
        """Returns the expected size of the type that is needed to load it.

        By default this returns self.length, but can be overloaded to define the
        size of the type. This *must* return an integral type.
        """

        # XXX: overloading will always provide a side effect of modifying the .source's offset
        #        make sure to fetch the blocksize first before you .getoffset() on something.
        blocksize = getattr(self, 'length', None)
        if blocksize is None:
            return 0 if self.value is None else len(self.value)
        return blocksize

    ## operator overloads
    def repr(self):
        """Display all ptype.type instances as a single-line hexstring"""
        return self.summary() if self.value is not None else '???'

    def __getstate__(self):
        return (super(type, self).__getstate__(), self.blocksize(), self.value,)
    def __setstate__(self, state):
        state, self.length, self.value = state
        super(type, self).__setstate__(state)

    def details(self):
        try: size = self.size() if getattr(self, 'length', None) is None else self.length
        except Exception: size = self.blocksize()
        return self.__details_size__(size)

    def summary(self):
        try: size = self.size() if getattr(self, 'length', None) is None else self.length
        except Exception: size = self.blocksize()
        return self.__summary_size__(size)

class container(base):
    '''
    This class is capable of containing other ptypes

    Readable properties:
        value:str<r>
            list of all elements that are being contained
    '''

    def __hash__(self):
        return super(container, self).__hash__() ^ hash(None if self.value is None else tuple(self.value))

    def __contains__(self, instance):
        if isinstance(instance):
            return any(item is instance for item in self.value or [])
        return super(container, self).__contains__(instance)

    def instance(self):
        """Returns a minimal string describing the type and it's location"""
        cls, name, ofs = self.__class__, self.classname(), self.getoffset()
        if self.value is None:
            return super(container, self).instance()
        try:
            if self.initializedQ():
                bs = self.size()
            elif utils.callable_eq(self, self.blocksize, cls, cls.blocksize):
                return super(container, self).instance()
            else:
                bs = self.blocksize()

        except Exception:
            return super(container, self).instance()
        return "{:s}[{:x}:{:+x}]".format(name, ofs, bs)

    def initializedQ(self):
        """True if the type is fully initialized"""
        if self.value is None:
            return False
        return all(item is not None and item.initializedQ() for item in self.value)

    def size(self):
        """Returns a sum of the number of bytes that are currently in use by all sub-elements"""
        iterable = self.value or []
        return sum(item.size() for item in iterable if item.value is not None)

    def __blocksize_originalQ__(self):
        '''Return whether the instance's blocksize has been rewritten by a definition.'''
        cls = self.__class__
        return utils.callable_eq(self, self.blocksize, cls, cls.blocksize) and utils.callable_eq(cls, cls.blocksize, container, container.blocksize)
    def blocksize(self):
        """Returns a sum of the bytes that are expected to be read"""
        if self.value is None:
            raise error.InitializationError(self, 'container.blocksize')
        return sum(item.blocksize() for item in self.value)

    def getoffset(self, *field):
        """Returns the current offset.

        If ``field`` is specified as a ``str``, return the offset of the
        sub-element with the provided name. If specified as a ``list`` or
        ``tuple``, descend into sub-elements using ``field`` as the path.
        """
        if not len(field):
            return super(container, self).getoffset()
        (field,) = field

        # if a path is specified, then recursively get the offset
        if builtins.isinstance(field, (tuple, list)):
            (name, res) = (lambda hd, *tl:(hd, tl))(*field)
            return self[name].getoffset(res) if len(res) > 0 else self.getoffset(name)

        index = self.__getindex__(field)
        return self.getoffset() + sum(map(utils.operator.methodcaller('size'), self.value[:index]))

    def __getindex__(self, name):
        """Searches the .value attribute for an element with the provided ``name``

        This is intended to be overloaded by any type that inherits from
        ptype.container.
        """
        raise error.ImplementationError(self, 'container.__getindex__', 'Developer forgot to overload this method')

    def __field__(self, key):
        index = self.__getindex__(key)
        if self.value is None:
            raise error.InitializationError(self, 'container.__field__')
        return self.value[index]
    def __getitem__(self, key):
        '''x.__getitem__(y) <==> x[y]'''
        return self.__field__(key)

    def __setitem__(self, index, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        if not builtins.isinstance(value, base):
            raise error.TypeError(self, 'container.__setitem__', message='Cannot assign a non-ptype to an element of a container. Use .set instead.')
        if self.value is None:
            raise error.InitializationError(self, 'container.__setitem__')
        offset = self.value[index].getoffset()
        value.setoffset(offset, recurse=True)
        value.parent, value.source = self, None
        self.value[index] = value
        return value

    def at(self, offset, recurse=True, **kwds):
        """Returns element that contains the specified offset

        If ``recurse`` is True, then recursively descend into all sub-elements
        until an atomic type (such as ptype.type, or pbinary.partial) is encountered.
        """
        if not self.contains(offset):
            raise error.ItemNotFoundError(self, 'container.at', "offset {:#x} can not be located within container.".format(offset))

        # if we weren't asked to recurse, then figure out which sub-element contains the offset
        if not recurse:
            for item in self.value:
                if item.contains(offset):
                    return item
                continue
            raise error.ItemNotFoundError(self, 'container.at', "offset {:#x} not found in a child element. returning encompassing parent.".format(offset))

        # descend into the trie a single level
        try:
            res = self.at(offset, recurse=False, **kwds)

        except ValueError as E:
            Log.info("container.at : {:s} : Non-fatal exception raised : {!r}".format(self.instance(), E), exc_info=True)
            return self

        # if we're already at a leaf of the trie, then no need to descend
        if builtins.isinstance(res, (type, pbinary.partial)):
            return res

        # drill into the trie's elements for more detail
        try:
            return res.at(offset, recurse=recurse, **kwds)
        except (error.ImplementationError, AttributeError):
            pass
        return res

    def field(self, *keys):
        '''Returns the field that is indexed with the specified keys.'''
        get_field = lambda object, field: object.__field__(field) if hasattr(object, '__field__') else operator.getitem(object, field)
        return functools.reduce(get_field, keys, self)

    def setoffset(self, offset, recurse=False):
        """Changes the current offset to ``offset``

        If ``recurse`` is True, the update all offsets in sub-elements.
        """
        return self.setposition((offset,), recurse=recurse)[0]

    def setposition(self, offset, recurse=False):
        res = super(container, self).setposition(offset, recurse=recurse)
        if recurse and self.value is not None:
            ofs = offset[0]
            for item in self.value:
                item.setposition((ofs,), recurse=recurse)
                ofs += item.size() if item.initializedQ() else item.blocksize()
            return res
        return res

    def __deserialize_block__(self, block):
        """Load type using the string provided by ``block``"""
        if self.value is None:
            raise error.SyntaxError(self, 'container.__deserialize_block__', message='caller is responsible for allocation of elements in self.value')

        # read everything up to the blocksize
        value, expected, total = self.value[:], self.blocksize(), 0
        while value and total < expected:
            res = value.pop(0)
            bs = res.blocksize()
            res.__deserialize_block__(block[:bs])
            block = block[bs:]
            total += bs

        # ..and then fill out any zero sized elements to update any state
        while value:
            res = value.pop(0)
            bs = res.blocksize()
            if bs > 0: break
            res.__deserialize_block__(block[:bs])

        # log any information about deserialization errors
        if total < expected:
            Log.warning("container.__deserialize_block__ : {:s} : Deserialized container size ({:#x}) is less than the expected blocksize ({:#x}).".format(self.instance(), total, expected))

        elif total > expected:
            Log.warning("container.__deserialize_block__ : {:s} : Deserialized container size ({:#x}) is larger than the expected blocksize ({:#x}).".format(self.instance(), total, expected))
        return self

    def serialize(self):
        """Return contents of all sub-elements concatenated as a string"""
        # check the blocksize(), if it's invalid then return what we have since we can't figure out the padding anyways
        try:
            res = self.blocksize()
        except Exception:
            return b''.join(map(utils.operator.methodcaller('serialize'), iter(self.value)))

        # if there's no blocksize, then this field is empty
        if res <= 0: return b''

        # serialize all the elements that we currently have
        data = b''.join(map(utils.operator.methodcaller('serialize'), iter(self.value)))

        try:
            parent = None if self.parent is None else self.getparent(encoded_t)
        except error.ItemNotFoundError:
            parent = self.getparent(None)

        # check to see if we should validate ourselves according to parent's boundaries
        if parent is None or not builtins.isinstance(parent.value, list) or self not in parent.value:
            return data

        # check if child element is child of encoded_t which doesn't get checked since encoded types can have their sizes changed.
        if builtins.isinstance(parent, encoded_t):
            pass

        # check that child element is actually within bounds of parent
        elif parent is not None and parent.getoffset() > self.getoffset():
            Log.info("container.serialize : {:s} : child element is outside the bounds of parent element {:s}. : {:#x} > {:#x}".format(self.instance(), parent.instance(), parent.getoffset(), self.getoffset()))

        # clamp the blocksize if we're outside the bounds of the parent
        elif builtins.isinstance(parent, container):
            parentSize = parent.blocksize()
            childOffset = self.getoffset() - parent.getoffset()
            maxElementSize = parentSize - childOffset
            if res > maxElementSize:
                Log.warning("container.serialize : {:s} : blocksize is outside the bounds of parent element {:s}. Clamping according to the parent's maximum : {:#x} > {:#x} : {:#x}".format(self.instance(), parent.instance(), res, maxElementSize, parentSize))
                res = maxElementSize

        # if the blocksize is larger than maxsize, then ignore the padding
        if res > sys.maxsize:
            Log.warning("container.serialize : {:s} : blocksize is larger than maximum size. Refusing to add padding : {:#x} > {:#x}".format(self.instance(), res, sys.maxsize))
            return data

        # if the data is smaller then the blocksize, then pad the rest in
        if len(data) < res:
            Log.debug("container.serialize : {:s} : Padding data by {:+#x} bytes due to element being partially uninitialized during serialization.".format(self.instance(), res))
            data += utils.padding.fill(res - len(data), self.padding)

        # if it's larger then the blocksize, then warn the user about it
        if len(data) > res:
            Log.debug("container.serialize : {:s} : Container larger than expected blocksize : {:#x} > {:#x}".format(self.instance(), len(data), res))

        # otherwise, our data should appear correct
        return data

    def load(self, **attrs):
        """Allocate the current instance with data from the .source attributes"""
        if self.value is None and 'value' not in attrs:
            raise error.UserError(self, 'container.load', message='Parent must initialize self.value')

        try:
            # if any of the sub-elements are undefined, load each element separately
            if Config.ptype.noncontiguous and \
                    any(builtins.isinstance(item, container) or builtins.isinstance(item, undefined) for item in self.value):
                # load each element individually up to the blocksize
                bs, value = 0, self.value[:]
                left, right = self.getoffset(), self.getoffset()+self.blocksize()
                while value and left < right:
                    res = value.pop(0)
                    bs, ofs = res.blocksize(), res.getoffset()
                    left = res.getoffset() if left + bs < ofs else left + bs
                    res.load(**attrs)

                # ..and then load any zero-sized elements that were left to update state
                while value:
                    res = value.pop(0)
                    if res.blocksize() > 0: break
                    res.load(**attrs)
                return self

            # otherwise the contents are contiguous, load them as so
            return super(container, self).load(**attrs)

        # we failed out, log what happened according to the variable state
        except error.LoadError as E:
            ofs, s, bs = self.getoffset(), self.size(), self.blocksize()
            self.source.seek(ofs+bs)
            if s > 0 and s < bs:
                Log.warning("container.load : {:s} : Unable to complete read at {{{:x}:{:+x}}} : {!r}".format(self.instance(), ofs, s, E))
            else:
                Log.debug("container.load : {:s} : Cropped to {{{:x}:{:+x}}} : {!r}".format(self.instance(), ofs, s, E))

            ## and then re-raise because there's no more data left...
            #raise error.LoadError(self, consumed=s, offset=ofs)

            # XXX: the re-raising of the prior exception has been commented-out in
            #      order to test out partially-initialized containers. this was
            #      actually an unintended hack and there's a chance it might work.
            return self
        return self

    def commit(self, **attrs):
        """Commit the current state of all children back to the .source attribute"""
        if not Config.ptype.noncontiguous and \
                all(not (builtins.isinstance(item, container) or builtins.isinstance(item, undefined)) for item in self.value):

            try:
                return super(container, self).commit(**attrs)
            except error.CommitError as E:
                Log.warning("container.commit : {:s} : Unable to complete contiguous store : write at {{{:x}:{:+x}}} : {!s}".format(self.instance(), self.getoffset(), self.size(), E))

        # commit all elements of container individually
        offset = self.getoffset()
        with utils.assign(self, **attrs):
            current, newoffset, size = 0, self.getoffset(), self.size()
            try:
                for item in self.value:
                    item.commit(source=self.source) if offset == newoffset else item.commit(source=self.source, offset=item.getoffset() - offset + newoffset)
                    current += item.size()
                    if current > size: break
                pass
            except error.CommitError as E:
                Log.fatal("container.commit : {:s} : Unable to complete non-contiguous store : write stopped at {{{:x}:{:+x}}} : {!r}".format(self.instance(), newoffset+current, self.blocksize()-current, E))
        return self

    def copy(self, **attrs):
        """Performs a deep-copy of self repopulating the new instance if self is initialized"""
        attrs.setdefault('value', [])
        attrs.setdefault('parent', self.parent)
        # create an empty instance of self and update with requested attributes
        res = super(container, self).copy(**attrs)

        # now copy the children, with the same parent
        res.value = [ item.copy(parent=res) for item in self.value or [] ]
        return res

    def compare(self, other, *args, **kwds):
        """Returns an iterable containing the difference between ``self`` and ``other``

        Each value in the iterable is composed of (index,(self,other)). Any
        extra arguments are passed to .getparent in order to only return
        differences in elements that are of a particular type.
        """
        if False in {self.initializedQ(), other.initializedQ()}:
            Log.fatal("container.compare : {:s} : Instance not initialized ({:s})".format(self.instance(), self.instance() if not self.initializedQ() else other.instance()))
            return

        if self.value == other.value:
            return

        def between(object, bounds):
            (left, right) = bounds

            objects = provider.proxy.collect(object, left, right)
            mapped = [ item.getparent(*args, **kwds) if kwds else item for item in objects ]
            for item, _ in itertools.groupby(mapped):
                if left + item.size() <= right:
                    yield item
                left += item.size()
            return

        for ofs, (s, o) in super(container, self).compare(other):
            if len(s) == 0:
                i = other.value.index(other.at(other.getoffset() + ofs, recurse=False))
                yield ofs, (None, tuple(between(other, (ofs, other.blocksize()))))
            elif len(o) == 0:
                i = self.value.index(self.at(self.getoffset() + ofs, recurse=False))
                yield ofs, (tuple(between(self, (ofs, self.blocksize()))), None)
            else:
                if len(s) != len(o):
                    raise error.AssertionError(self, 'container.compare', message="Invalid length between both objects : {:x} != {:x}".format(len(s), len(o)))
                length = len(s)
                s, o = (between(o, (ofs, ofs+length)) for o in (self, other))
                yield ofs, (tuple(s), tuple(o))
            continue
        return

    def __properties__(self):
        cls, result = self.__class__, super(container, self).__properties__()

        # if we're a container, then we need to check for uninitialized members
        # which can happen if an atomic member's underloaded (size < blocksize)
        if not result.get('uninitialized', False) and not self.initializedQ():
            result['uninitialized'] = True
        return result

    def repr(self):
        """Display all ptype.container types as a hexstring"""
        if self.initializedQ():
            return self.summary()
        threshold, message = Config.display.threshold.summary, Config.display.threshold.summary_message
        if self.value is not None:
            lefti, righti = utils.valueaccumulate(self.value, +1), utils.valueaccumulate(self.value, -1)
            _, leftbytes = next(lefti, (0, b''))
            leftitems = [leftbytes] + [item for _, item in itertools.takewhile(lambda offset_data: offset_data[0] < threshold, lefti)]
            _, rightbytes = next(righti, (0, b''))
            rightitems = [rightbytes] + [item for _, item in itertools.takewhile(lambda offset_data: offset_data[0] < threshold, righti)]
            data = bytes().join([bytes().join(leftitems), bytes().join([item for item in rightitems][::-1])])
            return u"\"{:s}\"".format(utils.emit_repr(data, threshold, message, size=self.size())) if len(data) > 0 else u"???"
        return u"???"

    def __append__(self, object):
        '''Append the specified ``object`` to ``self`` and then return it.'''

        # if we're uninitialized, then create an empty value and try again
        if self.value is None:
            self.value = []
            return self.__append__(object)

        # if object is not an instance, then try to resolve it to one and try again
        if not isinstance(object):
            res = self.new(object)
            return self.__append__(res)

        # assume that object is now a ptype instance
        object.parent, object.source = self, None

        offset = self.getoffset() + self.size()
        self.value.append(object if object.initializedQ() else object.a)
        return object

    def __len__(self):
        '''x.__len__() <==> len(x)'''
        return len(self.value)

    def __iter__(self):
        '''x.__iter__() <==> iter(x)'''
        if self.value is None:
            raise error.InitializationError(self, 'container.__iter__')

        for res in self.value:
            yield res
        return

    def __setvalue__(self, *items, **attrs):
        """Set ``self`` with instances or copies of the types provided in the iterable ``items``.

        If uninitialized, this will make a copy of all the instances in ``items`` and update the
        'parent' and 'source' attributes to match. All the offsets will be
        recursively updated.

        If initialized, this will pass the argument to .set using the current contents.

        This is an internal function and is not intended to be used outside of ptypes.
        """
        if self.initializedQ() and len(self.value) == len(items):
            for idx, (value, item) in enumerate(zip(self.value, items)):
                name = getattr(value, '__name__', None)
                if isresolveable(item) or istype(item):
                    self.value[idx] = self.new(item, __name__=name).a
                elif isinstance(item):
                    self.value[idx] = self.new(item, __name__=name)
                elif builtins.isinstance(item, dict):
                    value.set(**item)
                else:
                    value.set(item)
                continue
        elif all(isresolveable(item) or istype(item) or isinstance(item) for item in items):
            self.value = [ self.new(item) if isinstance(item) else self.new(item).a for item in items ]
        else:
            raise error.AssertionError(self, 'container.set', message="Invalid number or type of elements to assign with : {!r}".format(items))

        # Re-calculate all our offsets after applying our value iterable
        self.setoffset(self.getoffset(), recurse=True)

        return self

    def __getvalue__(self):
        return tuple((res.get() for res in self.value))

    def __getstate__(self):
        return (super(container, self).__getstate__(), self.source, self.attributes, self.ignored, self.parent, self.position)
    def __setstate__(self, state):
        state, self.source, self.attributes, self.ignored, self.parent, self.position = state
        super(container, self).__setstate__(state)

class block(type):
    """A ptype that can be accessed as an array"""
    length = None
    def initializedQ(self):
        return False if self.value is None else True
    def __getitem__(self, index):
        '''x.__getitem__(y) <==> x[y]'''
        if not builtins.isinstance(index, slice):
            if index < 0:
                shift = len(self.value) + index
                res = slice(shift, shift + 1)
            else:
                res = slice(index, index + 1)
            if res.start >= 0 and res.stop <= len(self.value):
                return self.__getitem__(res)
            raise IndexError(index)
        return self.value[index]
    def repr(self):
        """Display all ptype.block instances as a hexdump"""
        if not self.initializedQ():
            return u"???"
        if self.blocksize() > 0:
            return self.details() + '\n'
        return self.summary()
    def summary(self):
        if self.initializedQ():
            return '...' if self.length is None and self.size() == 0 else "({:d}) {:s}".format(self.size(), super(block, self).summary())
        return super(block, self).summary()
    def __setvalue__(self, *values, **attrs):
        """Set entire type equal to ``value``"""
        if not values:
            return super(block, self).__setvalue__(*values, **attrs)
        [value] = values
        return super(block, self).__setvalue__(value, **attrs)

    def __setitem__(self, index, value):
        if not builtins.isinstance(index, slice):
            if index < 0:
                shift = len(self.value) + index
                res = slice(shift, shift + len(value))
            else:
                res = slice(index, index + len(value))
            if res.start >= 0 and res.stop <= len(self.value):
                return self.__setitem__(res, value)
            raise IndexError(index)
        res = bytearray(self.value)
        res[index] = value
        self.value = bytes(res)

    def __format__(self, spec):
        if self.value is None or not spec:
            return super(block, self).__format__(spec)

        prefix, spec = spec[:-1], spec[-1:]
        if spec in 's':
            summary = super(block, self).summary()
            return "{:{:s}{:s}}".format(summary, prefix, spec)
        elif prefix in {'', '#'} and spec in 'xX':
            string, Fcase = "{:{:s}{:s}}".format(0, prefix, spec)[:-1], operator.methodcaller({'x': 'lower', 'X': 'upper'}[spec])
            data = self.serialize()
            hexed = data.encode('hex') if sys.version_info.major < 3 else bytearray(data).hex()
            return string + Fcase(hexed)
        elif spec in 'xX':
            data = bytearray(self.serialize())
            integer = functools.reduce(lambda agg, byte: pow(2, 8) * agg + byte, data, 0)
            string_prefix = ''.join(char for char in prefix if char != '#')
            hex_prefix, length = ('#', 2 + 2 * len(data)) if '#' in prefix else ('', 2 * len(data))
            res = "{:{:s}0{:d}{:s}}".format(integer, hex_prefix, length, spec)
            return "{:{:s}s}".format(res, string_prefix)

        return super(block, self).__format__(prefix + spec)

class undefined(block):
    """An empty ptype that is pretty much always empty...except when it's not."""
    length = 0
    def __init__(self, **attrs):
        return super(undefined, self).__init__(**attrs)
    def initializedQ(self):
        return True if self.blocksize() <= len(self.value or b'') else False
    def serialize(self):
        return self.value or b''
    def summary(self):
        return '...' if self.value is not None and not len(self.value) else super(undefined, self).summary()
    repr = details = summary
    def size(self):
        return self.blocksize()
    def load(self, **attrs):
        with utils.assign(self, **attrs):
            source, offset, blocksize = self.source, self.getoffset(), self.blocksize()
            source.seek(offset)
            self.value = self.source.consume(min(blocksize, source.size() - offset)) if builtins.isinstance(self.source, provider.bounded) and offset < self.source.size() else b''
            #self.value = b''
            source.seek(offset + blocksize)
        return self

#@utils.memoize('cls', newattrs=lambda n:tuple(sorted(n().items())))
def clone(cls, **newattrs):
    '''
    will clone a class, and set its attributes to **newattrs
    intended to aid with single-line coding.
    '''
    class _clone(cls):
        __doc__ = getattr(cls, '__doc__', '')
        def classname(self):
            cn = super(_clone, self).classname()
            return Config.ptype.clone_name.format(cn, **(utils.attributes(self) if Config.display.mangle_with_attributes else {}))

    if newattrs.get('__name__', None) is None:
        newattrs['__name__'] = cls.__name__
        newattrs.setdefault('__qualname__', cls.__qualname__) if hasattr(cls, '__qualname__') else None

    if hasattr(cls, '__module__'):
        newattrs.setdefault('__module__', cls.__module__)

    ignored = cls.ignored if hasattr(cls, 'ignored') else set()
    recurse = dict(newattrs.pop('recurse', {}))

    # update class with all attributes
    res = {}
    res.update(recurse)
    res.update(newattrs)
    for k, v in res.items():
        setattr(_clone, k, v)

    # filter out ignored attributes from recurse dictionary
    recurse = {k : v for k, v in recurse.items() if k not in ignored}

    def slot_getter(t, name, *default):
        res = getattr(t, name, *default)
        if builtins.isinstance(res, (property.fset.__class__, types.MemberDescriptorType)):
            return t.__slots__.get(name, *default)
        return res

    if hasattr(_clone, 'attributes'):
        _clone.attributes = slot_getter(_clone, 'attributes', None) or {}
        _clone.attributes.update(recurse)
    return _clone

class definition(object):
    """Used to store ptype definitions that are determined by a specific value

    This object should be used to simplify returning a ptype that is
    identified by a 'type' value which is commonly used in file formats
    that use a (type,length,value) tuple as their containers.

    To use this properly, in your definition file create a class that inherits
    from ptype.definition, and assign an empty dictionary to the `.cache`
    variable. The .attribute property defines which attribute to key the
    definition by. This defualts to 'type'

    Another thing to define is the `.default` property. This will be the
    default type that is returned when an identifier is not located in the
    cache that was defined.

    i.e.
    class mytypelookup(ptype.definition):
        cache = {}
        default = ptype.block
        attribute = 'type'

    In order to add entries to the cache, one can use the `.add` classmethod
    to add a ptype-entry to the cache by a specific type. However, it is
    recommended to use the `.define` method which takes it's lookup-key from
    the `.type` property.

    @mytypelookup.define
    class myptype(ptype.type):
        type = 66
        length = 10

    With this we can query the cache via `.lookup`, or `.get`.
    The `.get` method is guaranteed to always return a type.
    optionally one can assign attributes to a clone of the
    fetched type.

    i.e.
    theptype = mytypelookup.lookup(66)

    or

    class structure(pstruct.type):
        def __value(self):
            id = self['type'].int()
            thelength = self['length'].int()
            return myptypelookup.get(id, length=thelength)

        _fields_ = [
            (uint32_t, 'type'),
            (uint32_t, 'size')
            (__value, 'unknown')
        ]
    """

    cache = None        # children must assign this empty dictionary at definition time
    attribute = 'type'

    class default(block):
        '''The default type to return when a type is not found within a definition.'''

        @classmethod
        def typename(cls):
            return '.'.join([__name__, 'unknown'])

    @classmethod
    def __default__(cls, **kwargs):
        """Overloadable: Return the default type to use when a matching instance could not be found.

        By default, the implementation's `default` attribute is returned.
        """
        res = cls.default
        return clone(res, **kwargs) if kwargs else res

    @classmethod
    def __key__(cls, type, **kwargs):
        """Overloadable: Return a unique key for the specified ``type`` that can be used to fetch the item.

        By default, the `attribute` key of the implementation is used to fetch a unique attribute from the type.
        """
        return getattr(type, cls.attribute)

    @classmethod
    def __set__(cls, key, object, **kwargs):
        '''Overloadable: Update the current state of the definition to map the specified ``key`` to the specified ``object``.'''
        if cls.has(key, **kwargs):
            original, new = cls.cache[key], object
            Log.warning("definition.__set__ : {:s} : Overwriting definition ({:s}) for key {!r} with new definition ({:s})".format('.'.join([cls.__module__, cls.__name__]), '.'.join([original.__module__, original.__name__]), key, '.'.join([new.__module__, new.__name__])))
        return utils.operator.setitem(cls.cache, key, object)

    @classmethod
    def __get__(cls, key, default, **kwargs):
        '''Overloadable: Return the object for a specified ``key``. If not found, then return ``default``.'''
        try:
            result = utils.operator.getitem(cls.cache, key)

        except KeyError:
            result = default
        return result

    @classmethod
    def __del__(cls, key, **kwargs):
        '''Overloadable: Remove the object for the specified ``key``, and return it.'''
        res, _ = utils.operator.getitem(cls.cache, key), utils.operator.delitem(cls.cache, key)
        return res

    @classmethod
    def add(cls, key, object, **kwargs):
        """Add ``object`` to cache using the key that is specified by ``key``."""
        DictType = types.DictType if sys.version_info[0] < 3 else builtins.dict
        if not builtins.isinstance(cls.cache, DictType):
            raise error.TypeError(cls, 'definition.add', message="{:s} has an invalid type for the .cache attribute ({!r})".format(cls.__name__, cls.cache.__class__))
        return cls.__set__(key, object, **kwargs) or object

    @classmethod
    def define(cls, *args, **attributes):
        """Add a definition to the cache keyed by the .type attribute of the definition. Return the original definition.

        If any ``attributes`` are defined, the definition is duplicated with the specified attributes before being added to the cache.
        """
        if len(args) > 1:
            raise error.UserError(cls, 'definition.define', message="Unexpected number of positional arguments ({:d} given)".format(len(args)))

        # define some closures that we can depend on to update the cache.
        def add(object, **attributes):
            key = cls.__key__(object)
            return cls.add(key, object, **attributes) or object

        def clone(definition, attributes):
            newattributes = {key : definition.__dict__[key] for key in definition.__dict__}
            newattributes.update(attributes)

            # if there were some attributes provided, then we need to clone
            # the definition we were given when adding, and return the
            # original type.
            if attributes:
                name = newattributes.pop('__name__', definition.__name__)
                object = builtins.type(name, (definition,), newattributes)
                return add(object, **newattributes) and definition

            # otherwise, we can just return the original.
            return add(definition)

        # if we received only 1 argument, then this is all we need to define.
        if len(args) == 1:
            return add(*args, **attributes)

        # anything else means that we received our parameters, and so the only way to
        # get our definition that's being decorated is by returning a closure.
        return functools.partial(clone, attributes=attributes)

    @classmethod
    def lookup(cls, *args, **kwargs):
        """D.lookup(type[, default]) -> Lookup a ptype in the defintion D by ``type`` and return it.

        If it's not found return ``default`` or raise a KeyError if not specified.
        """
        if len(args) not in {1, 2}:
            raise error.UserError(cls, 'definition.lookup', message="Expected only 1 or 2 parameters ({:d} given)".format(len(args)))

        # if we didn't get a default value, then we need to handle the
        # case specially so that we can raise an exception.
        if len(args) < 2:
            [type] = args
            res = cls.__get__(type, None, **kwargs)
            if not res:
                raise error.KeyError(cls, 'definition.lookup', type)
            return res

        # otherwise, we can simply just use it since we don't have to
        # raise an exception.
        return cls.__get__(*args, **kwargs)

    @classmethod
    def has(cls, key, **kwargs):
        '''Return True if the specified ``key`` is within the definition.'''
        return True if cls.__get__(key, False, **kwargs) else False
    contains = has

    @classmethod
    def pop(cls, key, **kwargs):
        '''Removes the definition associated with the specified ``key`` from the cache.'''
        return cls.__del__(key, **kwargs)

    @classmethod
    def get(cls, *args, **attributes):
        """D.get(key[, default], **attributes) -> Lookup a ptype in the definition D by ``key`` and return a clone of it with ``attributes`` applied.

        If ``key`` was not found, then return ``default`` or D.default if it's undefined.
        """
        if len(args) not in {1, 2}:
            raise error.TypeError(cls, 'definition.get', message="Expected only 1 or 2 parameters ({:d} given)".format(len(args)))

        # if we weren't given a default value, then we'll simply return None.
        if len(args) < 2:
            [key] = args
            res = cls.lookup(key, None, **attributes)

        # otherwise use it to get a type back.
        else:
            res = cls.lookup(*args, **attributes)

        # whatever we received needs to be cloned here.
        return clone(res or cls.__default__(**attributes), **attributes) if attributes else res or cls.__default__(**attributes)

    @classmethod
    def withdefault(cls, *args, **missingattributes):
        """D.withdefault(key[, default], **missingattributes) -> Lookup a ptype in the definition D by ``key``.

        If ``key`` was not found, then return ``default`` or D.default with ``missingattributes`` applied to it.
        """
        if len(args) not in {1, 2}:
            raise error.TypeError(cls, 'definition.withdefault', message="Expected only 1 or 2 parameters ({:d} given)".format(len(args)))

        # if we weren't given a default value, then we need to figure that out ourselves.
        if len(args) < 2:
            [key] = args
            return cls.lookup(key, None, **missingattributes) or (clone(cls.__default__(**missingattributes), **missingattributes) if missingattributes else cls.__default__(**missingattributes))

        # otherwise, we can just extract it and use it if the key wasn't found
        key, default = args
        return cls.lookup(key, None, **missingattributes) or (clone(default, **missingattributes) if missingattributes else default)

    @classmethod
    def update(cls, other):
        """Import the definition cache from ``other``, effectively merging the contents into the current definition."""
        a, b = ({key for key in item.keys()} for item in [cls.cache, other.cache])
        if a & b:
            fullname = '.'.join([cls.__module__, cls.__name__])
            Log.error("definition.update : {:s} : Unable to import cache {!r} due to multiple definitions of the same record".format(fullname, other))
            Log.warning("definition.update : {:s} : Discovered the following duplicate record types : {!r}".format(fullname, a & b))
            return False

        # merge record caches into a single one
        for key, object in other.cache.items():
            cls.__set__(key, object)
        return True

    @classmethod
    def copy(cls, recurse=False):
        """Make a duplicate of the current definition and its members.

        If ``recurse`` is true, then also make copies of any definitions that are cached or defined underneath it.
        """

        # Create a dictionary that keeps track of references so that if there's more
        # than one reference to the same definition, they're properly retained in the
        # duplicate definition that we return.
        identity, duplicates = builtins.id, {}

        # Make a copy of the type's namespace
        ns = {}
        for name, attribute in cls.__dict__.items():
            if recurse and builtins.isinstance(attribute, builtins.type) and issubclass(attribute, definition):
                ns[name] = duplicates.setdefault(identity(attribute), attribute.copy(recurse=recurse))
            else:
                ns[name] = attribute
            continue

        # Copy the default properties that are used by definitions
        ns['attribute'] = cls.attribute
        ns['default'] = cls.default

        # Figure out which module name is calling us
        fr = sys._getframe()
        while fr.f_back is not None:
            if fr.f_globals['__name__'] != __name__:
                break
            fr = fr.f_back

        # Update the module name with the one that was found in the frame.
        if fr is not None and fr.f_globals['__name__'] != __name__:
            ns['__module__'] = fr.f_globals['__name__']

        # Copy the cache making sure to recurse into it if necessary
        ns['cache'] = res = {}
        for key, object in cls.cache.items():
            if recurse and builtins.isinstance(object, builtins.type) and issubclass(object, definition):
                res[key] = duplicates.setdefault(identity(object), object.copy(recurse=recurse))
            else:
                res[key] = object
            continue

        # Finally re-construct the type using the original name, base-classes, and new namespace
        return builtins.type(cls.__name__, cls.__bases__, ns)

    @classmethod
    def merge(cls, other):
        """Merge contents of current ptype.definition with ``other`` and update both with the resulting union."""
        if cls.update(other):
            other.cache = cls.cache
            return True
        return False

    ## special descriptors that automatically generate a type from a definition
    class __auto_type_descriptor(object):
        def __init__(self, attribute, definition):
            self._attribute = attribute
            self._definition = definition

        def __get__(self, obj, type=None):
            cls = type or definition
            clsname = '.'.join(getattr(cls, attribute) for attribute in ['__module__', '__name__'] if hasattr(cls, attribute))
            if obj is not None or type is None:
                raise AttributeError("type object '{:s}' has no attribute '{:s}' when instantiated and is only accessible from the definition".format(clsname, self._attribute))
            if not hasattr(type, self._definition):
                raise AttributeError("type object '{:s}' has no attribute '{:s}'".format(clsname, self._definition))
            return getattr(type, self._definition)

    class __type_instance__(__auto_type_descriptor):
        '''Use the "_object_" attribute to return a type that is associated with the definition.'''
        def __get__(self, obj, type=None):
            result = super(definition.__type_instance__, self).__get__(obj, type)
            if not builtins.isinstance(result, builtins.type):
                if not callable(result):
                    cls = type or definition
                    clsname = '.'.join(getattr(cls, attribute) for attribute in ['__module__', '__name__'] if hasattr(cls, attribute))
                    raise TypeError("type object '{:s}' in attribute '{:s}' is not a supported type or callable".format('.'.join(getattr(result, attribute) for attribute in ['__module__', '__name__'] if hasattr(result, attribute)), '.'.join([clsname, self._definition])))
                return result

            elif not issubclass(result, generic):
                cls = type or definition
                clsname = '.'.join(getattr(cls, attribute) for attribute in ['__module__', '__name__'] if hasattr(cls, attribute))
                raise TypeError("type object '{:s}' in attribute '{:s}' is not a supported type or callable".format('.'.join(getattr(result, attribute) for attribute in ['__module__', '__name__'] if hasattr(result, attribute)), '.'.join([clsname, self._definition])))

            name = '.'.join([type.__name__, self._attribute])
            return builtins.type(name, (result,), {'__module__': result.__module__})

    class __callable_descriptor__(object):
        def __init__(self, callable, *args, **kwargs):
            self.callable = callable
            self.args = args
            self.kwargs = kwargs
        def __get__(self, obj, type=None):
            args, kwargs = self.args, self.kwargs
            return self.callable(*args, **kwargs)

    class __enum_instance__(__auto_type_descriptor):
        '''Use the "_enum_" attribute as the base class for an enumeration generated using the types associated with the definition.'''
        @staticmethod
        def bytes_or_whatever(enum, key):
            '''Convert the key used as input for enum into an integer that can be assigned to the enumeration's values.'''
            temporary = enum().alloc()
            if builtins.isinstance(key, bitmap.integer_types):
                return key
            elif builtins.isinstance(key, builtins.bytes):
                return temporary.load(source=provider.bytes(key)).int()
            elif builtins.isinstance(key, temporary.get().__class__):
                return temporary.set(key).int()
            return key

        def __get__(self, obj, type=None):
            result = super(definition.__enum_instance__, self).__get__(obj, type)
            from . import pint, pbinary

            cls = type or definition
            clsname = '.'.join(getattr(cls, attribute) for attribute in ['__module__', '__name__'] if hasattr(cls, attribute))

            if not issubclass(result, generic):
                raise TypeError("type object '{:s}' in attribute '{:s}' is not a supported type or callable".format('.'.join(getattr(result, attribute) for attribute in ['__module__', '__name__'] if hasattr(result, attribute)), '.'.join([clsname, self._definition])))
            if not issubclass(result, (pint.enum, pbinary.enum)):
                raise TypeError("type object '{:s}' in attribute '{:s}' is not a supported enumeration type".format('.'.join(getattr(result, attribute) for attribute in ['__module__', '__name__'] if hasattr(result, attribute)), '.'.join([clsname, self._definition])))

            def get_filtered_values(values):
                unique_values = {self.bytes_or_whatever(result, key): object.__name__ for key, object in type.cache.items()}
                unique_values.update({key : name for name, key in values})
                newvalues = {name : key for key, name in unique_values.items()}
                if all(builtins.isinstance(key, bitmap.integer_types) for _, key in newvalues.items()):
                    return [(name, integer) for name, integer in newvalues.items()]

                invalid = {name for name, key in newvalues.items() if not builtins.isinstance(key, bitmap.integer_types)}
                fixed = {name : key for name, key in newvalues.items() if name not in invalid}
                if fixed:
                    Log.warning("{:s} : {:s} : Some of the values within the definition were not integers and have been ignored ({:s})".format(clsname, self._attribute, ', '.join(invalid)))
                elif invalid:
                    Log.warning("{:s} : {:s} : Returning an enumeration that has no values defined due to their \"{:s}\" attribute being non-integer".format(clsname, self._attribute, type.attribute))
                return [(name, integer) for name, integer in fixed.items()]

            attributes = {}
            module, name = (type.__module__, '.'.join([type.__name__, self._attribute])) if result.__name__ == self._definition else (result.__module__, result.__name__)
            attributes['__module__'] = module
            values = getattr(result, '_values_', None) or []
            attributes['_values_'] = definition.__callable_descriptor__(get_filtered_values, values)
            return builtins.type(name, (result,), attributes)

    # Just a generic type based on "definition._object_" that is scoped within the definition
    type = __type_instance__('type', '_object_')

    # An enumeration that inherits from "definition._enum_" and uses the names/values within the definition
    enum = __enum_instance__('enum', '_enum_')

class wrapper_t(type):
    '''This type represents a type that is backed and sized by another ptype.

    _value_ -- the type that will be instantiated as the wrapper_t's backend
    object -- an instance of ._value_ that the wrapper_t will use for modifying

    Modifying the instance of .object will affect the string in the .value property. If .value is modified, this will affect the state of the .object instance.
    '''

    _value_ = None

    # getter/setter that wraps .value and keeps .object and .value in sync
    __value__ = None
    @property
    def value(self):
        '''Returns the contents of the wrapper_t.'''
        return self.__value__

    @value.setter
    def value(self, data):
        '''Re-assigns the contents of the wrapper_t'''
        try:
            self.__deserialize_block__(data)
        except (StopIteration, error.ProviderError):
            raise error.LoadError(self, consumed=len(data))
        return

    __object__ = None

    # setters/getters for the object's backing instance
    @property
    def object(self):
        '''Returns the instance that is used to back the wrapper_t.'''
        cls = self.__class__

        # Check if wrapper_t.__object__ is undefined
        if self.__object__ is None:
            if self._value_ and not istype(self._value_):
                Log.info("wrapper_t.object : {:s} : Using wrapper_t._value_{:s} as a closure for instantiatiation of object.".format(self.instance(), '' if self._value_.__name__ == '_value_' else " ({:s})".format(self._value_.__name__)))
            res = self._value_ or type
            name = "wrapped<{:s}>".format(res.typename() if istype(res) else getattr(res, '__qualname__', res.__name__))
            self.__object__ = self.new(res, __name__=name, offset=0, source=provider.proxy(self))

        # Otherwise, we can simply return it
        return self.__object__

    @object.setter
    def object(self, instance):
        name = "wrapped<{:s}>".format(instance.name())

        # make a copy of the object the user specified
        # and take ownership of it prior to assignment.
        self.__object__ = object = instance.copy(__name__=name, offset=0, source=provider.proxy(self), parent=self)

        # if the backing type wasn't created yet, then create it
        if self.__value__ is None and object.initializedQ():
            block = object.serialize()
            try:
                self.__deserialize_block__(block)
            except (StopIteration, error.ProviderError):
                raise error.LoadError(self, consumed=len(block))
            return

        # update our value with the type that we assigned
        self.__value__ = object.serialize()

    o = object

    def initializedQ(self):
        return self.__object__ is not None and self.__object__.initializedQ()

    def __blocksize_originalQ__(self):
        '''Return whether the instance's blocksize has been rewritten by a definition.'''
        cls = self.__class__
        return utils.callable_eq(self, self.blocksize, cls, cls.blocksize) and utils.callable_eq(cls, cls.blocksize, wrapper_t, wrapper_t.blocksize)
    def blocksize(self):
        if self.__object__ is not None:
            try:
                return self.__object__.blocksize()
            except error.InitializationError:
                res = self.__object__.copy()
            return res.a.blocksize()

        # if blocksize can't be calculated by loading (invalid dereference)
        #   then guess the size by allocating an empty version of the type
        value = self.new(self._value_ or type, offset=self.getoffset(), source=self.source)
        try:
            res = value.l.blocksize()

        except error.LoadError:
            res = value.a.blocksize()
        return res

    def __deserialize_block__(self, block):
        assert(block is not None)
        self.__value__ = block
        try:
            self.object.load(offset=0, source=provider.proxy(self))

        # If we got a LoadError or similar, then we need to recast the
        # exception as a ConsumeError since this method is used to
        # deserialize a block for our wrapped type.
        except (StopIteration, error.ProviderError):
            raise error.ConsumeError(self, self.getoffset(), len(block), amount=self.object.size())
        return self

    # forwarded methods
    def __getvalue__(self):
        return self.object.get()

    def __setvalue__(self, *values, **attrs):
        if not values:
            return self

        [value] = values
        self.__value__ = self.object.set(value, **attrs).serialize()
        return self

    def commit(self, **attrs):
        self.object.commit(offset=0, source=provider.proxy(self))
        return super(wrapper_t, self).commit(**attrs)

    def size(self):
        if self.__object__ is not None and self.__object__.initializedQ():
            return self.__object__.size()
        elif self.__value__ is not None:
            return len(self.__value__)
        cls, backing = wrapper_t, self._value_
        Log.info("wrapper_t.size : {:s} : Unable to determine (real) size with {!s} ({!s}), as object is still uninitialized.".format(self.instance(), cls.typename(), backing))
        return 0

    def classname(self):
        if self.initializedQ():
            return "{:s}<{:s}>".format(self.typename(), self.__object__.classname())
        if self._value_ is None:
            return "{:s}<?>".format(self.typename())
        value = self._value_
        return "{:s}<{:s}>".format(self.typename(), value.typename() if istype(value) else getattr(value, '__qualname__', value.__name__))

    def contains(self, offset):
        left = self.getoffset()
        right = left + self.blocksize()
        return left <= offset < right

    def __getstate__(self):
        return super(wrapper_t, self).__getstate__(), self._value_, self.__object__

    def __setstate__(self, state):
        state, self._value_, self.__object__ = state
        super(wrapper_t, self).__setstate__(state)

    def __format__(self, spec):
        return self.object.__format__(spec)

    def alloc(self, *values, **attrs):
        self.__object__ = None
        return super(wrapper_t, self).alloc(*values, **attrs)

class encoded_t(wrapper_t):
    """This type represents an element that can be decoded/encoded to/from another element.

    To change the way a type is decoded, overload the .decode() method and then
    call the super class' method with a dictionary of any attributes that you
    want to modify.

    To change the way a type is encoded to it, overwrite .encode() and convert
    the object parameter to an encoded string.

    _value_ = the original element type
    _object_ = the decoded element type

    .object = the actual element object represented by self
    """
    _value_ = None      # source type
    _object_ = None     # new type

    d = property((lambda s, **a: s.dereference(**a)), (lambda s, *x, **a:s.reference(*x, **a)))
    ref = lambda s, *x, **a: s.reference(*x, **a)

    def decode(self, object, **attrs):
        """Take ``data`` and decode it back to it's original form"""
        [ attrs.pop(name, None) for name in ['offset', 'source', 'parent'] ]

        # attach decoded object to encoded_t
        attrs['offset'], attrs['source'], attrs['parent'] = 0, provider.proxy(self, autocommit={}), self
        object.__update__(recurse=self.attributes)
        object.__update__(attrs)
        return object

    def encode(self, object, **attrs):
        """Take ``data`` and return it in encoded form"""
        [ attrs.pop(name, None) for name in ['offset', 'source', 'parent'] ]

        # attach encoded object to encoded_t
        attrs['offset'], attrs['source'], attrs['parent'] = 0, provider.proxy(self, autocommit={}), self
        object.__update__(attrs)
        return object

    def __hook(self, object):
        '''This hooks ``object`` with a .load and .commit that will write to the encoded_t'''

        fmt = "_encoded_t__{:s}".format
        ## overriding the `commit` method
        if hasattr(object, fmt('commit')):
            object.commit = getattr(object, fmt('commit'))
            delattr(object, fmt('commit'))

        def commit(**attrs):
            expected = self.blocksize()

            # now turn it into the type that the encoded_t should expect
            res = object.cast(self._object_) if getattr(self, '_object_', None) else object

            # so that we can encode it
            enc = self.encode(res, **attrs)

            # cast whatever was returned from the encoded type to our backing
            backing = enc.cast(self._value_ or clone(type, length=enc.size()))

            # so that we can simply assign it to our object and be good to go
            self.object = backing

            return object
        setattr(object, fmt('commit'), object.commit)
        object.commit = commit

        ## overloading the `load` method
        if hasattr(object, fmt('load')):
            object.load = getattr(object, fmt('load'))
            delattr(object, fmt('load'))

        def load(**attrs):
            expected = self.size()

            # first cast into our backing type, or use what we have
            res = self.cast(self._value_) if self._value_ else self.object

            # use it to decode the type into an object
            dec = self.decode(res, **attrs)

            # finally load the decoded obj into self
            fn = getattr(object, fmt('load'))
            return fn(offset=0, source=provider.proxy(dec), blocksize=dec.blocksize)
        setattr(object, fmt('load'), object.load)
        object.load = load

        # ..and we're done
        return object

    #@utils.memoize('self', self=lambda n:(n.source, n._object_), attrs=lambda n:tuple(sorted(n.items())))
    @utils.memoize_method(self=lambda self: (self.source, self._object_), attrs=lambda self: frozenset(self.items()))
    def dereference(self, **attrs):
        """Dereference object into the target type specified by self._object_"""
        attrs.setdefault('__name__', '*'+self.name())

        # First cast ourselves into our backing type so that our decode implementation
        # knows how to handle the type we give it.
        res = self.cast(self._value_) if self._value_ else self.object

        # Hand off the casted object to our decode implementation along with
        # some necessary attributes. This allows the decode implementation to
        # change something if necessary
        dec = self.decode(res, offset=0, source=provider.proxy(self, autocommit={}))

        # also ensure that decoded object will encode/decode depending on commit/load
        dec = self.__hook(dec)

        # update attributes
        dec.__update__(recurse=self.attributes)

        # ensure that all of it's children autoload/autocommit to the decoded object
        recurse = {'source': provider.proxy(dec, autocommit={}, autoload={})}
        recurse.update(attrs.get('recurse', {}))
        attrs['recurse'] = recurse
        attrs.setdefault('blocksize', dec.size)

        # and we now have a good working object
        object = getattr(self, '_object_', type) or type
        return dec.new(object, **attrs)

    def reference(self, object, **attrs):
        """Reference ``object`` and encode it into self"""

        # re-parent the object to us
        object = self.new(object)

        # hook the object that we're referencing
        object = self.__hook(object)

        # assign some default attributes to object
        object.__name__ = '*'+self.name()

        # update our ._object_ attribute since the user explicitly
        # called .reference() to change what is being referenced
        self._object_ = object.__class__

        # now we can just pass through to our hooked .commit method
        object.commit()

        # last thing to do is cache it in the memoization by reloading
        res = self.dereference()
        if not res.initializedQ():
            res.load()

        return self

def setbyteorder(order):
    '''Sets the byte order for any pointer_t
    can be either .bigendian or .littleendian
    '''
    global pointer_t
    if order in (config.byteorder.bigendian, config.byteorder.littleendian):
        result, pointer_t._value_.byteorder = getattr(pointer_t._value_, 'byteorder', config.defaults.integer.order), config.byteorder.bigendian if order is config.byteorder.bigendian else config.byteorder.littleendian
        return result

    elif builtins.isinstance(order, utils.string_types):
        if order.startswith('big'):
            return setbyteorder(config.byteorder.bigendian)
        elif order.startswith('little'):
            return setbyteorder(config.byteorder.littleendian)
        raise ValueError("An unknown byteorder was specified ({:s}) for pointer types.".format(order))

    elif getattr(order, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)

    elif getattr(order, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("An unknown byteorder was specified ({:s}) for pointer types.".format(order))

class pointer_t(encoded_t):
    _object_ = None

    d = property((lambda s, **a: s.dereference(**a)), (lambda s, *x, **a:s.reference(*x, **a)))
    ref = lambda s, *x, **a: s.reference(*x, **a)

    class _value_(block):
        '''Default pointer value that can return an integer in any byteorder'''
        def __setvalue__(self, *values, **attrs):
            if not values:
                return super(pointer_t._value_, self).__setvalue__(*values, **attrs)

            [offset] = values
            res = bitmap.new(offset, 8 * self.blocksize())
            res = bitmap.data(res, reversed=(getattr(self, 'byteorder', Config.integer.order) is config.byteorder.littleendian))
            return super(pointer_t._value_, self).__setvalue__(res, **attrs)

        def __getvalue__(self):
            if self.value is None:
                raise error.InitializationError(self, 'pointer_t._value_.get')

            bs, value = self.blocksize(), self.value[:: -1 if getattr(self, 'byteorder', Config.integer.order) is config.byteorder.littleendian else -1]
            octets = __izip_longest__(bytearray(value), [8] * bs)
            res = functools.reduce(bitmap.push, octets, bitmap.zero)
            return bitmap.value(res)

        def blocksize(self):
            blocksize = getattr(self, 'length', None)
            if blocksize is None:
                return Config.integer.size if self.value is None else len(self.value)
            return blocksize

        def __format__(self, spec):
            if self.value is None or not spec:
                return super(pointer_t._value_, self).__format__(spec)

            prefix, spec = spec[:-1], spec[-1:]
            if spec in 'don' and prefix:
                return "{:{:s}{:s}}".format(self.__getvalue__(), prefix, spec)
            elif spec in 'don':
                return "{:{:s}}".format(self.__getvalue__(), spec)
            elif prefix == '#' and spec in 'xX':
                return "{:#0{:d}{:s}}".format(self.__getvalue__(), 2 + 2 * self.size(), spec)
            elif not prefix and spec in 'xX':
                return "{:0{:d}{:s}}".format(self.__getvalue__(), 2 * self.size(), spec)
            elif spec in 'xX':
                return "{:{:s}{:s}}".format(self.__getvalue__(), prefix, spec)
            return super(pointer_t._value_, self).__format__(prefix + spec)

    def decode(self, object, **attrs):
        return object.cast(self._value_, **attrs)

    def encode(self, object, **attrs):
        return object.cast(self._value_, **attrs)

    #@utils.memoize('self', self=lambda n:(n.source, n._object_, n.object.__getvalue__()), attrs=lambda n:tuple(sorted(n.items())))
    @utils.memoize_method(self=lambda self: (self.source, self._object_, self.object.__getvalue__()), attrs=lambda self:frozenset(self.items()))
    def dereference(self, **attrs):
        res = self.decode(self.object)
        attrs.setdefault('__name__', '*'+self.name())
        attrs.setdefault('source', self.__source__)
        attrs.setdefault('offset', res.get())
        object = getattr(self, '_object_', undefined) or undefined
        return self.new(object, **attrs)

    def reference(self, object, **attrs):
        attrs.setdefault('__name__', '*'+self.name())
        attrs.setdefault('source', self.__source__)
        res = self.object.copy().set(object.getoffset())
        enc = self.encode(res)
        enc.commit(offset=0, source=provider.proxy(self.object))
        self._object_ = object.__class__
        self.object.commit(offset=0, source=provider.proxy(self))
        return self

    def int(self):
        """Return the value of pointer as an integral"""
        return self.object.get()
    num = number = int

    def classname(self):
        object = getattr(self, '_object_', undefined) or undefined
        if self.initializedQ():
            res = self.dereference()
            return "{:s}<{:s}>".format(self.typename(), res.classname())
        objectname = force(object, self).typename() if istype(object) else object.__qualname__ if hasattr(object, '__qualname__') else getattr(object, '__name__', 'None')
        return "{:s}<{:s}>".format(self.typename(), objectname)

    def summary(self):
        if self.value is None:
            return u"???"
        return u"*{:#x}".format(self.int())

    def repr(self):
        """Display all pointer_t instances as an integer"""
        return self.summary() if self.initializedQ() else u"*???"

    def __getstate__(self):
        return super(pointer_t, self).__getstate__(), self._object_
    def __setstate__(self, state):
        state, self._object_ = state
        super(wrapper_t, self).__setstate__(state)

class rpointer_t(pointer_t):
    """a pointer_t that's at an offset relative to a specific object"""

    def classname(self):
        baseobject, object = getattr(self, '_baseobject_', None), getattr(self, '_object_', None)
        if self.initializedQ():
            return "{:s}<{:s}>".format(self.typename(), self.dereference().classname())
        basename = 'None' if baseobject is None else baseobject.classname() if builtins.isinstance(baseobject, base) else getattr(baseobject, '__qualname__', baseobject.__name__)
        objectname = force(object, self).typename() if istype(object) else object.__qualname__ if hasattr(object, '__qualname__') else getattr(object, '__name__', 'None')
        return "{:s}({:s}, {:s})".format(self.typename(), objectname, basename or '')

    def dereference(self, **attrs):
        baseobject = getattr(self, '_baseobject_', None)
        root = None if baseobject is None else force(baseobject, self)
        base = 0 if root is None else root.getoffset() if isinstance(root) else root().getoffset()
        res = self.decode(self.object)
        attrs.setdefault('offset', base + res.get())
        return super(rpointer_t, self).dereference(**attrs)

    def __getstate__(self):
        return super(rpointer_t, self).__getstate__(), getattr(self, '_baseobject_', None)

    def __setstate__(self, state):
        [state, self._baseobject_] = state
        super(rpointer_t, self).__setstate__(state)

class opointer_t(pointer_t):
    """a pointer_t that's calculated via a user-provided function that takes an integer value as an argument"""

    def classname(self):
        calculate, object = getattr(self, '_calculate_', None), getattr(self, '_object_', None)
        calcname = '' if calculate is None else getattr(calculate, '__qualname__', calculate.__name__)
        #if self.initializedQ():
        #    return "{:s}<{:s}>".format(self.typename(), self.dereference().classname())
        objectname = force(object, self).typename() if istype(object) else object.__qualname__ if hasattr(object, '__qualname__') else getattr(object, '__name__', 'None')
        return "{:s}({:s}, {:s})".format(self.typename(), objectname, calcname or '...')

    def dereference(self, **attrs):
        res, calculate = self.decode(self.object), getattr(self, '_calculate_', lambda value: value)
        if 'offset' not in attrs:
            attrs['offset'] = calculate(res.get())
        return super(opointer_t, self).dereference(**attrs)

class boundary(base):
    """Used to mark a boundary in a ptype tree. Can be used to make .getparent() stop."""

from . import pbinary  # XXX: recursive. yay.

if __name__ == '__main__':
    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)
                raise Failure
            except Success as E:
                print('%s: %r'% (name, E))
                return True
            except Failure as E:
                print('%s: %r'% (name, E))
            except Exception as E:
                print('%s: %r : %r'% (name, Failure(), E))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptypes
    from ptypes import dynamic, pint, pstr, parray, pstruct, ptype, provider, error
    prov = provider

    @TestCase
    def test_wrapper_read():
        class wrap(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.block, length=0x10)

        s = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        a = wrap(source=ptypes.prov.bytes(s))
        a = a.l
        if a.serialize() == b'ABCDEFGHIJKLMNOP':
            raise Success

    @TestCase
    def test_wrapper_write():
        class wrap(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.block, length=0x10)

        s = bytearray(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        a = wrap(source=ptypes.prov.bytes(s))
        a = a.l
        a.object[:0x10] = s[:0x10].lower()
        a.commit()

        if a.l.serialize() == b'abcdefghijklmnop':
            raise Success

    @TestCase
    def test_encoded_xorenc():
        k = 0x80
        s = bytes(bytearray(x ^ k for x in bytearray(b'hello world')))
        class xor(ptype.encoded_t):
            _value_ = dynamic.block(len(s))
            _object_ = dynamic.block(len(s))
            key = k
            def encode(self, object, **attrs):
                data = bytearray(x ^ k for x in bytearray(object.serialize()))
                return super(xor, self).encode(ptype.block(length=len(data)).set(bytes(data)))
            def decode(self, object, **attrs):
                data = bytearray(x ^ k for x in bytearray(object.serialize()))
                return super(xor, self).decode(ptype.block(length=len(data)).set(bytes(data)))

        x = xor(source=ptypes.prov.bytes(s))
        x = x.l
        if x.d.l.serialize() == b'hello world':
            raise Success

    @TestCase
    def test_decoded_xorenc():
        k = 0x80
        data = b'hello world'
        match = bytes(bytearray(x ^ k for x in bytearray(data)))

        class xor(ptype.encoded_t):
            _value_ = dynamic.block(len(data))
            _object_ = dynamic.block(len(match))

            key = k

            def encode(self, object, **attrs):
                data = bytearray(x ^ k for x in bytearray(object.serialize()))
                return super(xor, self).encode(ptype.block(length=len(data)).set(bytes(data)))
            def decode(self, object, **attrs):
                data = bytearray(x ^ k for x in bytearray(object.serialize()))
                return super(xor, self).decode(ptype.block(length=len(data)).set(bytes(data)))

        instance = ptype.block(length=len(match)).set(match)

        x = xor(source=ptypes.prov.bytes(b'\0'*0x100)).l
        x.reference(instance)
        if x.serialize() == data:
            raise Success

    @TestCase
    def test_encoded_b64():
        import base64
        b64encode, b64decode = (base64.encodestring, base64.decodestring) if sys.version_info[0] < 3 else (base64.encodebytes, base64.decodebytes)

        s = b64encode(b'AAAABBBBCCCCDDDD').strip() + b'\0' + b'A'*20
        class b64(ptype.encoded_t):
            _value_ = pstr.szstring
            _object_ = dynamic.array(pint.uint32_t, 4)

            def encode(self, object, **attrs):
                res = object.serialize()
                data = b64encode(res)
                return super(b64, self).encode(ptype.block(length=len(data)).set(data))

            def decode(self, object, **attrs):
                res = object.serialize()
                data = b64decode(object.serialize())
                return super(b64, self).decode(ptype.block(length=len(data)).set(data))

        x = b64(source=ptypes.prov.bytes(s)).l
        y = x.d.l
        if x.size() == 25 and y[0].serialize() == b'AAAA' and y[1].serialize() == b'BBBB' and y[2].serialize() == b'CCCC' and y[3].serialize() == b'DDDD':
            raise Success

    @TestCase
    def test_decoded_b64():
        import base64
        b64encode, b64decode = (base64.encodestring, base64.decodestring) if sys.version_info[0] < 3 else (base64.encodebytes, base64.decodebytes)

        input = b'AAAABBBBCCCCDDDD'
        result = b64encode(input)
        instance = pstr.string(length=len(input)).set(input)

        class b64(ptype.encoded_t):
            _value_ = dynamic.block(len(result))
            _object_ = dynamic.array(pint.uint32_t, 4)

            def encode(self, object, **attrs):
                res = object.serialize()
                data = b64encode(res)
                return super(b64, self).encode(ptype.block(length=len(data)).set(data))

            def decode(self, object, **attrs):
                res = object.serialize()
                data = b64decode(res)
                return super(b64, self).decode(ptype.block(length=len(data)).set(data))

        x = b64(source=ptypes.prov.bytes(b'A'*0x100+b'\0')).l
        x = x.reference(instance)
        if builtins.isinstance(x.d, pstr.string) and x.serialize() == result:
            raise Success

    @TestCase
    def test_attributes_static_1():
        x = pint.uint32_t(a1=5).a
        if 'a1' not in x.attributes and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_1():
        x = pint.uint32_t(recurse={'a1':5}).a
        if 'a1' in x.attributes and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_static_2():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh(a1=5).a
        if 'a1' not in x.attributes and 'a1' not in x.v[0].attributes and 'a1' not in dir(x.v[0]) and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_2():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh(recurse={'a1':5}).a
        if 'a1' in x.attributes and 'a1' in x.v[0].attributes and 'a1' in dir(x.v[0]) and x.v[0].a1 == 5:
            raise Success

    @TestCase
    def test_attributes_static_3():
        x = pint.uint32_t().a
        x.__update__({'a2':5})
        if 'a2' not in x.attributes and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_3():
        argh = pint.uint32_t
        x = pint.uint32_t().a
        x.__update__(recurse={'a2':5})
        if 'a2' in x.attributes and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_static_4():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh().a
        x.__update__({'a2':5})
        if 'a2' not in x.attributes and 'a2' not in x.v[0].attributes and 'a2' not in dir(x.v[0]) and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_4():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh().a
        x.__update__(recurse={'a2':5})
        if 'a2' in x.attributes and 'a2' in x.v[0].attributes and 'a2' in dir(x.v[0]) and x.v[0].a2 == 5:
            raise Success

    @TestCase
    def test_attributes_static_5():
        a = pint.uint32_t(a1=5).a
        x = a.new(pint.uint32_t)
        if 'a1' not in a.attributes and 'a1' not in x.attributes and 'a1' not in dir(x):
            raise Success

    @TestCase
    def test_attributes_recurse_5():
        a = pint.uint32_t(recurse={'a1':5}).a
        x = a.new(pint.uint32_t)
        if 'a1' in a.attributes and 'a1' in x.attributes and x.a1 == 5:
            raise Success

    @TestCase
    def test_pointer_dereference():
        import math
        count = math.log(sys.maxint if sys.version_info[0] < 3 else sys.maxsize) / math.log(0x100)
        prefix = bytes(bytearray([math.trunc(math.ceil(count))] + [0] * math.trunc(count)))

        data = prefix + b'AAAA'

        a = ptype.pointer_t(source=prov.bytes(data), offset=0, _object_=pint.uint32_t, _value_=pint.uint32_t)
        a = a.l
        b = a.dereference()
        if b.l.int() == 0x41414141:
            raise Success

    @TestCase
    def test_pointer_ref():
        import math
        count = math.log(sys.maxint if sys.version_info[0] < 3 else sys.maxsize) / math.log(0x100)
        prefix = bytes(bytearray([math.trunc(math.ceil(count))] + [0] * math.trunc(count)))

        src = prov.bytes(bytearray(prefix + b'AAAA' + b'AAAA'))

        a = ptype.pointer_t(source=src, offset=0, _object_=dynamic.block(4), _value_=pint.uint32_t).l
        b = a.d.l
        if b.serialize() != b'\x41\x41\x41\x41':
            raise Failure

        c = pint.uint32_t(offset=8,source=src).set(0x42424242).commit()
        a.reference(c)
        if a.getoffset() == 0 and a.int() == c.getoffset() and a.d.l.int() == 0x42424242 and a.d.getoffset() == c.getoffset():
            raise Success

    @TestCase
    def test_pointer_deref_32():
        data = b'\x04\x00\x00\x00AAAA'

        a = ptype.pointer_t(source=prov.bytes(data), offset=0, _object_=pint.uint32_t, _value_=pint.uint32_t)
        a = a.l
        b = a.dereference()
        if b.l.int() == 0x41414141:
            raise Success

    @TestCase
    def test_pointer_ref_32():
        src = prov.bytes(bytearray(b'\x04\x00\x00\x00AAAAAAAA'))
        a = ptype.pointer_t(source=src, offset=0, _object_=dynamic.block(4), _value_=pint.uint32_t).l
        b = a.d.l
        if b.serialize() != b'\x41\x41\x41\x41':
            raise Failure

        c = pint.uint32_t(offset=8,source=src).set(0x42424242).commit()
        a.reference(c)
        if a.getoffset() == 0 and a.int() == c.getoffset() and a.d.l.int() == 0x42424242 and a.d.getoffset() == c.getoffset():
            raise Success

    @TestCase
    def test_pointer_deref_64():
        data = b'\x08\x00\x00\x00\x00\x00\x00\x00AAAA'

        a = ptype.pointer_t(source=prov.bytes(data), offset=0, _object_=pint.uint32_t, _value_=pint.uint64_t)
        a = a.l
        b = a.dereference()
        if b.l.int() == 0x41414141:
            raise Success

    @TestCase
    def test_pointer_ref_64():
        src = prov.bytes(bytearray(b'\x08\x00\x00\x00\x00\x00\x00\x00AAAAAAAA'))
        a = ptype.pointer_t(source=src, offset=0, _object_=dynamic.block(4), _value_=pint.uint64_t).l
        b = a.d.l
        if b.serialize() != b'\x41\x41\x41\x41':
            raise Failure

        c = pint.uint32_t(offset=8,source=src).set(0x42424242).commit()
        a.reference(c)
        if a.getoffset() == 0 and a.int() == c.getoffset() and a.d.l.int() == 0x42424242 and a.d.getoffset() == c.getoffset():
            raise Success

    @TestCase
    def test_type_cast_same():
        t1 = dynamic.clone(ptype.type, length=4)
        t2 = pint.uint32_t

        data = prov.bytes(b'AAAA')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_container_cast_same():
        t1 = dynamic.clone(ptype.type, length=4)
        t2 = dynamic.array(pint.uint8_t, 4)

        data = prov.bytes(b'AAAA')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_type_cast_diff_large_to_small():
        t1 = ptype.clone(ptype.type, length=4)
        t2 = ptype.clone(ptype.type, length=2)
        data = prov.bytes(b'ABCD')
        a = t1(source=data).l
        b = a.cast(t2)
        if b.serialize() == b'AB':
            raise Success

    @TestCase
    def test_type_cast_diff_small_to_large():
        t1 = ptype.clone(ptype.type, length=2)
        t2 = ptype.clone(ptype.type, length=4)
        data = prov.bytes(b'ABCD')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.size() == b.size() and not b.initializedQ():
            raise Success

    @TestCase
    def test_container_cast_large_to_small():
        t1 = dynamic.array(pint.uint8_t, 8)
        t2 = dynamic.array(pint.uint8_t, 4)
        data = prov.bytes(b'ABCDEFGH')

        a = t1(source=data).l
        b = a.cast(t2)
        if b.size() == 4 and b.serialize() == b'ABCD':
            raise Success

    @TestCase
    def test_container_cast_small_to_large():
        t1 = dynamic.array(pint.uint8_t, 4)
        t2 = dynamic.array(pint.uint8_t, 8)
        data = prov.bytes(b'ABCDEFGH')
        a = t1(source=data).l
        b = a.cast(t2)
        if b.size() == 4 and not b.initializedQ() and b.blocksize() == 8:
            raise Success

    @TestCase
    def test_type_copy():
        data = prov.bytes(b'WIQIWIQIWIQIWIQI')
        a = pint.uint32_t(source=data).a
        b = a.copy()
        if b.l.serialize() == a.l.serialize() and a is not b:
            raise Success

    @TestCase
    def test_container_copy():
        class leaf_sr(ptype.type):
            length = 4
        class leaf_jr(ptype.type):
            length = 2

        class branch(ptype.container): pass

        a = branch(source=prov.empty())
        a.set(leaf_sr, leaf_jr, branch().set(leaf_jr,leaf_jr,leaf_jr))
        b = a.copy()
        if b.v[2].v[1].size() == leaf_jr.length:
            raise Success

    # XXX: test casting between block types and stream types (szstring) as this
    #      might've been broken at some point...

    @TestCase
    def test_type_getoffset():
        class bah(ptype.type): length=2
        bounds = (item for item in bytearray(b'az'))
        data = prov.bytes(bytes(bytearray(item for item in range(*bounds))))
        a = bah(offset=0,source=data)
        if a.getoffset() == 0 and a.l.serialize()==b'ab':
            raise Success

    @TestCase
    def test_type_setoffset():
        class bah(ptype.type): length=2
        bounds = (item for item in bytearray(b'az'))
        data = prov.bytes(bytes(bytearray(item for item in range(*bounds))))
        a = bah(offset=0,source=data)
        a.setoffset(20)
        if a.l.initializedQ() and a.getoffset() == 20 and a.serialize() == b'uv':
            raise Success

    @TestCase
    def test_container_setoffset_recurse():
        class bah(ptype.type): length=2
        class cont(ptype.container): __getindex__ = lambda s,i: i
        a = cont()
        a.set(bah().a, bah().a, bah().a)
        a.setoffset(a.getoffset(), recurse=True)
        if tuple(x.getoffset() for x in a.value) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_field():
        class bah(ptype.type): length=2
        class cont(ptype.container): __getindex__ = lambda s,i: i

        a = cont()
        a.set(bah().a, bah().a, bah().a)
        if tuple(a.getoffset(i) for i in range(len(a.v))) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_iterable():
        class bah(ptype.type): length=2
        class cont(ptype.container): __getindex__ = lambda s,i: i

        a,b = cont(),cont()
        a.set(bah,bah,bah)
        b.set(bah,bah,bah)
        a.set(bah, b.copy(), bah)
        a.setoffset(a.getoffset(), recurse=True)
        if a.getoffset((1,2)) == 6:
            raise Success

    @TestCase
    def test_decompression_block():
        import zlib
        message = b'hi there.'
        cmessage = zlib.compress(message)
        class cblock(pstruct.type):
            class _zlibblock(ptype.encoded_t):
                _object_ = ptype.clone(ptype.block, length=len(message))
                def encode(self, object, **attrs):
                    data = zlib.compress(object.serialize())
                    return super(cblock._zlibblock, self).encode(ptype.block(length=len(data)).set(data))
                def decode(self, object, **attrs):
                    data = zlib.decompress(object.serialize())
                    return super(cblock._zlibblock, self).decode(ptype.block(length=len(data)).set(data))

            def __zlibblock(self):
                return ptype.clone(self._zlibblock, _value_=dynamic.block(self['size'].l.int()))

            _fields_ = [
                (pint.uint32_t, 'size'),
                (__zlibblock, 'data'),
            ]
        data = pint.uint32_t().set(len(cmessage)).serialize()+cmessage
        a = cblock(source=prov.bytes(data)).l
        if a['data'].d.l.serialize() == message:
            raise Success

    @TestCase
    def test_compression_block():
        import zlib
        message = b'hi there.'
        class mymessage(ptype.block):
            length = len(message)
        data = mymessage().set(message)

        class zlibblock(ptype.encoded_t):
            _object_ = ptype.clone(ptype.block, length=len(message))
            def encode(self, object, **attrs):
                data = zlib.compress(object.serialize())
                return super(zlibblock, self).encode(ptype.block(length=len(data)).set(data))
            def decode(self, object, **attrs):
                data = zlib.decompress(object.serialize())
                return super(zlibblock, self).decode(ptype.block(length=len(data)).set(data))

        source = prov.bytes(b'\0'*1000)
        a = zlibblock(source=source)
        a.object = pstr.string(length=1000, source=source).l
        a.reference(data)
        if a.d.l.serialize() == message:
            raise Success

    @TestCase
    def test_equality_type_same():
        class type1(ptype.type): length=4
        class type2(ptype.type): length=4
        data = b'ABCDEFGHIJKLMNOP'
        a = type1(source=prov.bytes(data)).l
        b = type2(source=prov.bytes(data), offset=a.getoffset()).l
        if a.same(b):
            raise Success

    @TestCase
    def test_equality_type_different():
        class type1(ptype.type): length=4
        data = b'ABCDEFGHIJKLMNOP'
        a = type1(source=prov.bytes(data))
        b = a.copy(offset=1)
        c = a.copy().l
        d = c.copy().load(offset=1)
        if not a.same(b) and not c.same(d):
            raise Success

    @TestCase
    def test_compare_type():
        a = pstr.szstring().set('this sentence is over the top!')
        b = pstr.szstring().set('this sentence is unpunctuaTed')
        def getstr(string, result):
            index, (self, other) = result
            return string[index : index + len(self)].serialize()
        result = list(a.compare(b))
        c,d = result
        if getstr(a, c) == b'over the top!' and getstr(b,c) == b'unpunctuaTed\0' and d[0] >= b.size() and getstr(a,d) == b'\0':
            raise Success

    @TestCase
    def test_compare_container_types():
        a = pint.uint8_t().set(20)
        b = pint.uint8_t().set(40)
        c = pint.uint8_t().set(60)
        d = pint.uint8_t().set(80)
        e = pint.uint8_t().set(100)

        y = ptype.container(value=[], __name__='y')
        z = ptype.container(value=[], __name__='z')
        y.value.extend( (a,b,c,d,e) )
        z.value.extend( (a,b,a,a,e) )
        y.value = [_.copy() for _ in y.value]
        z.value = [_.copy() for _ in z.value]
        y.setoffset(y.getoffset()+10, recurse=True)
        z.setoffset(z.getoffset(), recurse=True)

        result = dict(y.compare(z))
        if list(result.keys()) == [2]:
            s,o = result[2]
            if c.serialize()+d.serialize() == b''.join(item.serialize() for item in s) and a.serialize()+a.serialize() == b''.join(item.serialize() for item in o):
                raise Success

    @TestCase
    def test_compare_container_sizes():
        a = pint.uint8_t().set(20)
        b = pint.uint8_t().set(40)
        c = pint.uint8_t().set(60)
        d = pint.uint8_t().set(80)
        e = pint.uint8_t().set(100)
        f = pint.uint8_t().set(120)
        g = pint.uint32_t().set(0xdead)

        y = ptype.container(value=[], __name__='y')
        z = ptype.container(value=[], __name__='z')
        y.value.extend( (a,g,f) )
        z.value.extend( (a,b,c,d,e,f) )
        y.value = [_.copy() for _ in y.value]
        z.value = [_.copy() for _ in z.value]
        y.setoffset(y.getoffset(), recurse=True)
        z.setoffset(z.getoffset()+0x1000, recurse=True)

        result = dict(y.compare(z))
        if list(result.keys()) == [1]:
            s,o = tuple(functools.reduce(lambda a,b:a+b,map(lambda x:x.serialize(),X),b'') for X in result[1])
            if s == g.serialize() and o == bytes(bytearray([40, 60, 80, 100])):
                raise Success

    @TestCase
    def test_compare_container_tail():
        a = pint.uint8_t().set(20)
        b = pint.uint8_t().set(40)
        c = pint.uint8_t().set(60)
        d = pint.uint8_t().set(80)
        e = pint.uint8_t().set(100)
        f = pint.uint8_t().set(120)
        g = pint.uint32_t().set(0xdead)

        y = ptype.container(value=[], __name__='y')
        z = ptype.container(value=[], __name__='z')
        y.value.extend( (a,b,c) )
        z.value.extend( (a,b,c,g,c.copy().set(0x40)) )
        y.value = [_.copy() for _ in y.value]
        z.value = [_.copy() for _ in z.value]
        y.setoffset(y.getoffset()+100, recurse=True)
        z.setoffset(z.getoffset()-0x1000, recurse=True)

        result = dict(y.compare(z))
        if list(result.keys()) == [3]:
            s,o = result[3]
            if s is None and functools.reduce(lambda a,b:a+b,map(lambda x:x.serialize(),o),b'') == g.serialize()+b'\x40':
                raise Success
    @TestCase
    def test_container_set_uninitialized_type():
        class container(ptype.container): pass
        a = container().set(pint.uint32_t,pint.uint32_t)
        if a.size() == 8:
            raise Success

    @TestCase
    def test_container_set_uninitialized_instance():
        class container(ptype.container): pass
        a = container().set(*(pint.uint8_t().set(1) for _ in range(10)))
        if sum(x.int() for x in a) == 10:
            raise Success

    @TestCase
    def test_container_set_initialized_value():
        class container(ptype.container): pass
        a = container().set(*((pint.uint8_t,)*4))
        a.set(4,4,4,4)
        if sum(x.int() for x in a) == 16:
            raise Success

    @TestCase
    def test_container_set_initialized_type():
        class container(ptype.container): pass
        a = container().set(*((pint.uint8_t,)*4))
        a.set(pint.uint32_t,pint.uint32_t,pint.uint32_t,pint.uint32_t)
        if sum(x.size() for x in a) == 16:
            raise Success

    @TestCase
    def test_container_set_initialized_instance():
        class container(ptype.container): pass
        a = container().set(pint.uint8_t,pint.uint32_t)
        a.set(pint.uint32_t().set(0xfeeddead), pint.uint8_t().set(0x42))
        if (a.v[0].size(),a.v[0].int()) == (4,0xfeeddead) and (a.v[1].size(),a.v[1].int()) == (1,0x42):
            raise Success

    @TestCase
    def test_container_set_invalid():
        class container(ptype.container): pass
        a = container().set(ptype.type,ptype.type)
        try: a.set(5,10,20)
        except error.AssertionError:
            raise Success
        raise Failure

    #@TestCase
    def test_collect_pointers():
        ptype.source = provider.bytes(provider.random().consume(0x1000))
        a = pint.uint32_t
        b = ptype.clone(ptype.pointer_t, _object_=a)
        c = ptype.clone(ptype.pointer_t, _object_=b)
        d = ptype.clone(ptype.pointer_t, _object_=c)

        z = ptype.container(value=[], __name__='z')
        z.value.append(a())
        z.value.append(b())
        z.value.append(c())
        z.value.append(d())
        z.setoffset(z.getoffset(), True)

        a = z.value[0].set(0xfeeddead)
        b = z.value[1].set(a.getoffset())
        c = z.value[2].set(b.getoffset())
        d = z.value[3].set(c.getoffset())
        z.commit()

        result = [z.v[-1].int()]
        for x in z.v[-1].collect():
            result.append(x.l.int())

        if result == [8,4,0,0xfeeddead]:
            raise Success

    #@TestCase
    def test_collect_pointers2():
        import pecoff
        #a = pint.uint32_t()
        #b = a.new(ptype.pointer_t)
        class parentTester(object):
            def __eq__(self, other):
                return other.parent is None or builtins.isinstance(other, ptype.encoded_t) or issubclass(other.__class__, ptype.encoded_t)
        parentTester = parentTester()
        #c = b.getparent(parentTester())
        #print(builtins.isinstance(b, ptype.encoded_t))
        source = ptypes.provider.file('~/mshtml.dll')
        a = pecoff.Executable.File(source=source).l

        result = list(a.collect())
        for n in result:
            print(n)
        #for n in a.traverse(filter=lambda n: parentTester == n):
        #    if builtins.isinstance(n, ptype.encoded_t):
        #        b = n.d.getparent(parentTester)
        #        print(b.l)
        #        continue
        #    assert n.parent is None
        #    print(n.l)

    @TestCase
    def test_overcommit_serialize():
        class E(ptype.type):
            length = 2
        class block(ptype.container):
            def blocksize(self):
                return 4
        x = block(value=[])
        for d in bytearray(b'ABCD'):
            x.value.append( x.new(E).load(source=ptypes.prov.bytes(bytes(bytearray([d, d])))) )
        if x.serialize() == b'AABBCCDD':
            raise Success

    @TestCase
    def test_overcommit_write():
        class E(ptype.type):
            length = 2
        class block(ptype.container):
            def blocksize(self):
                return 4
        x = block(value=[])
        for d in bytearray(b'ABCD'):
            x.value.append( x.new(E).load(source=ptypes.prov.bytes(bytes(bytearray([d, d])))) )
        source = ptypes.prov.bytes(bytearray(b'\0'*16))
        x.commit(source=source)
        if source.backing == b'AABBCCDD\x00\x00\x00\x00\x00\x00\x00\x00':
            raise Success

    @TestCase
    def test_overcommit_load():
        class E(ptype.type):
            length = 2
        class block(ptype.container):
            def blocksize(self):
                return 4
        x = block(value=[])
        for d in bytearray(b'ABCD'):
            x.value.append( x.new(E).load(source=ptypes.prov.bytes(bytes(bytearray([d, d])))) )
        x.load(source=ptypes.prov.bytes(b'E'*16))
        if x.serialize() == b'EEEECCDD':
            raise Success

    @TestCase
    def test_container_append_type():
        class C(ptype.container): pass
        x = C()
        x.__append__(pint.uint32_t)
        x.__append__(pint.uint32_t)
        if x.serialize() == b'\x00\x00\x00\x00\x00\x00\x00\x00':
            raise Success

    @TestCase
    def test_wrapped_double_assignment():
        class T(ptype.wrapper_t): pass
        a = pstr.szstring().set('i still love you and fucking miss you, camacho.')
        b = pstr.szstring().set('i love you, camacho')

        x = T()
        x.object = a
        if x.serialize() != a.serialize():
            raise Failure

        x.object = b
        if x.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_encoded_double_reference():
        class T(ptype.encoded_t): pass
        a = pstr.szstring().set('i still love you and fucking miss you, camacho.')
        b = pstr.szstring().set('i made the wrong decision, im sorry man :-/')

        x = T()
        x.reference(a)
        if x.serialize() != a.serialize():
            raise Failure

        x.reference(b)
        if x.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_encoded_reference_commit():
        class T(ptype.encoded_t):
            _object_ = pstr.szstring
        a = pstr.szstring().set('i still love you and fucking miss you, camacho.')
        b = pstr.szstring().set('i made the wrong decision, im sorry man :-/')

        x = T()
        x.reference(a)
        if x.serialize() != a.serialize():
            raise Failure
        x.d.l.set(b.serialize().decode('ascii')).c
        if x.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_wrapper_cast_attributes():
        class t(ptype.encoded_t):
            class _value_(pstruct.type):
                def __init__(self, **attrs):
                    super(t._value_, self).__init__(**attrs)
                    f = self._fields_ = []
                    if getattr(self, 'WIN64', False):
                        f.extend([
                            (pint.uint64_t, 'Unencoded'),
                            (pint.uint64_t, 'Encoded'),
                        ])
                    else:
                        f.extend([
                            (pint.uint32_t, 'Encoded'),
                            (pint.uint32_t, 'Unencoded'),
                        ])
                    return

        class wtf(pstruct.type):
            _fields_ = [
                (t, 'what'),
            ]

        a = wtf(recurse=dict(WIN64=1)).a
        if a.WIN64 != 1 or a.attributes['WIN64'] != 1:
            raise AssertionError
        if a['what'].size() != 16 or a['what'].o.size() != 16:
            raise AssertionError

        x = a['what'].cast(t._value_)
        if x.size() == 16:
            raise Success
        raise Failure

    @TestCase
    def test_wrapper_value_property():
        class t(ptype.wrapper_t):
            @property
            def _value_(self):
                class fuck(ptype.block):
                    length = 4
                return fuck

        x = t()
        a, b = x.object, x.object
        if a is b:
            raise Success

    @TestCase
    def test_wrapper_value_closure():
        class t(ptype.wrapper_t):
            def _value_(self):
                class fuck(ptype.block):
                    length = 4
                return fuck

        x = t()
        a, b = x.object, x.object
        if a is b:
            raise Success

    @TestCase
    def test_encoded_object_property():
        class t(ptype.encoded_t):
            class _value_(ptype.block):
                length = 4

            @property
            def _object_(self):
                return pint.uint32_t

        x = t()
        a, b = x.d, x.d
        if a is b:
            raise Success

    @TestCase
    def test_wrapper_object_assign_1():
        class wrapped(ptype.wrapper_t):
            class _value_(ptype.block):
                length = 4

        o = wrapped()
        o.object = pint.uint32_t().set(0x41424344)
        if o.initializedQ() and o.value == o.serialize() == b'\x44\x43\x42\x41' and hasattr(o.object, 'int') and o.object.int() == 0x41424344:
            raise Success

    @TestCase
    def test_wrapper_object_assign_2():
        class wrapped(ptype.wrapper_t):
            class _value_(ptype.block):
                length = 4

        o = wrapped()
        o.object = pint.uint32_t().set(0x41424344)
        o.a
        if o.initializedQ() and o.value == o.serialize() == b'\x00\x00\x00\x00' and not hasattr(o.object, 'int') and o.object.serialize() == b'\x00\x00\x00\x00':
            raise Success

    @TestCase
    def test_wrapper_value_assign_1():
        '''wrapper_t.value is uninitialized at start'''
        class wrapped(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.type, length=4)
        x = wrapped()
        if x.value is None and not x.initializedQ():
            raise Success

    @TestCase
    def test_wrapper_value_assign_2():
        '''wrapper_t.value gets assigned during wrapper_t.alloc'''
        class wrapped(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.type, length=4)
        x = wrapped().alloc()
        if x.value == b'\0\0\0\0' and x.initializedQ():
            raise Success

    @TestCase
    def test_wrapper_value_assign_3():
        '''wrapper_t.value gets assigned during wrapper_t.load'''
        class wrapped(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.type, length=4)
        data = b'ABCD'
        x = wrapped().load(source=ptypes.prov.bytes(data))
        if x.value == data and x.initializedQ():
            raise Success

    @TestCase
    def test_wrapper_value_assign_4():
        '''wrapper_t.value gets assigned during wrapper_t.set'''
        class wrapped(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.type, length=4)
        data = b'ABCD'
        x = wrapped().set(data)
        if x.value == data and x.initializedQ():
            raise Success

    @TestCase
    def test_definition_lookup():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.lookup(50)
        if rec is t:
            raise Success

    @TestCase
    def test_definition_lookup_missing():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        try:
            rec = records.lookup(49)

        except KeyError:
            raise Success
        raise Failure(rec)

    @TestCase
    def test_definition_lookup_default():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.lookup(49, ptype.undefined)
        if rec is ptype.undefined:
            raise Success

    @TestCase
    def test_definition_withdefault():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.withdefault(50)
        if rec is t:
            raise Success

    @TestCase
    def test_definition_withdefault_default():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.withdefault(49)
        if rec is not t and builtins.issubclass(rec, records.default):
            raise Success

    @TestCase
    def test_definition_withdefault_default_attrib():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.withdefault(49, myattrib=42)
        if rec is not t and builtins.issubclass(rec, records.default) and rec.myattrib == 42:
            raise Success

    @TestCase
    def test_definition_withdefault_custom():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.withdefault(49, ptype.undefined)
        if rec is ptype.undefined and builtins.issubclass(rec, ptype.undefined):
            raise Success

    @TestCase
    def test_definition_withdefault_custom_attrib():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.withdefault(49, ptype.undefined, myattrib=42)
        if rec is not ptype.undefined and builtins.issubclass(rec, ptype.undefined) and rec.myattrib == 42:
            raise Success

    @TestCase
    def test_definition_get():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.get(49)
        if rec is records.default:
            raise Success

    @TestCase
    def test_definition_get_default():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.get(50, myattrib=42)
        if rec is not t and builtins.issubclass(rec, t) and rec.myattrib == 42:
            raise Success

    @TestCase
    def test_definition_get_default_attrib():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.get(49, myattrib=42)
        if rec is not records.default and builtins.issubclass(rec, records.default) and rec.myattrib == 42:
            raise Success

    @TestCase
    def test_definition_get_custom():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.get(49, ptype.undefined)
        if rec is ptype.undefined and builtins.issubclass(rec, ptype.undefined):
            raise Success

    @TestCase
    def test_definition_get_custom_attrib():
        class records(ptype.definition): cache = {}

        @records.define
        class t(ptype.type):
            type = 50

        rec = records.get(49, ptype.undefined, myattrib=42)
        if rec is not ptype.undefined and builtins.issubclass(rec, ptype.undefined) and rec.myattrib == 42:
            raise Success

    @TestCase
    def test_container_underalloc():
        class cunt(ptype.container):
            def load(self, **attrs):
                self.value = []
                self.value.append(pint.uint32_t())
                self.value.append(pint.uint32_t())
                return super(cunt, self).load(**attrs)
            def blocksize(self):
                return 9
        x = cunt(source=ptypes.provider.empty()).a
        if (x.size(), x.blocksize()) == (8, 9) and x.value[0].size() == x.value[1].size() == 4:
            raise Success

    @TestCase
    def test_container_underload():
        class cunt(ptype.container):
            def load(self, **attrs):
                self.value = []
                self.value.append(pint.uint32_t())
                self.value.append(pint.uint32_t())
                return super(cunt, self).load(**attrs)
            def blocksize(self):
                return 9
        x = cunt(source=ptypes.provider.empty()).l
        tests, properties = [], x.properties()
        tests.append(x.size() == 8 and x.blocksize() == 9)
        tests.append(all(item.blocksize() == 4 for item in x.value))
        tests.append(x.value[0].initializedQ() and x.value[0].size() == 4 and x.value[0].serialize() == b'\0\0\0\0')
        tests.append(x.value[1].initializedQ() and x.value[1].size() == 4 and x.value[1].serialize() == b'\0\0\0\0')
        tests.append(properties.get('underload', False) and not properties.get('uninitialized', False))
        if all(tests):
            raise Success

    @TestCase
    def test_container_alloc_uninitialized():
        class cunt(ptype.container):
            def load(self, **attrs):
                self.value = []
                self.value.append(pint.uint32_t())
                self.value.append(pint.uint32_t())
                return super(cunt, self).load(**attrs)
            def blocksize(self):
                return 7
        x = cunt(source=ptypes.provider.bytes(b'\0'*7 + b'\1'))
        try: x.a
        except Exception: pass
        tests, properties = [], x.properties()
        tests.append(x.size() == 7 == x.blocksize())
        tests.append(all(item.blocksize() == 4 for item in x.value))
        tests.append(x.value[0].initializedQ() and x.value[0].size() == 4 and x.value[0].serialize() == b'\0\0\0\0')
        tests.append((not x.value[1].initializedQ() and x.value[1].size() == 3 and x.value[1].serialize() == b'\0\0\0\0'))
        tests.append((not properties.get('underload', False) and properties.get('uninitialized', False)))
        if all(tests):
            raise Success

    @TestCase
    def test_container_underload_source():
        class cunt(ptype.container):
            def load(self, **attrs):
                self.value = []
                self.value.append(pint.uint32_t())
                self.value.append(pint.uint32_t())
                return super(cunt, self).load(**attrs)
        x = cunt(source=ptypes.provider.bytes(b'\0'*7))
        try: x.l
        except Exception: pass
        tests, properties = [], x.properties()
        tests.append(x.size() == 7 and x.blocksize() == 8)
        tests.append(all(item.blocksize() == 4 for item in x.value))
        tests.append(x.value[0].initializedQ() and x.value[0].size() == 4 and x.value[0].serialize() == b'\0\0\0\0')
        tests.append((not x.value[1].initializedQ() and x.value[1].size() == 3 and x.value[1].serialize() == b'\0\0\0\0'))
        tests.append(properties.get('underload', False) and properties.get('uninitialized', False))
        if all(tests):
            raise Success

    @TestCase
    def test_container_underload_blocksize():
        class cunt(ptype.container):
            def load(self, **attrs):
                self.value = []
                self.value.append(pint.uint32_t())
                self.value.append(pint.uint32_t())
                return super(cunt, self).load(**attrs)
            def blocksize(self):
                return 7
        x = cunt(source=ptypes.provider.bytes(b'\0'*7 + b'\1'))
        try: x.l
        except Exception: pass
        tests, properties = [], x.properties()
        tests.append(x.size() == 7 == x.blocksize())
        tests.append(all(item.blocksize() == 4 for item in x.value))
        tests.append(x.value[0].initializedQ() and x.value[0].size() == 4 and x.value[0].serialize() == b'\0\0\0\0')
        tests.append((not x.value[1].initializedQ() and x.value[1].size() == 3 and x.value[1].serialize() == b'\0\0\0\0'))
        tests.append((not properties.get('underload', False) and properties.get('uninitialized', False)))
        if all(tests):
            raise Success

    @TestCase
    def test_getparent_instance():
        class d(pstruct.type): _fields_ = [(pint.uint32_t, 'd')]
        class c(pstruct.type): _fields_ = [(d, 'c')]
        class b(pstruct.type): _fields_ = [(c, 'b')]
        class a(pstruct.type): _fields_ = [(b, 'a')]

        x = a().a
        v = x['a']['b']['c']['d']
        res = v.getparent(x)
        if builtins.isinstance(res, b):
            raise Success

    @TestCase
    def test_getparent_top():
        class d(pstruct.type): _fields_ = [(pint.uint32_t, 'd')]
        class c(pstruct.type): _fields_ = [(d, 'c')]
        class b(pstruct.type): _fields_ = [(c, 'b')]
        class a(pstruct.type): _fields_ = [(b, 'a')]

        x = a().a
        v = x['a']['b']['c']['d']
        res = v.getparent(None)
        if res.parent is None and builtins.isinstance(res, a):
            raise Success

    @TestCase
    def test_getparent_types():
        class d(pstruct.type): _fields_ = [(pint.uint32_t, 'd')]
        class c(pstruct.type): _fields_ = [(d, 'c')]
        class b(pstruct.type): _fields_ = [(c, 'b')]
        class a(pstruct.type): _fields_ = [(b, 'a')]

        x = a().a
        v = x['a']['b']['c']['d']
        res = v.getparent((a,b,c))
        if builtins.isinstance(res, c):
            raise Success

    @TestCase
    def test_getparent_type_1():
        class d(pstruct.type): _fields_ = [(pint.uint32_t, 'd')]
        class c(pstruct.type): _fields_ = [(d, 'c')]
        class b(pstruct.type): _fields_ = [(c, 'b')]
        class a(pstruct.type): _fields_ = [(b, 'a')]

        x = a().a
        v = x['a']['b']['c']['d']
        res = v.getparent(a)
        if res.parent is None and builtins.isinstance(res, a):
            raise Success

    @TestCase
    def test_getparent_type_2():
        class d(pstruct.type): _fields_ = [(pint.uint32_t, 'd')]
        class c(pstruct.type): _fields_ = [(d, 'c')]
        class b(pstruct.type): _fields_ = [(c, 'b')]
        class a(pstruct.type): _fields_ = [(b, 'a')]

        x = a().a
        v = x['a']['b']['c']['d']
        res = v.getparent(b)
        if builtins.isinstance(res, b):
            raise Success

    @TestCase
    def test_get_field_0():
        class t(pstruct.type): _fields_ = [(pint.uint8_t, 'a'), (pint.uint8_t, 'b'), (pint.uint32_t, 'c')]

        x = t().alloc(a=1, b=2, c=3)
        if x.field().serialize() == x.serialize():
            raise Success

    @TestCase
    def test_get_field_1():
        class t(pstruct.type): _fields_ = [(pint.uint8_t, 'a'), (pint.uint8_t, 'b'), (pint.uint32_t, 'c')]

        x = t().alloc(a=1, b=2, c=3)
        if x.field('b').int() == 2:
            raise Success

    @TestCase
    def test_get_field_2():
        class t1(pstruct.type): _fields_ = [(pint.uint32_t, 'c')]
        class t2(pstruct.type): _fields_ = [(t1, 'b')]
        class t3(pstruct.type): _fields_ = [(t2, 'a')]

        x = t3().a
        if x.field('a', 'b', 'c').int() == 0:
            raise Success

    @TestCase
    def test_definition_enum_descriptor_1():
        class d(ptype.definition):
            cache = {}
            class _enum_(pint.enum):
                _values_ = [('a', 2)]

        if {(key, value) for key, value in d.enum._values_} == {('a', 2)}:
            raise Success

    @TestCase
    def test_definition_enum_descriptor_2():
        class d(ptype.definition):
            cache = {}
            class _enum_(pint.enum):
                pass

        @d.define(type=2)
        class a(ptype.type):
            length = 1

        if {(key, value) for key, value in d.enum._values_} == {('a', 2)}:
            raise Success

    @TestCase
    def test_definition_enum_descriptor_3():
        class d(ptype.definition):
            cache = {}
            class _enum_(pint.enum):
                _values_ = [('b', 1)]

        @d.define(type=2)
        class a(ptype.type):
            length = 1

        if {(key, value) for key, value in d.enum._values_} == {('a', 2), ('b', 1)}:
            raise Success

    @TestCase
    def test_definition_enum_descriptor_4():
        class d(ptype.definition):
            cache = {}
            class _enum_(pint.enum):
                _values_ = [('b', 2)]

        @d.define(type=2)
        class a(ptype.type):
            length = 1

        if {(key, value) for key, value in d.enum._values_} == {('b', 2)}:
            raise Success

    @TestCase
    def test_definition_type_descriptor_1():
        class d(ptype.definition):
            cache = {}
            class _object_(pint.uint32_t):
                pass

        if hasattr(d, 'type') and d.type().a.size() == 4:
            raise Success

    @TestCase
    def test_definition_type_descriptor_2():
        def py3_object_(length):
            class b(ptype.block): pass
            b.length = length
            return b()
        def py2_object_(*args):
            return py3_object_(*args)
        class d(ptype.definition):
            cache = {}
            _object_ = staticmethod(py2_object_) if sys.version_info.major < 3 else py3_object_
        if hasattr(d, 'type') and d.type(4).a.size() == 4:
            raise Success

    @TestCase
    def test_definition_type_descriptor_3():
        class d(ptype.definition):
            cache = {}
            @classmethod
            def _object_(cls, length):
                class b(ptype.block): pass
                b.length = length
                return b()
        if hasattr(d, 'type') and d.type(4).a.size() == 4:
            raise Success

    @TestCase
    def test_definition_type_descriptor_4():
        class d(ptype.definition):
            cache = {}
            @staticmethod
            def _object_(length):
                class b(ptype.block): pass
                b.length = length
                return b()
        if hasattr(d, 'type') and d.type(4).a.size() == 4:
            raise Success

    @TestCase
    def test_nonzero_type_1():
        x = ptype.type().a
        if x:
            raise Success

    @TestCase
    def test_nonzero_container_2():
        x = ptype.container(value=[]).a
        if x:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
