# cic3_interpolator class 
# Last modification by Marko Kosunen, marko.kosunen@aalto.fi, 15.11.2018 19:48
#Add TheSDK to path. Importing it first adds the rest of the modules
#Simple buffer template
from thesdk import *
from verilog import *

import numpy as np

class cic3_interpolator(verilog,thesdk):
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__
    def __init__(self,*arg): 
        self.proplist = [' '];    #properties that can be propagated from parent
        self.Rs_high = 160e6*8;          # sampling frequency
        self.Rs_low  = 4*20e6;          # sampling frequency
        self.derivscale = 1023
        self.derivshift = 0
        self.iptr_A = refptr();
        self.model='py';             #can be set externally, but is not propagated
        self._Z = refptr();
        if len(arg)>=1:
            parent=arg[0]
            self.copy_propval(parent,self.proplist)
            self.parent =parent;
        self.init()

    def init(self):
        self.def_verilog()
        self._vlogparameters=dict([ ('g_rs',self.Rs_high), ('g_Rs_slow',self.Rs_low), ('g_integscale',self.derivscale) ])
        
    def run(self,*arg):
        if len(arg)>0:
            self.par=True      #flag for parallel processing
            queue=arg[0]  #multiprocessing.Queue as the first argument
        else:
            self.par=False

        if self.model=='py':
            self.main()
        else: 
          self.write_infile()
          self.run_verilog()
          self.read_outfile()

    def main(self):
        ratio=int(self.Rs_high/self.Rs_low)
         
        #Aah functional :) 
        # Caution! Without the three zeros before the diff, the discarded samples will cause an
        # error that will accumulate in the integrators, ans screw your output signal
        # Took me too long to figure this out. Feel stupid. Do not repeat. 
        s1=reduce(lambda signal, func: func(signal), 
                    [ lambda s: np.diff(s,axis=0).reshape(-1,1) for i in range(3) ], 
                     np.r_['0,2', 0, 0, 0, self.iptr_A.Value.reshape(-1,1)]).reshape(-1,1)*self.derivscale*2**self.derivshift
        interpolated=np.zeros((ratio*s1.shape[0],1),dtype=complex)
        for i in range(ratio):
            interpolated[i::ratio,0]=s1.reshape(-1,1)[:,0]
   
             
        out=reduce(lambda signal, func: func(signal), 
                    [ lambda s: np.cumsum(s,axis=0).reshape(-1,1) for i in range(3) ]
                    , interpolated.reshape(-1,1) ).reshape(-1,1)
        if self.par:
            queue.put(out)
        self._Z.Value=out

if __name__=="__main__":
    import matplotlib.pyplot as plt
    from  cic3_interpolator import *
    t=thesdk()
    t.print_log({'type':'I', 'msg': "This is a testing template. Enjoy"})
