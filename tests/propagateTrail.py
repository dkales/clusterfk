from context import Mantis

trail = Mantis.MantisTrail(5, "./mantis5R_34.trail")
trail.makeActiveOnly()

trail.propagate()

trail.printTrail()
