import sys,os,math
import six,logging

__all__ = 'defaults,byteorder'.split(',')

class field:
    class descriptor(object):
        def __init__(self):
            self.__value__ = {}
        def __set__(self, instance, value):
            self.__value__[instance] = value
        def __get__(self, instance, type=None):
            return self.__value__.get(instance)
        def __delete__(self, instance):
            raise AttributeError

    class __enum_descriptor(descriptor):
        __option = set
        def option(self, name, documentation=''):
            cls = type(self)
            res = type(name, cls, {'__doc__': documentation})
            self.__option__.add(res)
            return res
        def __set__(self, instance, value):
            if value in self.__option__:
                return field.descriptor.__set__(self, instance, value)
            raise ValueError('{!r} is not a member of {!r}'.format(value, self.__option__))

    class __type_descriptor(descriptor):
        __type__ = type
        def __set__(self, instance, value):
            if (hasattr(self.__type__, '__iter__') and type(value) in self.__type__) or isinstance(value, self.__type__):
                return field.descriptor.__set__(self, instance, value)
            raise ValueError('{!r} is not an instance of {!r}'.format(value, self.__type__))

    class __set_descriptor(descriptor):
        set, get = None, None
        def __init__(self):
            return
        def __set__(self, instance, value):
            res = self.__getattribute__('set')
            return res.im_func(value) if sys.version_info.major < 3 else res.__func__(value)
        def __get__(self, instance, type=None):
            res = self.__getattribute__('get')
            return res.im_func() if sys.version_info.major < 3 else res.__func__()

    class __bool_descriptor(descriptor):
        def __set__(self, instance, value):
            if not isinstance(value, bool):
                logging.warn("rvalue {!r} is not of boolean type. Coercing it into one : ({:s} != {:s})".format(value, type(value).__name__, bool.__name__))
            return field.descriptor.__set__(self, instance, bool(value))

    @classmethod
    def enum(cls, name, options=(), documentation=''):
        base = cls.__enum_descriptor
        attrs = dict(base.__dict__)
        attrs['__option__'] = set(options)
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def option(cls, name, documentation='', base=object):
        return type(name, (base,), {'__doc__': documentation})
    @classmethod
    def type(cls, name, subtype, documentation=''):
        base = cls.__type_descriptor
        attrs = dict(base.__dict__)
        attrs['__type__'] = subtype
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def set(cls, name, fetch, store, documentation=''):
        base = cls.__set_descriptor
        attrs = dict(base.__dict__)
        attrs['__doc__'] = documentation
        attrs['set'] = store
        attrs['get'] = fetch
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def constant(cls, name, value, documentation=''):
        base = cls.descriptor
        attrs = dict(base.__dict__)
        def raiseAttributeError(self, instance, value):
            raise AttributeError
        attrs['__set__'] = raiseAttributeError
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def bool(cls, name, documentation=''):
        base = cls.__bool_descriptor
        attrs = dict(base.__dict__)
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()

def namespace(cls):
    # turn all instances of things into read-only attributes
    readonly = []
    if hasattr(property, '__isabstractmethod__'):
        readonly.append(property.__isabstractmethod__)
    readonly.append(property.deleter)

    attributes, properties, subclass = {}, {}, {}
    for name, value in cls.__dict__.items():
        if hasattr(value, '__name__') and all(not isinstance(value, item.__class__) for item in readonly):
            value.__name__ = '.'.join([cls.__name__, name])
        if name.startswith('_') or isinstance(value, property):
            attributes[name] = value
        elif not six.callable(value) or isinstance(value, type):
            properties[name] = value
        elif not hasattr(value, '__class__'):
            subclass[name] = namespace(value)
        else:
            attributes[name] = value
        continue

    def collectproperties(object):
        result = []
        for name, value in object.items():
            if isinstance(value, type):
                fmt = '<>'
            elif hasattr(value, '__class__'):
                fmt = '{!r}'.format(value)
            else:
                raise ValueError(name)
            doc = value.__doc__.split('\n')[0] if value.__doc__ else None
            result.append((name, fmt, doc))
        return result

    def formatproperties(items):
        namewidth = max(len(name) for name, _, _ in items)
        formatwidth = max(len(fmt) for _, fmt, _ in items)
        return [('{name:{}} : {format:{}} # {doc}' if documentation else '{name:{}} : {format:{}}').format(namewidth, formatwidth, name=name, format=value, doc=documentation) for name, value, documentation in items]

    def __repr__(self):
        props = collectproperties(properties)
        formatted = formatproperties(props)
        descr = ('{{{!s}}} # {}\n' if cls.__doc__ else '{{{!s}}}\n')
        subs = ['{{{}.{}}}\n...'.format(cls.__name__, name) for name in subclass.keys()]
        res = descr.format(cls.__name__, cls.__doc__) + '\n'.join(formatted)
        if subs:
            return res + '\n' + '\n'.join(subs) + '\n'
        return res + '\n'

    def __setattr__(self, name, value):
        if name in attributes:
            object.__setattr__(self, name, value)
            return
        raise AttributeError('Configuration \'{:s}\' does not have field named \'{:s}\''.format(cls.__name__, name))

    attributes['__repr__'] = __repr__
    attributes['__setattr__'] = __setattr__
    attributes.update((name, property(fget=lambda _, name=name: properties[name])) for name in properties)
    attributes.update((name, property(fget=lambda _, name=name: subclass[name])) for name in subclass)
    cons = type(cls.__name__, cls.__bases__, attributes)
    return cons()

