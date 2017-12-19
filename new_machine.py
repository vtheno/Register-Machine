#coding=utf-8
# todo : 5.3 表结构存储器
def show(machine):
    print '--------------------start'
    for i,v in zip(machine.register_table.keys(),machine.register_table.values()):
        print '<',i,':',v,'>'
    print machine.labels
    print machine.stack
    print machine.display_all_mem()
    print '--------------------end'

class Error(Exception): pass
def checkWapper(value,Type,error):
    try:
        assert isinstance(value,Type)
        return value
    except AssertionError:
        raise error("type({}) :: {} not is {} ".format(value,
                                                       type(value),
                                                          Type
                                                      ))
class Vector(object):
    def __init__(self,size,symbol):
        self.value = [symbol] * size
    def ref(self,index):
        return self.value[index]
    def set(self,index,value):
        self.value[index] = value
    def __repr__(self):
        return repr(self.value)

class Register(object):
    def __init__(self,value):
        self.value = value
    def get(self):
        return self.value
    def set(self,value):
        # class ptr(object) 
        class RegisterSetError(Error): pass
        self.value = value
    def __repr__(self):
        return "< Register {} >".format(self.value)
    
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

class Machine(object):
    pc             = Register( 0 )
    flag           = Register( 0 )
    # memory 
    root = [] # root is object table
    mem_size = 15
    n = 'n'
    e = 'e'
    s = 's'
    p = 'p'
    the_empty = TypeData(e,0)
    the_free = 0
    the_cars = Vector(mem_size,'**')
    the_cdrs = Vector(mem_size,'**')
    new_free = 0
    new_cars = Vector(mem_size,'**')
    new_cdrs = Vector(mem_size,'**')
    # disk         = Disk()
    # base op start
    def reg(self,name):
        class MachineRegError(Error):pass
        checkWapper(name,str,MachineRegError)
        if name not in self.register_table.keys():
            raise MachineRegError("{} not in reg table".format(name))
        return self.register_table.get(name).get()
        


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
            return self.root
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
        self.the_cars,self.new_cars = self.new_cars,self.the_cars
        self.the_cdrs,self.new_cdrs = self.new_cdrs,self.the_cdrs
        self.the_free,self.new_free = self.new_free,0
    def gc(self):
        print "root:",self.root
        self.root = self.process(self.root)
        self.scan(0)
        self.flip()
        return True

    def const(self,constant_value):
        class MachineConstError(Error):pass
        checkWapper(constant_value,str,MachineConstError)
        if constant_value.isdigit():
            # 不应该是在这里 这里应该只是返回类型解析 
            # 由 assgin 对 寄存器进行操作 root 维护的是寄存器名表
            return self.define_sym('var',int(constant_value))
        if constant_value.isalpha():
            return self.define_sym('var',constant_value)
            
    def label(self,label_name):
        class MachineLabelError(Error):pass
        checkWapper(label_name,str,MachineLabelError)
        if label_name not in self.labels.keys():
            raise MachineLabelError("{} is not label".format(label_name))
        return self.labels.get(label_name)

    def op(self,name,args):
        values = list( [ ] )
        print 'op_name:',name,'args:',args
        func   = self.other_op_table[name]
        for i in args:
            fn_name,arg = i[0],i[1:]
            temp = self.base_op_table[fn_name]
            #print "op:",temp
            values.append(temp(*arg))
        print "op:",values
        value = func(*values)
        print "op:",value
        return value
    # base op end 
    def setMachineReg(self,*RegNames):
        class SetMachineRegisterError(Error):pass
        if not all(map(lambda x:isinstance(x,str),list(RegNames))):
            raise SetMachineRegisterError
        for reg in RegNames:
            if reg not in ['pc','flag']:
                self.register_table[reg] = Register( 0 )
            else:
                raise SetMachineRegisterError("pc,flag is base reg ,but you set {}".format(reg))
        
    def putControllerSeq(self,*seq):
        seq = list(seq)
        self.controller_seq = seq
        self.controller_len = len(seq)
    def putOps(self,ops):
        self.other_op_table.update(ops)
    def getNowController(self):
        return self.controller_seq[self.pc.get()]
    # scanf 三趟扫描法
    # 第一趟标签表 和 基础pef规范 参数规范
    # 第二趟 执行 程序
    # scan and Run ------------------------
    def scanLabel(self):
        for i in self.controller_seq:
            length = len(i)
            if length == 1:
                temp = int(self.controller_seq.index(i))
                self.labels[i[0]] = temp
            elif length > 1 :
                self.scanPerfor(i)

    def scanPerfor(self,AST):
        name,rest = AST[0],AST[1:]
        print "scanPerfor:",name,rest
        assert name in self.perCount.keys()
        count = len(rest)
        temp  = self.perCount.get(name)
        assert count == temp
        if name == 'assgin':
            arg1,arg2 = rest[0],rest[1:]
            assert isinstance(arg1,str)
            assert arg1 in self.register_table.keys()
            assert isinstance(arg2,list)
            arg2 = self.scanBaseOp(*arg2)
        if name == 'test':
            arg1,_ = rest[0],rest[1:]
            assert isinstance(arg1,list) and _ == [ ]
            assert arg1[0] == 'op'
            arg1   = self.scanBaseOp(arg1)
            
        if name == 'branch':
            arg1,_ = rest[0],rest[1:]
            assert isinstance(arg1,list) and _ == [ ]
            assert arg1[0] == 'label'
            arg1   = self.scanBaseOp(arg1)
            
        if name == 'goto':
            arg1,_ = rest[0],rest[1:]
            assert isinstance(arg1,list) and _ == [ ]
            arg1   = self.scanBaseOp(arg1)
            assert arg1[0] in ['reg','label']
        if name == 'save':
            arg1,_ = rest[0],rest[1:]
            assert isinstance(arg1,str) and _ == [ ]
            #arg1   = self.scanBaseOp(arg1)
            
        if name == 'restore':
            arg1,_ = rest[0],rest[1:]
            assert isinstance(arg1,str) and _ == [ ]
            #arg1   = self.scanBaseOp(arg1)

        if name == 'perform':
            arg1,_ = rest[0],rest[1:]
            assert isinstance(arg1,list) and _ == [ ]
            assert arg1[0] == 'op'
            arg1   = self.scanBaseOp(arg1)
            
    def scanBaseOp(self,AST):
        env = {
            'reg':1,
            'const':1,
            'label':1,
            'op':None
        }
        name,rest = AST[0],AST[1:]
        print "scanBaseOp:",name
        assert name in env.keys()
        if name == 'op':
            arg1,arg2 = rest[0],rest[1:]
            assert arg1 in self.other_op_table
            return AST
        else:
            assert env[name] == len(rest)
            return AST
            
    def run(self,seq):
        print "run:",seq
        # len(seq) == 1 there is label pass it 
        if len(seq) > 1:
            name,rest = seq[0],seq[1:]
            print "run:",seq
            self.perEnv[name](*rest)
        
    def excute(self):
        self.scanLabel()
        print"excute:",self.labels
        while self.pc.get() <self.controller_len:
            seq = self.controller_seq[self.pc.get()]
            print "excute_:",self.pc.get(),type(self.pc.get())
            self.run(seq)
            tmp  = self.pc.get()
            temp = tmp + 1
            self.pc.set( temp )

    # perFunc -----------------------
    def assgin(self,reg_name,arg2):
        fn_name,arg = arg2[0],arg2[1:]
        func   = self.base_op_table[fn_name]
        print "assgin:",reg_name,fn_name,arg,func
        if fn_name == 'op':
            arg1,arg2 = arg[0],arg[1:]
            value = func(arg1,arg2)
        else:
            value  = func(*arg)
        #print "assgin:",value,type(value)
        #temp = Point()
        #temp.pSet(value)
        print "assgin:",value,type(value)
        self.register_table.get(reg_name).set(value)
        
    def perform(self,args):
        fn_name,arg = args[0],args[1:]
        func   = self.base_op_table[fn_name]
        #value  = func(*arg)
        arg1,arg2 = arg[0],arg[1:]
        value     = func(arg1,arg2)
        print "perform:",fn_name,arg,value
        #temp = Point()
        #temp.pSet(value)
        #return value#temp
    def test(self,args):
        # (test (op <op-name> <input1> ... <inputn>) )
        name,arg = args[0],args[1:]
        arg1,arg2 = arg[0],arg[1:]
        func  = self.base_op_table[name]
        value = func(arg1,arg2)
        print "test:",name,arg,value
        self.flag.set(value)
    def branch(self,args):
        if self.flag.get():
            fn_name,arg = args[0],args[1:]
            func        = self.base_op_table[fn_name]
            value       = func(*arg)
            print 'branch:',value,self.flag.get()
            self.pc.set(value)
    def goto(self,args):
        # 这里 解析 名字 和参数 以及返回值的过程 可以抽象出来        
        fn_name,arg = args[0],args[1:]
        func        = self.base_op_table[fn_name]
        value       = func(*arg)
        print "goto:",value
        self.pc.set(value)
    def save(self,args):
        #reg_name,arg = args[0],args[1:]
        #value = self.register_table[reg_name].get()
        #print "save:",reg_name,arg,value
        #self.stack.push(value)
        pass
    def initStack(self):
        pass
    def restore(self,args):
        #reg_name,arg = args[0],args[1:]
        #value = self.stack.pop()
        #print "restore:",reg_name,arg,value
        #self.register_table[reg_name].set(value)
        pass
    # perFunc end.
    def __repr__(self):
        #temp = "< {}\n{}\n{}\n >".format(self.register_table,self.labels,self.stack)
        return "< Machine >"#temp
    def __init__(self):
        self.register_table = {
            'pc':self.pc,
            'flag':self.flag,
        }
        self.controller_seq = list([ ])
        self.controller_len = int(0)
        self.labels = {}
        self.stack = ()#Stack()
        self.perCount = {
            'assgin'  : 2,
            'perform' : 1,
            'test'    : 1,
            'branch'  : 1,
            'goto'    : 1,
            'save'    : 1,
            'restore' : 1,
        }
        self.perEnv = {
            'assgin' : self.assgin,
            'test'   : self.test,
            'perform': self.perform,
            'branch' : self.branch,
            'goto'   : self.goto,
            'save'   : self.save,
            'restore': self.restore, 
        }
        self.base_op_table  = {
            'reg'   :self.reg,
            'const' :self.const,
            'label' :self.label,
            'op'    :self.op,
        }
        self.other_op_table = {
            '<'     : self.lt,
            '-'     : self.sub,
            '+'     : self.add,
            '='     : self.eq,
            'read'  : self.read,
        }
    def lt(self,a,b):
        flag = a < b
        print "Lt:",a,b
        return flag
    def sub(self,a,b):
        flag = a - b
        print "Sub:",a,b
        return flag
    def add(self,a,b):
        flag = a + b
        print "ADD:",flag,a,b
        return flag
    def eq(self,a,b):
        flag = a == b
        print "Eq:",a,b,flag
        return flag
    def read(self):
        temp = int(raw_input("read>> "))
        return temp

    #def flip(self):
    #    """
    #    # flip is gc last op flip data memory 
    #    ['assgin','temp',['reg','the-cdrs']],
    #    ['assgin','the-cdrs',['reg','new-cdrs']],
    #    ['assgin','new-cdrs',['reg','temp']],
    #    ['assgin','temp',['reg','the-cars']],
    #    ['assgin','the-cars',['reg','new-cars']],
    #    ['assgin','new-cars',['reg','temp']],
    #    """
    #    self.assgin('temp',['reg','the-cdrs'])
    #    self.assgin('the-cdrs',['reg','new-cdrs'])
    #    self.assgin('new-cdrs',['reg','temp'])
    #    self.assgin('temp',['reg','the-cars'])
    #    self.assgin('the-cars',['reg','new-cars'])
    #    self.assgin('new-cars',['reg','temp'])

m = Machine()
m.setMachineReg('a','b','c','the-stack')

m.putControllerSeq(
    ['main'],
    ['assgin','a',['const','233']],
    ['test',['op','=',['const','233'],['reg','a']]],
)
show(m)
m.excute()
show(m)
