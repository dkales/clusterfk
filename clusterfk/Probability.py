import itertools
import math
import operator

def prod(factors):
    return reduce(operator.mul, factors, 1)

class ProbabilityStep:
    def __init__(self):
        pass

    def getProbability(self,verbose=False):
        raise NotImplementedError("Subclasses need to implement this")

class FullroundStep(ProbabilityStep):
    def __init__(self, round, sboxstate, addstate, tweak, permstate, mixcolstate, sboxstate2, sbox, P):
        self.round = round
        self.sboxstate = sboxstate
        self.sboxstate2 = sboxstate2
        self.tweak = tweak
        self.addstate = addstate
        self.permstate = permstate
        self.mixcolstate = mixcolstate
        self.sbox = sbox
        self.P = P
        self._initDDT(sbox)

    def _initDDT(self, sbox):
        size= len(sbox)
        ddt = [[0 for _ in range(size)] for _ in range(size)]
        for in1, in2 in itertools.product(range(size), repeat=2):
            out1, out2 = sbox[in1], sbox[in2]
            ddt[in1^in2][out1^out2] += 1
        self.ddt = ddt

    def getProbability(self,verbose=False):
        # permuation of columns after P step
        # cols = ((0,10,5,15),(11,1,14,4),(6,12,3,9),(13,7,8,2))
        overall_prob = 1.0
        
        # samedict = {}
        # for i in range(16):
            # if self.sboxstate.statenumbers[i] not in samedict:
                # samedict[self.sboxstate.statenumbers[i]] = []
            # samedict[self.sboxstate.statenumbers[i]].append(i)

        for column, probs in self.sboxstate.columnprobs.items():
            # if number == 0 or len(group) == 1:
                # for i in group:
                    # sboxprob = 0.0
                    # for x in self.sboxstate.atI(i):
                        # sboxprob += self.sboxstate.stateprobs[i][x] * float(sum([self.ddt[x][y] for y in self.addstate.atI(i)])) / sum(self.ddt[x])
                        # for y in self.addstate.atI(i):
                            # self.addstate.stateprobs[i][y] += \
                                    # self.sboxstate.stateprobs[i][x] * float(self.ddt[x][y]) / sum(self.ddt[x])
                    # # if verbose:
                        # # print "SBOX", i, sboxprob
                    # overall_prob *= sboxprob

            sboxprob = 0.0
            for values, prob in probs.items():
                part = prob
                for idx,x in enumerate(values):
                    j = column[idx]
                    part *= float(sum([self.ddt[x][y] for y in self.addstate.atI(j)])) / sum(self.ddt[x])
                    for y in self.addstate.atI(j):
                        self.addstate.stateprobs[j][y] += prob * float(self.ddt[x][y]) / sum(self.ddt[x])
                sboxprob += part

            # if verbose:
                # print "SBOX", column, math.log(sboxprob,2)
            overall_prob *= sboxprob

        #normalize addstate
        for i in range(16):
            self.addstate.stateprobs[i] = [float(x)/sum(self.addstate.stateprobs[i]) for x in self.addstate.stateprobs[i]]


        sboxprob = overall_prob
        for i in range(16):
            if self.tweak.atI(i) !=[0]:
                assert len(self.tweak.atI(i)) == 1
                # outprobs[i] = [outprobs[i][x^self.tweak.atI(i)[0]] for x in range(16)]
                self.permstate.stateprobs[i] = [self.addstate.stateprobs[i][x^self.tweak.atI(i)[0]] for x in range(16)]
            else:
                self.permstate.stateprobs[i] = [self.addstate.stateprobs[i][x] for x in range(16)]

        # print "permstate.stateprobs"
        # print self.permstate.stateprobs
        # print "outprobs"
        # print outprobs
        # permute state probs
        for i in range(16):
            self.mixcolstate.stateprobs[i] = self.permstate.stateprobs[self.P[i]]


        self.sboxstate2.columnprobs = {}
        for col in range(4):
            # print "-"*40
            incol = [self.mixcolstate.at(row, col) for row in range(4)]
            outset = set()
            colprob = 0.0
            colprob_all = 0.0
            self.sboxstate2.columnprobs[(0+col,4+col,8+col,12+col)] = {}
            for a,b,c,d in itertools.product(self.sboxstate2.at(0, col), self.sboxstate2.at(1, col), self.sboxstate2.at(2, col), self.sboxstate2.at(3, col)):
                outset.add((a,b,c,d))
            for a,b,c,d in itertools.product(incol[0], incol[1], incol[2], incol[3]):
                prob = self.mixcolstate.stateprobs[0+col][a] * self.mixcolstate.stateprobs[4+col][b] * self.mixcolstate.stateprobs[8+col][c] * self.mixcolstate.stateprobs[12+col][d]    
                result = (b^c^d, a^c^d, a^b^d, a^b^c)
                if result in outset:
                    colprob += prob
                    self.sboxstate2.columnprobs[(0+col,4+col,8+col,12+col)][result] = prob
                colprob_all += prob
            
            # print col, colprob, colprob_all
            overall_prob *= colprob

        for col, probs in self.sboxstate2.columnprobs.items():
            total = sum(probs.values())
            for val, prob in probs.items():
                probs[val] = prob/total

            for val, prob in probs.items():
                self.sboxstate2.stateprobs[col[0]][val[0]] += prob
                self.sboxstate2.stateprobs[col[1]][val[1]] += prob
                self.sboxstate2.stateprobs[col[2]][val[2]] += prob
                self.sboxstate2.stateprobs[col[3]][val[3]] += prob

        for i in range(16):
            self.sboxstate2.stateprobs[i] = [float(x)/sum(self.sboxstate2.stateprobs[i]) for x in self.sboxstate2.stateprobs[i]]
            
        mixcolprob = overall_prob / sboxprob
        # print self.sboxstate.stateprobs
        # print "------"
        # print self.mixcolstate.stateprobs
        # print "------"
        # print self.sboxstate2.stateprobs

        if verbose:
            print self.sboxstate.name, overall_prob, math.log(overall_prob, 2)

        return (overall_prob, sboxprob, mixcolprob)