def configuration(cls):
    attributes, properties, subclass = dict(cls.__dict__), {}, {}
    for name, value in attributes.items():
        if isinstance(value, field.descriptor):
            properties[name] = value
        elif not hasattr(value, '__class__'):
            subclass[name] = configuration(value)
        continue

    def collectproperties(object, values):
        result = []
        for name, value in object.items():
            documentation = value.__doc__.split('\n')[0] if value.__doc__ else None
            result.append((name, values[name], documentation))
        return result

    def formatproperties(items):
        namewidth = max(len(name) for name, _, _ in items)
        formatwidth = max(len("{!r}".format(format)) for _, format, _ in items)
        return [(('{{name:{:d}}} = {{values:<{:d}}} # {{doc}}' if documentation else '{{name:{:d}}} = {{values:<{:d}}}').format(namewidth, formatwidth)).format(name=name, values=values, doc=documentation) for name, values, documentation in items]

    def __repr__(self):
        descr = ('[{!s}] # {}\n' if cls.__doc__ else '[{!s}]\n')
        values = {name : getattr(self, name, None) for name in properties}
        items = collectproperties(properties, values)
        res = descr.format(cls.__name__, cls.__doc__.split('\n')[0] if cls.__doc__ else None) + '\n'.join(formatproperties(items))
        subs = ['[{}.{}]\n...'.format(cls.__name__, name) for name in subclass.keys()]
        if subs:
            return res + '\n' + '\n'.join(subs) + '\n'
        return res + '\n'

    def __setattr__(self, name, value):
        if name in attributes:
            object.__setattr__(self, name, value)
            return
        raise AttributeError('Namespace \'{:s}\' does not have a field named \'{:s}\''.format(cls.__name__, name))

    attributes['__repr__'] = __repr__
    attributes['__setattr__'] = __setattr__
    attributes.update({name : property(fget=lambda _, name=name: subclass[name]) for name in subclass})
    result = type(cls.__name__, cls.__bases__, attributes)
    return result()

### constants that can be used as options
@namespace
class byteorder:
    '''Byte order constants'''
    bigendian = field.option('bigendian', 'Specify big-endian ordering')
    littleendian = field.option('littleendian', 'Specify little-endian ordering')

@namespace
class partial:
    fractional = field.option('fractional', 'Display the offset as a fraction of the full bit (0.0, 0.125, 0.25, ..., 0.875)')
    hex = field.option('hexadecimal', 'Display the partial-offset in hexadecimal (0.0, 0.2, 0.4, ..., 0.c, 0.e)')
    bit = field.option('bit', 'Display just the bit number (0.0, 0.1, 0.2, ..., 0.7)')

### new-config
@configuration
class defaults:
    log = field.type('default-logger', logging.Filterer, 'Default place to log progress')

    class integer:
        size = field.type('integersize', six.integer_types, 'The word-size of the architecture')
        order = field.enum('byteorder', (byteorder.bigendian,byteorder.littleendian), 'The endianness of integers/pointers')

    class ptype:
        clone_name = field.type('clone_name', six.string_types, 'This will only affect newly cloned types')
        noncontiguous = field.bool('noncontiguous', 'Disable optimization for loading ptype.container elements contiguously. Enabling this allows there to be \'holes\' within a list of elements in a container and disables an important optimization.')

    class pint:
        bigendian_name = field.type('bigendian_name', six.string_types, 'Modifies the name of any integers that are big-endian')
        littleendian_name = field.type('littleendian_name', six.string_types, 'Modifies the name of any integers that are little-endian')

    class parray:
        break_on_zero_sized_element = field.bool('break_on_zero_sized_element', 'Terminate an array if the size of one of it\'s elements is invalid instead of possibly looping indefinitely.')
        break_on_max_count = field.bool('break_on_max_count', 'If a dynamically created array is larger than max_count, then fail it\'s creation. If not, then issue a warning.')
        max_count = field.type('max_count', six.integer_types, 'If max_count is larger than 0, then notify via a warning or an exception based on the value of \'break_on_max_count\'')

    class pstruct:
        use_offset_on_duplicate = field.bool('use_offset_on_duplicate', 'If more than one field has the same name, then suffix the field by it\'s offset. Otherwise use the field\'s index.')

    class display:
        show_module_name = field.bool('show_module_name', 'include the full module name in the summary')
        show_parent_name = field.bool('show_parent_name', 'include the parent name in the summary')
        mangle_with_attributes = field.bool('mangle_with_attributes', 'when doing name-mangling, include all atomic attributes of a ptype as a formatstring keyword')

        class hexdump:
            '''Formatting for a hexdump'''
            width = field.type('width', six.integer_types)
            threshold = field.type('threshold', six.integer_types)

        class threshold:
            '''Width and Row thresholds for displaying summaries'''
            summary = field.type('summary_threshold', six.integer_types)
            summary_message = field.type('summary_threshold_message', six.string_types)
            details = field.type('details_threshold', six.integer_types)
            details_message = field.type('details_threshold_message', six.string_types)

    class pbinary:
        '''How to display attributes of an element containing binary fields which might not be byte-aligned'''
        offset = field.enum('offset', (partial.bit,partial.fractional,partial.hex), 'which format to display the sub-offset for binary types')

        bigendian_name = field.type('bigendian_name', six.string_types, 'format specifier defining an element that is read most-significant to least-significant')
        littleendian_name = field.type('littleendian_name', six.string_types, 'format specifier defining an element that is read least-significant to most-significant')

    def __getsource():
        global ptype
        return ptype.source
    def __setsource(value):
        global ptype
        if all(hasattr(value, method) for method in ('seek','store','consume')) or isinstance(value, provider.base):
            ptype.source = value
            return
        raise ValueError("Invalid source object")
    source = field.set('default-source', __getsource, __setsource, 'Default source to load/commit data from/to')

