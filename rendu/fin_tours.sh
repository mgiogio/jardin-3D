#!/bin/bash
# Chaîne complète Tours : photo ravivée -> produits 3D posés -> modèles entraînés -> ombres -> teinte -> aménagement -> mobilier -> ombres
set -e
python3 poser.py cas/tours-1_v.jpg fin/tours_calque_sm.png fin/tours_pose0.jpg '#978461' >/dev/null
python3 meubles_poser.py fin/tours_pose0.jpg fin/tours_cal_meubles.png fin/tours_pose.jpg >/dev/null
PROTEGE=fin/tours_cal_ter.png python3 affine.py fin/tours_pose.jpg fin/tours_cal_perg.png fin/tours_a.jpg "$(cat lora/weights_url2)" "CVGPRGA natural brown wooden freestanding pergola, slatted roof, grey metal connectors, square posts, real garden photo" 0.4 40 >/dev/null
PROTEGE=fin/tours_cal_perg.png python3 affine.py fin/tours_a.jpg fin/tours_cal_ter_np.png fin/tours_b.jpg "$(cat lora/weights_url_terrasse)" "a photo of a CVGTER pressure treated pine wooden deck terrace, boards with aligned joints and visible screws, under a wooden pergola, smartphone photo" 0.15 20 >/dev/null
python3 ombre_report.py fin/tours_b.jpg fin/tours_calque.png fin/tours_cal_ter.png fin/tours_c.jpg >/dev/null
python3 teinte.py fin/tours_c.jpg fin/tours_d.jpg teinte_ref.json soleil fin/tours_cal_perg.png,fin/tours_cal_ter_np.png 0.5 >/dev/null 2>&1
GARDER=cas/tours_garder2.json FONDU_ZONE=8 MOBILIER_SEPARE=1 HAUT_MOBILIER=0 python3 amenage.py fin/tours_d.jpg cas/tours_zone3.json 1 cas/tours_amenage.txt fin/tours_e.jpg fin/tours_calque.png fin/vide_tours.png fin/tours_cal_ter.png 0.0 >/dev/null 2>&1
cp fin/tours_e.jpg fin/tours_g.jpg   # mobilier : modèles 3D libres de droits (Poly Haven, CC0) posés dans la scène
echo fini fin/tours_g.jpg