class MantisInnerRoundStep(ProbabilityStep):
    def __init__(self, sboxstatein, mixcolstatein, mixcolstateout, sboxstateout, sbox):
        self.sboxstatein = sboxstatein
        self.sboxstateout = sboxstateout
        self.mixcolstatein = mixcolstatein
        self.mixcolstateout = mixcolstateout
        self.sbox = sbox
        self._initDDT(sbox)

    def _initDDT(self, sbox):
        size= len(sbox)
        ddt = [[0 for _ in range(size)] for _ in range(size)]
        for in1, in2 in itertools.product(range(size), repeat=2):
            out1, out2 = sbox[in1], sbox[in2]
            ddt[in1^in2][out1^out2] += 1
        self.ddt = ddt

    def getProbability(self,verbose=False):
        overall_prob = 1.0

        # sbox forward round:
        for i in range(16):
            sboxprob = 0.0
            for x in self.sboxstatein.atI(i):
                sboxprob += self.sboxstatein.stateprobs[i][x] * float(sum([self.ddt[x][y] for y in self.mixcolstatein.atI(i)])) / sum(self.ddt[x])
                for y in self.mixcolstatein.atI(i):
                    self.mixcolstatein.stateprobs[i][y] += \
                            self.sboxstatein.stateprobs[i][x] * float(self.ddt[x][y]) / sum(self.ddt[x])
            overall_prob *= sboxprob


            self.mixcolstatein.stateprobs[i] = [float(x)/sum(self.mixcolstatein.stateprobs[i]) for x in self.mixcolstatein.stateprobs[i]]

        for col in range(4):
            columnin  = [set(self.sboxstatein.at(row, col)) for row in range(4)]
            columnout = [set(self.sboxstateout.at(row, col)) for row in range(4)]
            mcolumnin  = [set(self.mixcolstatein.at(row, col)) for row in range(4)]
            mcolumnout = [set(self.mixcolstateout.at(row, col)) for row in range(4)]
            if columnin.count(set([0x0])) == 4 and columnout.count(set([0x0])) == 4:
                continue
            
            if columnin.count(set([0xa])) == 2 and columnin.count(set([0x0])) == 2 and     columnout.count(set([0xa])) == 2 and columnout.count(set([0x0])) == 2:
                if mcolumnin.count(set([0xa])) == 2 and mcolumnin.count(set([0x0])) == 2 and     mcolumnout.count(set([0xa])) == 2 and mcolumnout.count(set([0x0])) == 2:
                    overall_prob *= 1.0 # overall 2**-8
                    continue
                elif mcolumnin.count(set([0xa,0x5,0xd,0xf])) == 2 and mcolumnin.count(set([0x0])) == 2 and     mcolumnout.count(set([0xa,0x5,0xd,0xf])) == 2 and mcolumnout.count(set([0x0])) == 2:
                    overall_prob *= 1.0 # overall 2**-4
                    continue
            
            raise NotImplementedError("Superbox case not specified")

        # temporary hack, assume uniform distribution in inner step
        for i in range(16):
            self.mixcolstateout.stateprobs[i] = [1.0/len(self.mixcolstateout.atI(i)) if x in self.mixcolstateout.atI(i) else 0.0 for x in range(16)]


        # sbox backward round
        for i in range(16):
            sboxprob = 0.0
            for x in self.mixcolstateout.atI(i):
                sboxprob += self.mixcolstateout.stateprobs[i][x] * float(sum([self.ddt[x][y] for y in self.sboxstateout.atI(i)])) / sum(self.ddt[x])
                for y in self.sboxstateout.atI(i):
                    self.sboxstateout.stateprobs[i][y] += \
                            self.mixcolstateout.stateprobs[i][x] * float(self.ddt[x][y]) / sum(self.ddt[x])
            overall_prob *= sboxprob


            self.sboxstateout.stateprobs[i] = [float(x)/sum(self.sboxstateout.stateprobs[i]) for x in self.sboxstateout.stateprobs[i]]


        if verbose:
            print "I", overall_prob, math.log(overall_prob,2)

        return (overall_prob, overall_prob, 1)


