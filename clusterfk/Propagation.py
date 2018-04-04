import Mantis
#internal imports
import Utils

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
    def __init__(self, statesize, instate, outstate, perm):
        self.statesize = statesize
        self.instate = instate
        self.outstate = outstate
        self.perm = perm

    def propagate(self):
        for i in range(self.statesize):
            intersection = self.instate.atI(self.perm[i]) & self.outstate.atI(i)
            if len(intersection) == 0:
                print "Error in: ", self.instate.name
                assert False

            self.instate.setI(self.perm[i], intersection)
            self.outstate.setI(i, intersection)


class UpdateTweakeyStepQarma(PropagationStep):
    def __init__(self, statesize, instate, outstate, perm, lfsrcomputationmatrix, lfsrlookup):
        self.statesize = statesize
        self.instate = instate
        self.outstate = outstate
        self.perm = perm
        self.lfsrlookup = lfsrlookup
        self.lfsrmatrix = lfsrcomputationmatrix
        self._initLFSRLookupInv(lfsrlookup)

    def _initLFSRLookupInv(self, lookup):
        self.lfsrlookupinv = [lookup.index(x) for x in range(self.statesize)]

    def propagate(self):
        for i in range(self.statesize):
            if self.lfsrmatrix[i] is 1:
                instate_i_shifted = set(map(lambda x: self.lfsrlookup[x], list(self.instate.atI(self.perm[i]))))
                intersection = instate_i_shifted & self.outstate.atI(i)
                self.instate.setI(self.perm[i], set(map(lambda x: self.lfsrlookupinv[x], intersection)))
            else:
                intersection = self.instate.atI(self.perm[i]) & self.outstate.atI(i)
                self.instate.setI(self.perm[i], intersection)

            if len(intersection) == 0:
                print "Error in: ", self.instate.name
                assert False

            self.outstate.setI(i, intersection)


class XORStep(PropagationStep):
    def __init__(self, statesize, instate, outstate, tweak):
        self.statesize = statesize
        self.instate = instate
        self.outstate = outstate
        self.tweak = tweak

    def propagate(self):
        for i in range(self.statesize):
            t = self.tweak.atI(i)
            assert(len(t) == 1)
            t = Utils.first(t)
            in_new = {x^t for x in self.outstate.atI(i)}
            out_new = {x^t for x in self.instate.atI(i)}

            self.instate.setI(i, self.instate.atI(i) & in_new)
            self.outstate.setI(i, self.outstate.atI(i) & out_new)

            if len(self.instate.atI(i)) == 0 or len(self.outstate.atI(i)) == 0:
                print "Error in: ", self.instate.name
                assert False


class SBOXStep(PropagationStep):
    def __init__(self, statesize, instate, outstate, sbox):
        self.statesize = statesize
        self.instate = instate
        self.outstate = outstate
        self.sbox = sbox
        self._initDDT(sbox)

    def _initDDT(self, sbox):
        size = len(sbox)
        assert(self.statesize == size)
        ddt = [[0 for _ in range(size)] for _ in range(size)]
        for in1, in2 in itertools.product(range(size), repeat=2):
            out1, out2 = sbox[in1], sbox[in2]
            ddt[in1^in2][out1^out2] += 1
        self.ddt = ddt

    def _getDDTState(self, state):
        ret = set()
        for x in state:
            ret.update([i for i in range(self.statesize) if self.ddt[x][i] > 0])
        return ret

    def propagate(self):
        for i in range(self.statesize):
            outposs = self._getDDTState(self.instate.atI(i))
            inposs = self._getDDTState(self.outstate.atI(i))

            self.instate.setI(i, self.instate.atI(i) & inposs)
            self.outstate.setI(i, self.outstate.atI(i) & outposs)

            if len(self.instate.atI(i)) == 0 or len(self.outstate.atI(i)) == 0:
                print "Error in: ", self.instate.name
                assert False


