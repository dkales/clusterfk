from context import Mantis, Propagation


tweak = [[[0xa],[0],[0],[0]],
         [[0xa],[0],[0],[0]],
         [[0],[0],[0],[0]],
         [[0],[0],[0],[0]]]

emptystate = [[[0],[0],[0],[0]],
         [[0],[0],[0],[0]],
         [[0],[0],[0],[0]],
         [[0],[0],[0],[0]]]

T = Mantis.MantisState("T", tweak)

S = Mantis.MantisState("S", Mantis.getUndefinedState())
A = Mantis.MantisState("A", Mantis.getUndefinedState())
M = Mantis.MantisState("M", Mantis.getUndefinedState())
P = Mantis.MantisState("P", emptystate)
P2= Mantis.MantisState("P", Mantis.getUndefinedState())

props = []
props.append(Propagation.XORStep(P, A, T))
props.append(Propagation.SBOXStep(A, S, Mantis.SBOX))
props.append(Propagation.MixColStepMantis(S, M))
props.append(Propagation.PermutationStep(M, P2, inverse=True))

for prop in props:
    prop.propagate()

print P
print S
print A
print M
print P2