class FullroundInverseStep(ProbabilityStep):
    def __init__(self, round, sboxstate, mixcolstate, permstate, addstate, tweak, sboxstate2, sbox, P):
        self.round = round
        self.sboxstate = sboxstate
        self.sboxstate2 = sboxstate2
        self.tweak = tweak
        self.addstate = addstate
        self.permstate = permstate
        self.mixcolstate = mixcolstate
        self.sbox = sbox
        self.P = P
        self._initDDT(sbox)

    def _initDDT(self, sbox):
        size= len(sbox)
        ddt = [[0 for _ in range(size)] for _ in range(size)]
        for in1, in2 in itertools.product(range(size), repeat=2):
            out1, out2 = sbox[in1], sbox[in2]
            ddt[in1^in2][out1^out2] += 1
        self.ddt = ddt

    def getProbability(self, verbose=False):
        overall_prob = 1.0

        self.mixcolstate.columnprobs = {}
        for col in range(4):
            # print "-"*40
            incol = [self.sboxstate.at(row, col) for row in range(4)]
            outset = set()
            colprob = 0.0
            colprob_all = 0.0
            self.mixcolstate.columnprobs[(0+col,4+col,8+col,12+col)] = {}
            for a,b,c,d in itertools.product(self.mixcolstate.at(0, col), self.mixcolstate.at(1, col), self.mixcolstate.at(2, col), self.mixcolstate.at(3, col)):
                outset.add((a,b,c,d))
            for a,b,c,d in itertools.product(incol[0], incol[1], incol[2], incol[3]):
                prob = self.sboxstate.stateprobs[0+col][a] * self.sboxstate.stateprobs[4+col][b] * self.sboxstate.stateprobs[8+col][c] * self.sboxstate.stateprobs[12+col][d]    
                result = (b^c^d, a^c^d, a^b^d, a^b^c)
                if result in outset:
                    colprob += prob
                    self.mixcolstate.columnprobs[(0+col,4+col,8+col,12+col)][result] = prob
                colprob_all += prob
            
            # print col, colprob, colprob_all
            overall_prob *= colprob

        for col, probs in self.mixcolstate.columnprobs.items():
            total = sum(probs.values())
            for val, prob in probs.items():
                probs[val] = prob/total

            for val, prob in probs.items():
                self.mixcolstate.stateprobs[col[0]][val[0]] += prob
                self.mixcolstate.stateprobs[col[1]][val[1]] += prob
                self.mixcolstate.stateprobs[col[2]][val[2]] += prob
                self.mixcolstate.stateprobs[col[3]][val[3]] += prob

        mixcolprob = overall_prob
        # normalize probablities for mixcols
        for i in range(16):
            self.mixcolstate.stateprobs[i] = [float(x)/sum(self.mixcolstate.stateprobs[i]) for x in self.mixcolstate.stateprobs[i]]

        # propagate to perm with correct permutation of probabilites
        for i in range(16):
            self.permstate.stateprobs[self.P[i]] = list(self.mixcolstate.stateprobs[i])
        self.permstate.columnprobs = {}
        for col, probs in self.mixcolstate.columnprobs.items():
            self.permstate.columnprobs[(self.P[col[0]], self.P[col[1]], self.P[col[2]], self.P[col[3]])] = probs.copy()

        self.addstate.columnprobs = {}
        for i in range(16):
            if self.tweak.atI(i) !=[0]:
                assert len(self.tweak.atI(i)) == 1
                self.addstate.stateprobs[i] = [self.permstate.stateprobs[i][x^self.tweak.atI(i)[0]] for x in range(16)]
            else:
                self.addstate.stateprobs[i] = [self.permstate.stateprobs[i][x] for x in range(16)]
        for col, probs in self.permstate.columnprobs.items():
            self.addstate.columnprobs[col] = {}
            for values, prob in probs.items():
                self.addstate.columnprobs[col][(values[0]^self.tweak.atI(col[0])[0], values[1]^self.tweak.atI(col[1])[0], values[2]^self.tweak.atI(col[2])[0], values[3]^self.tweak.atI(col[3])[0])] = prob 


        for column, probs in self.addstate.columnprobs.items():
            sboxprob = 0.0
            for values, prob in probs.items():
                part = prob
                for idx,x in enumerate(values):
                    j = column[idx]
                    part *= float(sum([self.ddt[x][y] for y in self.sboxstate2.atI(j)])) / sum(self.ddt[x])
                    for y in self.sboxstate2.atI(j):
                        self.sboxstate2.stateprobs[j][y] += prob * float(self.ddt[x][y]) / sum(self.ddt[x])
                sboxprob += part

            # if verbose:
                # print "SBOX", column, math.log(sboxprob,2)
            overall_prob *= sboxprob


        # for i in range(16):
            # sboxprob = 0.0
            # for x in self.addstate.atI(i):
                # sboxprob += self.addstate.stateprobs[i][x] * float(sum([self.ddt[x][y] for y in self.sboxstate2.atI(i)])) / sum(self.ddt[x])
                # for y in self.sboxstate2.atI(i):
                    # self.sboxstate2.stateprobs[i][y] += \
                            # self.addstate.stateprobs[i][x] * float(self.ddt[x][y]) / sum(self.ddt[x])
            # overall_prob *= sboxprob

        # normalize sbox2 probs
        for i in range(16):
            self.sboxstate2.stateprobs[i] = [float(x)/sum(self.sboxstate2.stateprobs[i]) for x in self.sboxstate2.stateprobs[i]]


        sboxprob = overall_prob / mixcolprob
        if verbose:
            print self.sboxstate.name, overall_prob, math.log(overall_prob, 2)

        return (overall_prob, sboxprob, mixcolprob)


# class SBOXProbabilityStep(ProbabilityStep):
    # def __init__(self, instate, outstate, sbox):
        # self.instate = instate
        # self.outstate = outstate
        # self.sbox = sbox
        # self._initDDT(sbox)

    # def _initDDT(self, sbox):
        # size= len(sbox)
        # ddt = [[0 for _ in range(size)] for _ in range(size)]
        # for in1, in2 in itertools.product(range(size), repeat=2):
            # out1, out2 = sbox[in1], sbox[in2]
            # ddt[in1^in2][out1^out2] += 1
        # self.ddt = ddt

    # def getProbability(self):
        # overall_prob = 1.0
        # for i in range(16):
            # sboxprob = 0.0
            # for x in self.instate.atI(i):
                # sboxprob += float(sum([self.ddt[x][y] for y in self.outstate.atI(i)])) / sum(self.ddt[x])
            # sboxprob /= len(self.instate.atI(i))
            # overall_prob *= sboxprob

        # print self.instate.name, overall_prob, math.log(overall_prob, 2)
        # return overall_prob

