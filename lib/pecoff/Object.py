import ptypes
import definitions
from warnings import warn

def open(filename, **kwds):
    res = File()
    res.source = ptypes.provider.file(filename, **kwds)
    res.load()
    res.filename = filename     # ;)
    return res

class File(definitions.headers.CoffHeader, definitions.__base__.BaseHeader): pass

if __name__ == '__main__':
    import sys
    sys.path.append('f:/work')
    sys.path.append('f:/work/syringe.git/lib')

    ## parse the file
    import pecoff, ptypes
    from ptypes import provider

    print '-'*20 + 'loading file..'
    coff = pecoff.Object.File()
    coff.source = provider.file('../../obj/inject-helper.obj')
    coff.load()
    print coff['Header']
    print coff['Sections']

    ### check everything from the symbol table's perspective
    sst = coff['Header'].getsymbols()
    sst.load()

    symboltable = sst['Symbols']

    print '-'*20 + 'printing external symbols'
    ## build list of external symbols
    sym_external = {}
    for name in sst.names():
        v = sst.get(name)
        if int(v['StorageClass']) == 2:
            sym_external[name] = v
        continue

    print '\n'.join(map(repr, sym_external.values()))

    print '-'*20 + 'printing statically defined symbols'
    ## build list of static symbols
    sym_static = {}
    for name in sst.names():
        v = sst.get(name)
        if int(v['StorageClass']) == 3 and int(v['Value']) == 0:
            num = v['SectionNumber'].get()
            sym_static[num] = (v, sst.getaux(name))
        continue

    for x in sym_static.keys():
        sym,aux = sym_static[x]
        print sym
        if aux:
            print '\n'.join(map(repr,aux))

    print '-'*20 + 'check that the number of relocations in the symboltable matches the section\'s'
    ## build list of static symbols
    ## sanity check that the number of relocations are correct
    sections = coff['Sections']
    for index,(sym,aux) in sym_static.items():
        section = sections[index]
        sectioncount = int(section['NumberOfRelocations'])
        if len(aux) > 0:
            symbolcount = int(aux[0]['NumberOfRelocations'])
            if sectioncount != symbolcount:
                warn('number of relocations (%d) for section %s differs from section definition (%d)'% (symbolcount,sym['Name'].get(),sectioncount))
        print 'relocated section %s'% repr(section)
        continue

    print '-'*20 + 'adding some symbols'
    ## reassign some symbols
    sst.assign('_TlsAlloc@0', 0xcccccccc)
    sst.assign('.text', 0x4010000)

    print '-'*20 + 'printing all symbol information'
    print '\n'.join(map(repr, symboltable))

    def formatrelocation(relo, symboltable):
        symbol = symboltable[ int(relo['SymbolTableIndex']) ]
        return '\n'.join([repr(symbol), repr(relo)]) + '\n'

    ### everything from the section's perpsective
    print '-'*20 + 'printing all relocations'
    for section in coff['Sections']:
        relocations = section.getrelocations()
        data = section.getdata().load()
        section.data, section.relocations = data.serialize(), relocations   # save for later
        continue
        
    ## do relocations for every section
    for section in coff['Sections']:
        data = section.data
        for r in section.relocations.load():
            print r
            section.data = r.relocate(section.data, symboltable)
        continue
        
    ## print out results
    print '-'*20 + 'printing relocated sections'
    for section in coff['Sections']:
        print section['Name'].get()
        print ptypes.utils.indent('\n'.join(map(lambda x: formatrelocation(x, symboltable), section.relocations)))
        print ptypes.utils.hexdump(section.data)

    if False:
        print '-'*20 + 'dumping relocated sections'
        for index in range( len(sections) ):
            section = sections[index]

            name = ptypes.utils.strdup( section['Name'].serialize(), terminator='\x00')
            print name,
            if index in sym_static.keys():
                sym,aux = sym_static[index]
                print sym['Name'].get(), sym['SectionNumber'].get(), int(sym['Value'])
                data = section.getrelocateddata(symboltable)
            else:
                print 
                data = section.getdata().serialize()

    #        print ptypes.utils.hexdump( section.getdata().serialize() )
            print ptypes.utils.hexdump( data )

            x = file('%s.section'% name[1:], 'wb')
            x.write(data)
            x.close()
