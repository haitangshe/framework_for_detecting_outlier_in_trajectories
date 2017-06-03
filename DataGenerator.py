'''
Created on Nov 30, 2016

@author: zahran
'''
import pandas as pd
import numpy as np
import random

class DataGenerator(object):    
    def __init__(self, MODEL_PATH, DATA_GEN, perUserSequences):
        self.MODEL_PATH = MODEL_PATH
        self.DATA_GEN = DATA_GEN
        self.perUserSequences = perUserSequences        
        store = pd.HDFStore(MODEL_PATH)         
                        
        self.Theta_zh = store['Theta_zh'].values
        self.Psi_oz = store['Psi_sz'].values    
        self.true_mem_size = store['Dts'].values.shape[1]    
        self.hyper2id = dict(store['hyper2id'].values)
        self.obj2id = dict(store['source2id'].values)
        print len(self.hyper2id), len(self.obj2id)
        
        self.id2obj = dict((v, k) for k, v in self.obj2id.items())
        
        self.nz, self.nh = self.Theta_zh.shape
        self.no, self.nz = self.Psi_oz.shape  
              
        #normalizing 
        #axis 0 is summing the cols. i.e. normalizing by the col sum. (i.e for each env)
        self.Psi_oz = self.Psi_oz / self.Psi_oz.sum(axis=0)
        self.Theta_zh = self.Theta_zh / self.Theta_zh.sum(axis=0)
        
        #for optimization, save the transitions for each environment
        self.envTransitions = {}
                    
        
        store.close()
    
    def getTransitionMatrixForEnv(self, z):                                    
        #Compute transitions for a given env  
        if(z in self.envTransitions):
            return self.envTransitions[z]            
        T = np.outer(self.Psi_oz[:, z], self.Psi_oz[:, z]) #the P[ dest | source, z ] matrix
        np.fill_diagonal(T, 0)
        T = T / T.sum(axis=0) #Re-normalize
        self.envTransitions[z] = T
        return T #(o x o)
    
    def sample(self, srcs, probs):
        #numpy.random.choice(a, size=None, replace=True, p=None)
        #replace =True. i.e. put back the sampled item to the space
        #replace =False. i.e. once picked, it's removed and thus affecting the probability of the remainging items
        mySample = np.random.choice(srcs, 1, replace =True, p=probs)
        return mySample
    
    def generateOneSequence(self, T, starto):
        seq = [starto]
        currento = starto
        for i in range(self.true_mem_size):
            currento_o = T[:,currento]
            sampledo = self.sample(list(range(0,self.no)), currento_o)[0]
            seq.append(sampledo)
            currento = sampledo
        return seq
    
    def generateOneSequence_optimized(self, z, starto):
        seq = [starto]
        currento = starto
        for i in range(self.true_mem_size):
            currento_o = np.array(self.Psi_oz[:, z])
            currento_o *= currento_o[currento]
            currento_o = currento_o / currento_o.sum() #Re-normalize
            #currento_o = T[:,currento]
            sampledo = self.sample(list(range(0,self.no)), currento_o)[0]
            seq.append(sampledo)
            currento = sampledo
        return seq
                            
    
    def generateSequenceByUser_optimized(self, h):                        
        h_z = self.Theta_zh[:,h]
        sampledZ = self.sample(list(range(0,self.nz)), h_z)[0]
        
        z_o = self.Psi_oz[:,sampledZ]

        firsto = self.sample(list(range(0,self.no)), z_o)[0]
        
        #T = self.getTransitionMatrixForEnv(sampledZ)  
        
        seqIds = self.generateOneSequence_optimized(sampledZ, firsto)
        seq = []
        for s in seqIds:
            seq.append(self.id2obj[s])
            
        return seq
    
    def generateSequenceByUser(self, h):                        
        h_z = self.Theta_zh[:,h]
        sampledZ = self.sample(list(range(0,self.nz)), h_z)[0]
        
        z_o = self.Psi_oz[:,sampledZ]

        firsto = self.sample(list(range(0,self.no)), z_o)[0]
        
        T = self.getTransitionMatrixForEnv(sampledZ)  
        
        seqIds = self.generateOneSequence(T, firsto)
        seq = []
        for s in seqIds:
            seq.append(self.id2obj[s])
            
        return seq
            
        
               
        
    def generate(self):                    
        w = open(self.DATA_GEN, 'w')
        cnt = 0
        for userName in self.hyper2id:
            if(cnt % 10 == 0):
                print(str(cnt)+' users are finished ...')
            cnt+=1
            h = self.hyper2id[userName]
            
            for i in range(self.perUserSequences):
                w.write(str(userName)+'\t')
                seq = self.generateSequenceByUser(h)                
                for s in seq:
                    w.write(s + '\t')
                for g in range(self.true_mem_size+1):
                    w.write('false\t')
                w.write('\n')               
                w.flush()
        w.close()
        
    
    def generate_optimized(self):
        w = open(self.DATA_GEN, 'w')
        cnt = 0
        print '#users', len(self.hyper2id)
        for userName in self.hyper2id:
            #if(cnt % 10 == 0):
            print(str(cnt)+' users are finished ...')
            cnt+=1
            h = self.hyper2id[userName]
            
            for i in range(self.perUserSequences):
                #print userName, i
                w.write(str(userName)+'\t')
                seq = self.generateSequenceByUser_optimized(h)                
                for s in seq:
                    w.write(s + '\t')
                for g in range(self.true_mem_size+1):
                    w.write('false\t')
                w.write('\n')               
                w.flush()
        w.close()
                
            
        
    
        







def main():
    MODEL_PATH = '/scratch/snyder/m/mohame11/lastFm/lastfm_win10_noob.h5'
    #MODEL_PATH = '/Users/mohame11/Documents/myFiles/Career/Work/New_Linux/PARSED_pins_repins_win10_noop_NoLeaveOut_pinterest.h5'
    DATA_GEN = '/scratch/snyder/m/mohame11/lastFm/simulatedData/tmp'
    perUserSequences = 20
       
    dg = DataGenerator(MODEL_PATH, DATA_GEN, perUserSequences)
    #dg.generate()
    dg.generate_optimized()
  
    

if __name__ == "__main__":
    
#     d = {'a':0.0, 'b':0.0, 'c':0.0, 'd':0.0}
#     srcs = d.keys()    
#     probs = [0.6, 0.2, 0.15, 0.05]
#     tot = 10000
#     for i in range(tot):
#         mySample = np.random.choice(srcs, 1, replace =True, p=probs)[0]
#         d[mySample] += 1
#     for k in srcs:
#         print(k,d[k]/tot)
        
        
    main()       
    print('DONE!')
