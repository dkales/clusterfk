import Mantis

# external imports
import itertools

def intersect(cell1, cell2):
    return list(set(cell1) & set(cell2))

class PropagationStep:
    def __init__(self):
        pass

    def propagate(self):
        raise NotImplementedError("Subclasses need to implement this")


class PermutationStep(PropagationStep):
    def __init__(self, instate, outstate, perm):
        self.instate = instate
        self.outstate = outstate
        self.perm = perm

    def propagate(self):
        for i in range(16):
            if 'T' in self.instate.name:
                intersection = intersect(self.instate.atI(self.perm[i]), self.outstate.atI(i))
            else:
                intersection = self.instate.atI(self.perm[i]) & self.outstate.atI(i)
            if len(intersection) == 0:
                print "Error in:", self.instate.name
                assert False
            self.instate.setI(self.perm[i], intersection)
            self.outstate.setI(i, intersection)


class XORStep(PropagationStep):
    def __init__(self, instate, outstate, tweak):
        self.instate = instate
        self.outstate = outstate
        self.tweak = tweak

    def propagate(self):
        for i in range(16):
            t = self.tweak.atI(i)
            assert(len(t) == 1)
            t = t[0]
            in_new = {x^t for x in self.outstate.atI(i)}
            out_new = {x^t for x in self.instate.atI(i)}
            self.instate.setI(i, self.instate.atI(i) & in_new)
            self.outstate.setI(i, self.outstate.atI(i) & out_new)


class SBOXStep(PropagationStep):
    def __init__(self, instate, outstate, sbox):
        self.instate = instate
        self.outstate = outstate
        self.sbox = sbox
        self._initDDT(sbox)

    def _initDDT(self, sbox):
        size= len(sbox)
        ddt = [[0 for _ in range(size)] for _ in range(size)]
        for in1, in2 in itertools.product(range(size), repeat=2):
            out1, out2 = sbox[in1], sbox[in2]
            ddt[in1^in2][out1^out2] += 1
        self.ddt = ddt

    def _getDDTState(self, state):
        ret = set()
        for x in state:
            ret.update([i for i in range(16) if self.ddt[x][i] > 0])
        return ret

    def propagate(self):
        for i in range(16):
            outposs = self._getDDTState(self.instate.atI(i))
            inposs = self._getDDTState(self.outstate.atI(i))
            self.instate.setI(i, self.instate.atI(i) & inposs)
            self.outstate.setI(i, self.outstate.atI(i) & outposs)

class MixColStep(PropagationStep):
    def __init__(self, instate, outstate):
        self.instate = instate
        self.outstate = outstate

    def propagate(self):
        global cellcounter

        for col in range(4):
            incol = [self.instate.at(row, col) for row in range(4)]
            outcol = [self.outstate.at(row, col) for row in range(4)]
            # only branchnum = 4 atm
            # if "5" in self.instate.name:
                # print "<",col
                # print self.instate
                # print self.outstate
                # print incol
                # print outcol
                # print incol.count([0]) + outcol.count([0])

            # skip undefined blocks for now, will probably be resolved on their own
            if incol.count([0]) + outcol.count([0]) == 8:
                continue

            if incol.count([0]) + outcol.count([0]) == 4 and False:
                states = {x for x in incol+outcol if x != [0]}
                newstate = ((states[0] & states[1]) & states[2]) & states[3]
                # print newstate

                inidx = [i for i in range(4) if incol[i] != [0]]
                outidx = [i for i in range(4) if outcol[i] != [0]]
                
                for row in inidx:
                    self.instate.set(row, col, newstate)
                for row in outidx:
                    self.outstate.set(row, col, newstate)


            else:
                #print "WARNING MC not 4, but", 8-(incol.count([0]) + outcol.count([0])),": "+ self.instate.name + "," + self.outstate.name
               
                incol_old = set()
                outcol_old = set()
                incol_new = set()
                outcol_new = set()
                for a,b,c,d in itertools.product(incol[0], incol[1], incol[2], incol[3]):
                    incol_old.add((a,b,c,d))
                    outcol_new.add((b^c^d, a^c^d, a^b^d, a^b^c))
                for a,b,c,d in itertools.product(outcol[0], outcol[1], outcol[2], outcol[3]):
                    outcol_old.add((a,b,c,d))
                    incol_new.add((b^c^d, a^c^d, a^b^d, a^b^c))

                newinstate = incol_old & incol_new
                newoutstate = outcol_old & outcol_new
                for row in range(4):
                    ni = set()
                    no = set()
                    for x in newinstate:
                        ni.add(x[row])
                    for x in newoutstate:
                        no.add(x[row])
                    self.instate.set(row, col, ni)
                    self.outstate.set(row, col, no)




