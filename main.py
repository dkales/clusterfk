#!/usr/bin/env python2
from clusterfk import UI
from clusterfk import Qarma, Mantis

CIPHERS = {
    "Mantis": Mantis.MantisTrail,
    "Qarma": Qarma.QarmaTrail
}

#UI.ClusterFK(5, "./files/saved/mantis5.cfk")
#UI.ClusterFK(5, "./files/saved/Mantis5__.cfk", CIPHERS["Mantis"])


#UI.ClusterFK(5, "./files/input/qarma5.trail", CIPHERS["Qarma"])
#UI.ClusterFK(5, "./files/input/mantis5R_34.trail", CIPHERS["Mantis"])
#UI.ClusterFK(5, "./files/input/mantis5R_36.trail", CIPHERS["Mantis"])
#UI.ClusterFK(6, "./files/input/mantis6R_48_2t.trail", CIPHERS["Mantis"])
#UI.ClusterFK(7, "./files/input/7r.trail", CIPHERS["Mantis"])

#UI.ClusterFK(6, "./files/saved/mantis6_slow_drawing.cfk", CIPHERS["Mantis"]) # not correct
#UI.ClusterFK(6, "./files/saved/mantis6_slow_drawing_fixed.cfk", CIPHERS["Mantis"])
UI.ClusterFK(6, "./files/saved/mantis6_slow_drawing_with_green_inner.cfk", CIPHERS["Mantis"])