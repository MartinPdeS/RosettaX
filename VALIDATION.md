# Cross-device FCS validation

Scatter and fluorescence are the FCS channels used for bead sizing. R² is the scattering calibration-curve fit for the assigned bead sizes.

| Status | Recording | Model | Scatter | Fluorescence | Sizes&nbsp;(nm) | R² | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PASS | apogee_a50_micro_metves_19s1.fcs | Apogee&nbsp;A50&nbsp;Micro | 405-&#8288;LALS(Peak) | 405-&#8288;Grn(Peak) | ?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.813610 |  |
| PASS | apogee_a60_micro_cal003_2022-&#8288;01-&#8288;31.fcs | Apogee&nbsp;A60&nbsp;Micro | 405LALS(Peak) | 405Grn(Peak) | 70,&nbsp;100,&nbsp;125,&nbsp;147,&nbsp;203,&nbsp;296 | 0.796623 |  |
| PASS | apogee_a60_micro_metves_22v1.fcs | Apogee&nbsp;A60&nbsp;Micro | 405LALS(Peak) | 405Grn(Peak) | 70,&nbsp;100,&nbsp;125,&nbsp;147,&nbsp;203,&nbsp;296 | 0.795784 |  |
| PASS | apogee_microplus_metves_04d1.fcs | Apogee&nbsp;MicroPLUS | LALS(Peak) | 405-&#8288;Grn(Peak) | ?,&nbsp;400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.989953 |  |
| FAIL | apogee_microplus_metves_06f2.fcs | Apogee&nbsp;MicroPLUS | LALS(Peak) | 405-&#8288;Grn(Peak) | ?,&nbsp;?,&nbsp;?,&nbsp;? | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| FAIL | apogee_microplus_metves_07g1.fcs | Apogee&nbsp;MicroPLUS | 405-&#8288;LALS(Peak) | 488-&#8288;Grn(Peak) | ?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;? | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| FAIL | apogee_microplus_metves_07g2.fcs | Apogee&nbsp;MicroPLUS | LALS(Peak) | 488Grn(Peak) | ?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;? | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| FAIL | bd_facscalibur_cal003_2023-&#8288;02-&#8288;08.fcs | BD&nbsp;FACSCalibur | SSC-&#8288;H | FL1-&#8288;H | none | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| PASS | bd_facscelesta_sorp_metves_09i1.fcs | BD&nbsp;FACSCelesta&nbsp;SORP | SSC-&#8288;H | B530/&#8288;30-&#8288;A | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.989216 |  |
| FAIL | bd_facslyric_metves_20t1.fcs | BD&nbsp;FACSLyric | SSC-&#8288;H | FITC-&#8288;H | ?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;?,&nbsp;? | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| PASS | bd_facsymphony_a1_cal003_2022-&#8288;02-&#8288;11.fcs | BD&nbsp;FACSymphony&nbsp;A1 | SSC-&#8288;H | B530/&#8288;30-&#8288;A | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.988895 |  |
| PASS | bd_facsymphony_a1_cal003_2022-&#8288;02-&#8288;18.fcs | BD&nbsp;FACSymphony&nbsp;A1 | SSC-&#8288;H | B530/&#8288;30-&#8288;A | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.989208 |  |
| PASS | bd_facsymphony_a1_cal003_2022-&#8288;11-&#8288;16.fcs | BD&nbsp;FACSymphony&nbsp;A1 | SSC-&#8288;H | BB515-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.985928 |  |
| PASS | bd_facsymphony_a1_metves_25y1.fcs | BD&nbsp;FACSymphony&nbsp;A1 | SSC-&#8288;H | BB515-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.987229 |  |
| PASS | bd_facsymphony_a1_metves_25y2.fcs | BD&nbsp;FACSymphony&nbsp;A1 | SSC-&#8288;H | BB515-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.985928 |  |
| PASS | bd_facsymphony_a5_metves_08h1.fcs | BD&nbsp;FACSymphony&nbsp;A5 | SSC-&#8288;H | BB515-&#8288;H | ?,&nbsp;147,&nbsp;203,&nbsp;296,&nbsp;400,&nbsp;600,&nbsp;799 | 0.991048 |  |
| PASS | beckman_coulter_cytoflex_lx_metves_05e1.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;LX | FL12-&#8288;H | FL1-&#8288;H | ?,&nbsp;147,&nbsp;203,&nbsp;296,&nbsp;400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.932175 |  |
| FAIL | beckman_coulter_cytoflex_lx_metves_14n1.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;LX | SSC_1-&#8288;H | FL1-&#8288;H | ?,&nbsp;?,&nbsp;? | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| PASS | beckman_coulter_cytoflex_lx_metves_16p2.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;LX | SSC_1-&#8288;H | FL1-&#8288;H | 147,&nbsp;203,&nbsp;296,&nbsp;400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.991740 |  |
| PASS | beckman_coulter_cytoflex_s_cal003_2023-&#8288;01-&#8288;05.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;S | SSC_1-&#8288;H | FL1-&#8288;H | ?,&nbsp;?,&nbsp;147,&nbsp;203,&nbsp;296,&nbsp;400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.983627 |  |
| PASS | beckman_coulter_cytoflex_s_metves_05e2.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;S | SSC_1-&#8288;H | FL5-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.953475 |  |
| PASS | beckman_coulter_cytoflex_s_metves_06f1.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;S | SSC_1-&#8288;H | FL1-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.969551 |  |
| PASS | beckman_coulter_cytoflex_s_metves_16p1.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;S | SSC_1-&#8288;H | FL1-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.973443 |  |
| PASS | beckman_coulter_cytoflex_s_metves_23w1.fcs | Beckman&nbsp;Coulter&nbsp;CytoFLEX&nbsp;S | SSC_1-&#8288;H | FL1-&#8288;H | ?,&nbsp;147,&nbsp;203,&nbsp;296,&nbsp;?,&nbsp;? | 0.954591 |  |
| PASS | beckman_coulter_moflo_astrios_metves_21u1.fcs | Beckman&nbsp;Coulter&nbsp;MoFlo&nbsp;Astrios | SSC1-&#8288;Height | FL12-&#8288;Height | 400,&nbsp;600,&nbsp;799,&nbsp;994 | — | no&nbsp;optical&nbsp;preset |
| PASS | cytek_aurora_metves_11k2.fcs | Cytek&nbsp;Aurora | SSC-&#8288;H | B2-&#8288;H | ?,&nbsp;?,&nbsp;147,&nbsp;203,&nbsp;296 | 0.830969 |  |
| FAIL | cytek_aurora_metves_12l1.fcs | Cytek&nbsp;Aurora | SSC-&#8288;H | B2-&#8288;H | ?,&nbsp;?,&nbsp;?,&nbsp;? | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| PASS | cytek_aurora_metves_18r1.fcs | Cytek&nbsp;Aurora | SSC-&#8288;H | B2-&#8288;A | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.989452 |  |
| PASS | cytek_aurora_metves_23w2.fcs | Cytek&nbsp;Aurora | SSC-&#8288;H | B2-&#8288;H | ?,&nbsp;?,&nbsp;147,&nbsp;203,&nbsp;296 | 0.879949 |  |
| FAIL | cytek_northern_lights_metves_22v2.fcs | Cytek&nbsp;Northern&nbsp;Lights | SSC-&#8288;H | B2-&#8288;H | ?,&nbsp;?,&nbsp;?,&nbsp;? | — | fewer&nbsp;than&nbsp;2&nbsp;assigned&nbsp;peaks |
| PASS | miltenyi_macsquant_cal003_2022-&#8288;05-&#8288;13.fcs | Miltenyi&nbsp;Biotec&nbsp;MACSQuant&nbsp;Analyzer&nbsp;16 | SSC-&#8288;H | FL6-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.989987 |  |
| PASS | sony_id7000_experiment_1_beads.fcs | Sony&nbsp;ID7000 | SSC-&#8288;H | FITC-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.989676 |  |
| PASS | sony_id7000_experiment_2_beads.fcs | Sony&nbsp;ID7000 | SSC-&#8288;H | FITC-&#8288;H | 400,&nbsp;600,&nbsp;799,&nbsp;994 | 0.988980 |  |

? = detected peak with no assigned diameter

25/33 recordings passed (66 checks).
