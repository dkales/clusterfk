#!/usr/bin/env python2
from clusterfk import UI

# JSON: .json
# ------------------
# UI.ClusterFK(6, "./files/saved/deoxys384_table13.json", UI.CIPHER_TRAILS["DeoxysBC"])
# UI.ClusterFK(7, "./files/saved/deoxys384_table14.json", UI.CIPHER_TRAILS["DeoxysBC"])

# Trail: .trail
# ------------------
# UI.ClusterFK(4, "./files/input/deoxysbc256_table7.trail", UI.CIPHER_TRAILS["DeoxysBC"])
# UI.ClusterFK(7, "./files/input/deoxysbc384_table14.trail", UI.CIPHER_TRAILS["DeoxysBC"])


UI.ClusterFK(5, "./files/input/qarma5.trail", UI.CIPHER_TRAILS["Qarma"])
# UI.ClusterFK(5, "./files/input/mantis5R_34.trail", UI.CIPHER_TRAILS["Mantis"])
# UI.ClusterFK(5, "./files/input/mantis5R_36.trail", UI.CIPHER_TRAILS["Mantis"])
#UI.ClusterFK(6, "./files/input/mantis6R_48_2t.trail", UI.CIPHER_TRAILS["Mantis"])
# UI.ClusterFK(7, "./files/input/7r.trail", UI.CIPHER_TRAILS["Mantis"])


# deprecated .cfk
# ------------------
# UI.ClusterFK(5, "./files/saved/mantis5.cfk")
# UI.ClusterFK(5, "./files/saved/Mantis5__.cfk", UI.CIPHER_TRAILS["Mantis"])
# UI.ClusterFK(6, "./files/saved/mantis6_sharam.cfk", UI.CIPHER_TRAILS["Mantis"])