try:
    from . import ptype

except ImportError:
    # XXX: recursive
    import ptype

### defaults
# logging
defaults.log = log = logging.getLogger('ptypes')
log.setLevel(logging.root.level)
log.propagate = 1
res = logging.StreamHandler(None)
res.setFormatter(logging.Formatter("[%(created).3f] <%(process)x.%(thread)x> [%(levelname)s:%(name)s] %(message)s", None))
log.addHandler(res)
del(res, log)

# general integers
defaults.integer.size = math.trunc(math.log(2 * (sys.maxsize + 1), 2) // 8)
defaults.integer.order = byteorder.littleendian if sys.byteorder == 'little' else byteorder.bigendian if sys.byteorder == 'big' else None

# display
defaults.display.show_module_name = False
defaults.display.show_parent_name = False
defaults.display.hexdump.width = 16
defaults.display.hexdump.threshold = 8
defaults.display.threshold.summary = 80
defaults.display.threshold.details = 8
defaults.display.threshold.summary_message = ' ..skipped ~{leftover} bytes.. '
defaults.display.threshold.details_message = ' ..skipped {leftover} rows, {skipped} bytes.. '
defaults.display.mangle_with_attributes = False

# array types
defaults.parray.break_on_zero_sized_element = False
defaults.parray.break_on_max_count = False
defaults.parray.max_count = six.MAXSIZE

# structures
defaults.pstruct.use_offset_on_duplicate = True

# root types
defaults.ptype.noncontiguous = False
#defaults.ptype.clone_name = 'clone({})'
#defaults.pint.bigendian_name = 'bigendian({})'
#defaults.pint.littleendian_name = 'littleendian({})'
defaults.ptype.clone_name = 'c({})'

# integer types
defaults.pint.bigendian_name = 'be({})' if sys.byteorder.startswith('little') else '{}'
defaults.pint.littleendian_name = 'le({})' if sys.byteorder.startswith('big') else '{}'

# pbinary types
defaults.pbinary.offset = partial.hex
defaults.pbinary.bigendian_name = 'pb({})'
defaults.pbinary.littleendian_name = 'pble({})'

if __name__ == '__main__':
    @namespace
    class consts:
        bigendian = field.option('bigendian', 'Big-endian integers')
        littleendian = field.option('littleendian', 'Little-endian integers')
        size = 20
        whatever = object()
        class huh:
            what = 5
            default = 10
            blah = object()
            class more:
                whee = object()

        class blah:
            pass

    import logging
    @configuration
    class config(object):
        byteorder = field.enum('byteorder', (byteorder.bigendian,byteorder.littleendian), 'The endianness of integers/pointers')
        integersize = field.type('integersize', six.integer_types, 'The word-size of the architecture')

        class display:
            summary = field.type('single-line', six.integer_types)
            details = field.type('multi-line', six.integer_types)
            show_module = field.bool('show-module-name')

        def __getlogger():
            return logging.root
        def __setlogger(value):
            logging.root = value
        logger = field.set('default-logger', __getlogger, __setlogger, 'Default place to log progress')
        #logger = field.type('default-logger', logging.Filterer, 'Default place to log progress')

        def __getsource():
            return ptype.source
        def __setsource(value):
            if not isinstance(value, provider.base):
                raise ValueError("Invalid source object")
            ptype.source = value
        source = field.set('default-source', __getsource, __setsource, 'Default source to load/commit data from/to')

    #ptypes.config.logger = logging.root
    print('{!r}'.format(consts))
    print('{!r}'.format(config))