class MixColStepMantis(PropagationStep):
    def __init__(self, staterow, statecol, instate, outstate):
        self.staterow = staterow
        self.statecol = statecol
        self.instate = instate
        self.outstate = outstate

    def propagate(self):
        global cellcounter

        for col in range(self.statecol):
            incol = [self.instate.at(row, col) for row in range(self.staterow)]
            outcol = [self.outstate.at(row, col) for row in range(self.staterow)]

            # skip undefined blocks for now, will probably be resolved on their own
            if incol.count({0}) + outcol.count({0}) == 8:
                continue

            else:
                #print "WARNING MC not 4, but", 8-(incol.count([0]) + outcol.count([0])),": "+ self.instate.name + "," + self.outstate.name
               
                incol_old = set()
                outcol_old = set()
                incol_new = set()
                outcol_new = set()

                for a, b, c, d in itertools.product(incol[0], incol[1], incol[2], incol[3]):
                    incol_old.add((a,b,c,d))
                    outcol_new.add((b^c^d, a^c^d, a^b^d, a^b^c))
                for a, b, c, d in itertools.product(outcol[0], outcol[1], outcol[2], outcol[3]):
                    outcol_old.add((a,b,c,d))
                    incol_new.add((b^c^d, a^c^d, a^b^d, a^b^c))

                newinstate = incol_old & incol_new
                newoutstate = outcol_old & outcol_new
                for row in range(self.staterow):
                    ni = set()
                    no = set()
                    for x in newinstate:
                        ni.add(x[row])
                    for x in newoutstate:
                        no.add(x[row])
                    self.instate.set(row, col, ni)
                    self.outstate.set(row, col, no)


class MixColStepQarma(PropagationStep):
    def __init__(self, staterow, statecol, instate, outstate, m):
        self.staterow = staterow
        self.statecol = statecol
        self.instate = instate
        self.outstate = outstate
        self.m = m

    def propagate(self):
        for col in range(self.statecol):
            incol = [self.instate.at(row, col) for row in range(self.staterow)]
            outcol = [self.outstate.at(row, col) for row in range(self.staterow)]

            # skip undefined blocks for now, will probably be resolved on their own
            if incol.count({0}) + outcol.count({0}) == 8:
                continue

            else:
                incol_old = set()
                outcol_old = set()
                incol_new = set()
                outcol_new = set()

                for a,b,c,d in itertools.product(incol[0], incol[1], incol[2], incol[3]):
                    incol_old.add((a,b,c,d))
                    outcol_new.add((Utils.rotl(b, self.m[0][1]) ^ Utils.rotl(c, self.m[0][2]) ^ Utils.rotl(d, self.m[0][3]),
                                    Utils.rotl(a, self.m[1][0]) ^ Utils.rotl(c, self.m[1][2]) ^ Utils.rotl(d, self.m[1][3]),
                                    Utils.rotl(a, self.m[2][0]) ^ Utils.rotl(b, self.m[2][1]) ^ Utils.rotl(d, self.m[2][3]),
                                    Utils.rotl(a, self.m[3][0]) ^ Utils.rotl(b, self.m[3][1]) ^ Utils.rotl(c, self.m[3][2])))

                for a,b,c,d in itertools.product(outcol[0], outcol[1], outcol[2], outcol[3]):
                    outcol_old.add((a,b,c,d))
                    incol_new.add((Utils.rotl(b, self.m[0][1]) ^ Utils.rotl(c, self.m[0][2]) ^ Utils.rotl(d, self.m[0][3]),
                                   Utils.rotl(a, self.m[1][0]) ^ Utils.rotl(c, self.m[1][2]) ^ Utils.rotl(d, self.m[1][3]),
                                   Utils.rotl(a, self.m[2][0]) ^ Utils.rotl(b, self.m[2][1]) ^ Utils.rotl(d, self.m[2][3]),
                                   Utils.rotl(a, self.m[3][0]) ^ Utils.rotl(b, self.m[3][1]) ^ Utils.rotl(c, self.m[3][2])))

                newinstate = incol_old & incol_new
                newoutstate = outcol_old & outcol_new
                for row in range(self.staterow):
                    ni = set()
                    no = set()
                    for x in newinstate:
                        ni.add(x[row])
                    for x in newoutstate:
                        no.add(x[row])
                    self.instate.set(row, col, ni)
                    self.outstate.set(row, col, no)

                    if len(self.instate.at(row, col)) == 0 or len(self.outstate.at(row, col)) == 0:
                        print "Error in: ", self.instate.name
                        assert False


