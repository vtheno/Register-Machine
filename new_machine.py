#coding=utf-8
# todo : 5.3 表结构存储器
def show(machine):
    print '--------------------start'
    for i,v in zip(machine.register_table.keys(),machine.register_table.values()):
        print '<',i,':',v,'>'
    print machine.labels
    print machine.stack
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

class Register(object):
    def __init__(self,value):
        self.value = value
    def get(self):
        return self.value
    def set(self,value):
        # 5.3 的时候这里会修改成 支持 vector 和 int
        # 其实这里修改成支持指针的操作会比较好 
        # class ptr(object) 
        class RegisterSetError(Error): pass
        #self.value = checkWapper(value,int,RegisterSetError)
        #if isinstance(value,Point):
        #    self.value = value.pGet()
        #else:
        self.value = value
    def __repr__(self):
        return "< Register {} >".format(self.value)
    
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
    
class Machine(object):
    pc             = Register( 0 )
    flag           = Register( 0 )
    # memory 
    
    # disk         = Disk()
    # base op start
    def reg(self,name):
        class MachineRegError(Error):pass
        checkWapper(name,str,MachineRegError)
        if name not in self.register_table.keys():
            raise MachineRegError("{} not in reg table".format(name))
        return self.register_table.get(name).get()
        
    def const(self,constant_value):
        class MachineConstError(Error):pass
        checkWapper(constant_value,str,MachineConstError)
        if constant_value.isdigit():
            return Point( int(constant_value) )
        else:
            if constant_value == '()':
                # nil 
                return 
            if constant_value == 'Bh':
                # broken_heart 
                return 
            
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
                self.register_table[reg] = Register()
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
            'vector-ref':self.vector_ref,
            'vector-set':self.vector_set,
            'cons'      :self.cons,
            'pair?'     :self.isPair,
            'broken-heart?':self.isBroken_heart,
            'flip'         :self.flip,
            'gc'           :self.gc,
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

    def flip(self):
        """
        # flip is gc last op flip data memory 
        ['assgin','temp',['reg','the-cdrs']],
        ['assgin','the-cdrs',['reg','new-cdrs']],
        ['assgin','new-cdrs',['reg','temp']],
        ['assgin','temp',['reg','the-cars']],
        ['assgin','the-cars',['reg','new-cars']],
        ['assgin','new-cars',['reg','temp']],
        """
        self.assgin('temp',['reg','the-cdrs'])
        self.assgin('the-cdrs',['reg','new-cdrs'])
        self.assgin('new-cdrs',['reg','temp'])
        self.assgin('temp',['reg','the-cars'])
        self.assgin('the-cars',['reg','new-cars'])
        self.assgin('new-cars',['reg','temp'])

m = Machine()
m.setMachineReg('a','b','c','the-stack')

m.putControllerSeq(
#    ['main'],
#    ['assgin','a',['const','233']],
#    ['test',['op','=',['const','233'],['reg','a']]],
#    ['save','a'],
#    ['restore','b'],
#    ['goto',['label','done']],
#    #['branch',['label','main']],
#    ['done'],
#    )
# (set-car index value)
    ['assgin','the-stack',['const','()']],# init stack
    ['assgin','a',['const','233']],
    ['assgin','the-stack',['op','cons',['reg','a'],['reg','the-stack']]],#push
    ['assgin','the-stack',['op','cons',['reg','a'],['reg','the-stack']]],#push
    ['assgin','the-stack',['op','cons',['reg','a'],['reg','the-stack']]],#push
    ['assgin','the-stack',['op','cons',['reg','a'],['reg','the-stack']]],#push
    ['assgin','b',['op','vector-ref',['reg','the-cars'],['reg','the-stack']]],# pop
    ['assgin','the-stack',['op','vector-ref',['reg','the-cdrs'],['reg','the-stack']]],# pop 
    ['assgin','the-stack',['op','cons',['reg','a'],['reg','the-stack']]],#push
    #['perform',['op','pair?',['reg','the-stack']]],
    #['perform',['op','broken-heart?',['reg','the-stack']]],
    
    # gc-loop gc-flip then perform flip
    # flip
    #['gc-flip'],
    #['perform',['op','flip']],
    # --- 
    #['perform',['op','cons',['reg','a'],['reg','the-stack']]], / cons 的时候记得设置 e0 
    # ( n233 . p0 ) p0 -> (n233 . e0 ) start
    
    # stack over 
    # test start 
    #['assgin','b',['const','234']],
    #['assgin','c',['const','1']],
    #['perform',['op','-',['reg','b'],['reg','c']]],
    #['assgin','a',['op','vector-ref',['reg','the-cars'],['reg','c']]],
    #['perform',['op','vector-set',['reg','the-cars'],['reg','c'],['reg','b']]],
    # set-car! 
    #['assgin','a',['op','cons',['reg','b'],['reg','c']]],
    
    # test over 
    
    #['perform',['op','set-car',['reg','b'],['reg','c']]],# (set-car! <index> <value>)
    #['perform',['op','set-cdr',['reg','b'],['reg','c']]],# (set-cdr! <index> <value>)
    #    ['assgin','a',['const','95']],
    #    ['assgin','b',['const','10']],
    #['assgin','a',['op','read']],
    #['assgin','b',['op','read']],
    #['start'],
    #['test',['op','<',['reg','a'],['reg','b']]],
    #['branch',['label','done']],
    #['assgin','a',['op','-',['reg','a'],['reg','b']]],
    #['goto',['label','start']],
    #['done'],
    #['assgin','c',['reg','a']],
)
show(m)
m.excute()
show(m)
