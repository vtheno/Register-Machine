#coding=utf-8
class Error(Exception):pass
class Vector(object):
    def __init__(self,size,symbol):
        self.value = [symbol] * size
    def ref(self,index):
        return self.value[index]
    def set(self,index,value):
        self.value[index] = value
    def __repr__(self):
        return repr(self.value)

class TypeData(object):
    def __init__(self,tag,val):
        self.tag = tag
        self.val = val
    def __repr__(self):
        return repr("{}{}".format(self.tag,self.val))

class Cons(object):
    def __init__(self,a,b):
        self.first = a
        self.rest  = b
    def isNull(self):
        #return self.first == empty and self.rest == empty
        return self.first == None and self.rest == None
    def __repr__(self):
        if self.isNull():
            return "nil"
        else:
            return "( {} . {} )".format(self.first,self.rest)

nil  = Cons(None,None)
def List(*pylst):
    lst = list(pylst)
    if len(lst) > 0:
        car,cdr = lst[0],lst[1:]
    else:
        return nil
    if cdr == []:
        return Cons(car,nil)
    return Cons(car,List(*cdr))

def pointerp(typedata):
    return typedata.tag == 'p'

class gc(object):
    root = [] # root is object table
    mem_size = 15
    n = 'n'
    e = 'e'
    s = 's'
    p = 'p'
    the_empty = TypeData(e,0)
    def __init__(self):
        self.the_free = 0
        self.the_cars = Vector(self.mem_size,'**')
        self.the_cdrs = Vector(self.mem_size,'**')
        self.new_free = 0
        self.new_cars = Vector(self.mem_size,'**')
        self.new_cdrs = Vector(self.mem_size,'**')
    def display_all_mem(self):
        print "root____:",self.root
        print "the_free:",self.the_free
        print "the_cars:",self.the_cars
        print "the_cdrs:",self.the_cdrs
        print "new_free:",self.new_free
        print "new_cars:",self.new_cars
        print "new_cdrs:",self.new_cdrs

    def make_pointer(self,val):
        return TypeData(self.p,val)
    def make_broken_heart(self):
        return TypeData('bh',0)
    def makeTypeData(self,val):
        print "makeTypeData:",val,type(val),isinstance(val,Cons)
        if isinstance(val,int):
            return TypeData('n',val)
        if isinstance(val,str):
            return TypeData('s',val)
        if isinstance(val,Cons):
            if val.isNull() :
                return TypeData('e',0)
            else:
                return self.store_list(val)
        else:
            raise Error("makeTypeDataError:",val)

    def lengthx(self,lst):
        if lst.isNull():
            return 0
        elif isinstance(lst.first,Cons):
            return 1 + self.lengthx(lst.first) + self.lengthx(lst.rest)
        else:
            return 1 + self.lengthx(lst.rest)

    def size(self,val):
        if isinstance(val,Cons):
            return self.lengthx(val)
        return 0
    def storage_space_available(self):
        return self.mem_size - self.the_free
    def sufficient_space_for(self,val):
        needsize = self.size(val)
        flag     = needsize <= self.storage_space_available()
        print flag,needsize,self.storage_space_available()
        if flag:
            return flag
        else:
            return self.gc() and flag
    def define_sym(self,var,val):
        if self.sufficient_space_for(val):
            value = self.makeTypeData(val)
            # namespace is self.root then can changed to dict map or other data struct 
            self.root.append( (var,value) )
        else:
            raise Error( "define-sym: insufficient space for {}".format(val))
    def store_list(self,lst):
        loc = self.the_free
        self.the_free += 1
        print "store_list:",lst,loc
        # there can change data type to py list
        if isinstance(lst.first,Cons):
            self.the_cars.set(loc,self.store_list(lst.first))
        else:
            self.the_cars.set(loc,self.makeTypeData(lst.first))
        if isinstance(lst.rest,Cons):
            if not lst.rest.isNull():
                self.the_cdrs.set(loc,self.store_list(lst.rest))
            else:
                self.the_cdrs.set(loc,self.the_empty)
        return self.make_pointer(loc)

    def forwarded(self,ptr):
        flag1 = ptr.tag == self.p # pointer? ptr
        flag2 = self.the_cars.ref(ptr.val).tag == 'bh' # broken_heart?
        return flag1 and flag2
    def forwarding_addr(self,ptr):
        return self.the_cdrs.ref(ptr.val)
    def move(self,ptr):
        print "move:",ptr
        if self.forwarded(ptr):
            return self.forwarding_addr(ptr)
        else:
            loc = self.new_free
            old_loc = ptr.val
            self.new_free += 1
            self.new_cars.set(loc,self.the_cars.ref( old_loc) )
            self.new_cdrs.set(loc,self.the_cdrs.ref( old_loc) )
            self.the_cars.set(old_loc,self.make_broken_heart())
            new_addr = self.make_pointer(loc)
            self.the_cdrs.set(old_loc,new_addr)
            return new_addr

    def scan(self,addr):
        while addr < self.new_free:
            ncar = self.new_cars.ref(addr)
            ncdr = self.new_cdrs.ref(addr)
            if ncar.tag == self.p:
                self.new_cars.set(addr,self.move(ncar))
            if ncdr.tag == self.p:
                self.new_cdrs.set(addr,self.move(ncdr))
            #self.scan(addr+1)
            addr+=1 

    def atomData(self,xxx):
        return xxx[1].tag in [self.e,self.s,self.n]
    def listData(self,xxx):
        return xxx[1].tag in [self.p]
    def new_frame(self,old_frame):
        var = old_frame[0]
        typed_data = old_frame[1]
        td = self.move(typed_data)
        return (var,td)
    def process(self,table):
        print "process:",table
        res = [ ]
        for i in table:
            print "process:",res
            if self.atomData(i):
                res.append(i)
            if self.listData(i):
                res.append( self.new_frame(i) )
        print "process:",res
        return res
    def flip(self):
        #temp = None
        #temp = self.the_cars
        self.the_cars,self.new_cars = self.new_cars,self.the_cars
        #self.new_cars = temp
        #temp = self.the_cdrs
        self.the_cdrs,self.new_cdrs = self.new_cdrs,self.the_cdrs
        #self.new_cdrs = temp
        self.the_free,self.new_free = self.new_free,0
        #self.new_free = 0
    def gc(self):
        print "root:",self.root
        self.root = self.process(self.root)
        self.scan(0)
        self.flip()
        return True
a = gc()
a.display_all_mem()
a.define_sym('a',1)
a.define_sym('b','b')
a.define_sym('c',List() )
a.define_sym('a',List(1,2,3,4,5) )
a.define_sym('b',List(1,2,3,4) )
# define_sym equal const xxx
a.define_sym('shard','huk')
a.display_all_mem()
#a.display_all_mem()
#print a.lengthx(List(1,2,3))
