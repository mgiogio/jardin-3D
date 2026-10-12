#!/bin/bash
# Chaîne Tours pour une palette d'ambiance : bash fin_tours_pal.sh <palette>  -> fin/tp_<palette>_g.jpg
set -e; P=$1; O=fin/tp_${P}
python3 poser.py cas/tours-1_v.jpg fin/tours_calque_sm2.png ${O}_pose0.jpg '#978461' >/dev/null
cp ${O}_pose0.jpg ${O}_pose.jpg   # meubles posés après les retouches produits, sinon la passe terrasse les teinte
PROTEGE=fin/tours_cal_ter.png python3 affine.py ${O}_pose.jpg fin/tours_cal_perg.png ${O}_a.jpg "$(cat lora/weights_url2)" "CVGPRGA natural brown wooden freestanding pergola, slatted roof, grey metal connectors, square posts, real garden photo" 0.4 40 >/dev/null
PROTEGE=fin/tours_cal_perg.png python3 affine.py ${O}_a.jpg fin/tours_cal_ter_np.png ${O}_b.jpg "$(cat lora/weights_url_terrasse)" "a photo of a CVGTER pressure treated pine wooden deck terrace, boards with aligned joints and visible screws, under a wooden pergola, smartphone photo" 0.15 20 >/dev/null
python3 ombre_report.py ${O}_b.jpg fin/pal_${P}_calque.png fin/tours_cal_ter.png ${O}_c.jpg >/dev/null
python3 teinte.py ${O}_c.jpg ${O}_d0.jpg teinte_ref.json soleil fin/tours_cal_perg.png,fin/tours_cal_ter_np.png 0.5 >/dev/null 2>&1
python3 meubles_poser.py ${O}_d0.jpg fin/pal_${P}_meubles.png ${O}_d.jpg >/dev/null
[ -n "$STOP_D" ] && { echo fini ${O}_d.jpg; exit 0; }
GARDER=cas/tours_garder2.json FONDU_ZONE=8 MOBILIER_SEPARE=1 HAUT_MOBILIER=0 python3 amenage.py ${O}_d.jpg cas/tours_zone3.json 1 cas/tours_amenage.txt ${O}_e.jpg fin/pal_${P}_calque.png fin/vide_tours.png fin/tours_cal_ter.png 0.0 > ${O}_amenage.log 2>&1
cp ${O}_e.jpg ${O}_g.jpg; echo fini ${O}_g.jpg
