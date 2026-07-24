#!/usr/bin/env python3
"""
Extract the full PTS Reference table from the blog post HTML
and save to Excel.

Source: https://palistudies.blogspot.com/2020/02/sutta-number-to-pts-reference-converter.html
"""

import re
import base64
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# The HTML table data extracted from the blog post
# Each row: [sutta_id, type, pts_ref]
# We parse from the raw blog content

DATA_RAW = """DN 1: Brahmajāla	Sutta	D i 1
DN 2: Sāmaññaphala	Sutta	D i 47
DN 3: Ambaṭṭha	Sutta	D i 87
DN 4: Soṇadaṇḍa	Sutta	D i 111
DN 5: Kūṭadanta	Sutta	D i 127
DN 6: Mahāli	Sutta	D i 150
DN 7: Jāliya	Sutta	D i 159
DN 8: Kassapasīhanāda	Sutta	D i 161
DN 9: Poṭṭhapāda	Sutta	D i 178
DN 10: Subha	Sutta	D i 204
DN 11: Kevaṭṭa	Sutta	D i 211
DN 12: Lohicca	Sutta	D i 224
DN 13: Tevijja	Sutta	D i 235
DN 14: Mahāpadāna	Sutta	D ii 1
DN 15: Mahānidāna	Sutta	D ii 55
DN 16: Mahāparinibbāna	Sutta	D ii 72
DN 17: Mahāsudassana	Sutta	D ii 169
DN 18: Janavasabha	Sutta	D ii 200
DN 19: Mahāgovinda	Sutta	D ii 220
DN 20: Mahāsamaya	Sutta	D ii 253
DN 21: Sakkapañha	Sutta	D ii 263
DN 22: Mahāsatipaṭṭhāna	Sutta	D ii 290
DN 23: Pāyāsi	Sutta	D ii 316
DN 24: Pāṭika	Sutta	D iii 1
DN 25: Udumbarika-sīhanāda	Sutta	D iii 36
DN 26: Cakkavatti-sīhanāda	Sutta	D iii 58
DN 27: Aggañña	Sutta	D iii 80
DN 28: Sampasādanīya	Sutta	D iii 99
DN 29: Pāsādika	Sutta	D iii 117
DN 30: Lakkhaṇa	Sutta	D iii 142
DN 31: Siṅgālovāda	Sutta	D iii 180
DN 32: Āṭānāṭiya	Sutta	D iii 194
DN 33: Saṅgīti	Sutta	D iii 207
DN 34: Dasuttara	Sutta	D iii 272
MN 1: Mūlapariyāya	Sutta	M i 1
MN 2: Sabbāsava	Sutta	M i 6
MN 3: Dhammadāyāda	Sutta	M i 12
MN 4: Bhayabherava	Sutta	M i 16
MN 5: Anaṅgaṇa	Sutta	M i 24
MN 6: Ākaṅkheyya	Sutta	M i 33
MN 7: Vatthūpama	Sutta	M i 36
MN 8: Sallekha	Sutta	M i 40
MN 9: Sammādiṭṭhi	Sutta	M i 46
MN 10: Satipaṭṭhāna	Sutta	M i 55
MN 11: Cūḷasīhanāda	Sutta	M i 63
MN 12: Mahāsīhanāda	Sutta	M i 68
MN 13: Mahādukkhakkhandha	Sutta	M i 83
MN 14: Cūḷadukkhakkhandha	Sutta	M i 91
MN 15: Anumāna	Sutta	M i 95
MN 16: Cetokhīla	Sutta	M i 101
MN 17: Vanapattha	Sutta	M i 104
MN 18: Madhupiṇḍika	Sutta	M i 108
MN 19: Dvedhāvitakka	Sutta	M i 114
MN 20: Vitakkasaṇṭhāna	Sutta	M i 118
MN 21: Kakacūpama	Sutta	M i 122
MN 22: Alagaddūpama	Sutta	M i 130
MN 23: Vammika	Sutta	M i 142
MN 24: Rathavinīta	Sutta	M i 145
MN 25: Nivāpa	Sutta	M i 151
MN 26: Ariyapariyesana	Sutta	M i 160
MN 27: Cūḷahatthipadopama	Sutta	M i 175
MN 28: Mahāhatthipadopama	Sutta	M i 184
MN 29: Mahāsāropama	Sutta	M i 192
MN 30: Cūḷasāropama	Sutta	M i 198
MN 31: Cūḷagosiṅga	Sutta	M i 205
MN 32: Mahāgosiṅga	Sutta	M i 212
MN 33: Mahāgopālaka	Sutta	M i 220
MN 34: Cūḷagopālaka	Sutta	M i 225
MN 35: Cūḷasaccaka	Sutta	M i 227
MN 36: Mahāsaccaka	Sutta	M i 237
MN 37: Cūḷataṇhāsaṅkhaya	Sutta	M i 251
MN 38: Mahātaṇhāsaṅkhaya	Sutta	M i 256
MN 39: Mahā-Assapura	Sutta	M i 271
MN 40: Cūḷa-Assapura	Sutta	M i 281
MN 41: Saleyyaka	Sutta	M i 285
MN 42: Verañjaka	Sutta	M i 290
MN 43: Mahāvedalla	Sutta	M i 292
MN 44: Cūḷavedalla	Sutta	M i 299
MN 45: Cūḷadhammasamādāna	Sutta	M i 305
MN 46: Mahādhammasamādāna	Sutta	M i 309
MN 47: Vīmaṁsaka	Sutta	M i 317
MN 48: Kosambiyann	Sutta	M i 320
MN 49: Brahmanimantani	Sutta	M i 326
MN 50: Maratajjaniya	Sutta	M i 332
MN 51: Kandaraka	Sutta	M i 339
MN 52: Aṭṭhakanāgara	Sutta	M i 349
MN 53: Sekhann	Sutta	M i 353
MN 54: Potaliya	Sutta	M i 359
MN 55: Jīvaka	Sutta	M i 368
MN 56: Upāli	Sutta	M i 371
MN 57: Kukkuravatika	Sutta	M i 387
MN 58: Abhayarājakumāra	Sutta	M i 392
MN 59: Bahuvedanīya	Sutta	M i 396
MN 60: Apaṇṇaka	Sutta	M i 400
MN 61: Ambalaṭṭhikārāhulovāda	Sutta	M i 414
MN 62: Mahārahulovada	Sutta	M i 420
MN 63: Cūḷamaluṅkya	Sutta	M i 426
MN 64: Mahāmāluṅkya	Sutta	M i 432
MN 65: Bhaddāli	Sutta	M i 437
MN 66: Laṭukikopama	Sutta	M i 447
MN 67: Cātuma	Sutta	M i 456
MN 68: Naḷakapāna	Sutta	M i 462
MN 69: Gulissāni	Sutta	M i 469
MN 70: Kiṭāgiri	Sutta	M i 473
MN 71: Tevijja-vacchagottann	Sutta	M i 481
MN 72: Aggivacchagotta	Sutta	M i 483
MN 73: Mahāvacchagotta	Sutta	M i 489
MN 74: Dīghanakha	Sutta	M i 497
MN 75: Māgandiya	Sutta	M i 501
MN 76: Sandaka	Sutta	M i 513
MN 77: Mahāsakuludāyi	Sutta	M ii 1
MN 78: Samaṇamaṇḍikā	Sutta	M ii 22
MN 79: Cūḷasakuludāyi	Sutta	M ii 29
MN 80: Vekhanassa	Sutta	M ii 40
MN 81: Ghaṭikāra	Sutta	M ii 45
MN 82: Raṭṭhapala	Sutta	M ii 54
MN 83: Makhādeva	Sutta	M ii 74
MN 84: Madhura	Sutta	M ii 83
MN 85: Bodhirajakumāra	Sutta	M ii 91
MN 86: Aṅgulimāla	Sutta	M ii 97
MN 87: Piyajātika	Sutta	M ii 106
MN 88: Bāhitika	Sutta	M ii 112
MN 89: Dhammacetiya	Sutta	M ii 118
MN 90: Kaṇṇakatthala	Sutta	M ii 125
MN 91: Brahmāyu	Sutta	M ii 133
MN 92: Sela	Sutta	M ii 146
MN 93: Assalāyana	Sutta	M ii 147
MN 94: Ghoṭamukha	Sutta	M ii 157
MN 95: Caṅkī	Sutta	M ii 164
MN 96: Esukāri	Sutta	M ii 177
MN 97: Dhānañjāni	Sutta	M ii 184
MN 98: Vāseṭṭha	Sutta	M ii 196
MN 99: Subha	Sutta	M ii 196
MN 100: Saṅgārava	Sutta	M ii 209
MN 101: Devadaha	Sutta	M ii 214
MN 102: Pañcattaya	Sutta	M ii 228
MN 103: Kinti	Sutta	M ii 238
MN 104: Sāmagāma	Sutta	M ii 243
MN 105: Sunakkhatta	Sutta	M ii 252
MN 106: Āneñjasappāya	Sutta	M ii 261
MN 107: Gaṇakamoggallāna	Sutta	M iii 1
MN 108: Gopakamoggallāna	Sutta	M iii 7
MN 109: Mahāpuṇṇama	Sutta	M iii 15
MN 110: Cūlapuṇṇma	Sutta	M iii 20
MN 111: Anupada	Sutta	M iii 25
MN 112: Chabbisodhana	Sutta	M iii 29
MN 113: Sappurisa	Sutta	M iii 37
MN 114: Sevitabbasevitabba	Sutta	M iii 45
MN 115: Bahudhātuka	Sutta	M iii 61
MN 116: Isigili	Sutta	M iii 68
MN 117: Mahācattārīsaka	Sutta	M iii 71
MN 118: Ānāpānasati	Sutta	M iii 78
MN 119: Kāyagatāsati	Sutta	M iii 88
MN 120: Saṅkhārupapatti	Sutta	M iii 99
MN 121: Cūḷasuññata	Sutta	M iii 104
MN 122: Mahāsuññata	Sutta	M iii 109
MN 123: Acchariya-abbhuta	Sutta	M iii 118
MN 124: Bakkula	Sutta	M iii 124
MN 125: Dantabhūmi	Sutta	M iii 128
MN 126: Bhūmija	Sutta	M iii 138
MN 127: Anuruddha	Sutta	M iii 144
MN 128: Upakkilesa	Sutta	M iii 152
MN 129: Bālapaṇḍita	Sutta	M iii 163
MN 130: Devadūta	Sutta	M iii 178
MN 131: Bhaddekaratta	Sutta	M iii 187
MN 132: Ānandabhaddekaratta	Sutta	M iii 189
MN 133: Mahākaccanabhaddekaratta	Sutta	M iii 192
MN 134: Lomasakaṅgiyabhaddekaratta	Sutta	M iii 199
MN 135: Cūḷakammavibhaṅga	Sutta	M iii 202
MN 136: Mahākammavibhaṅga	Sutta	M iii 207
MN 137: Saḷāyatanavibhaṅga	Sutta	M iii 215
MN 138: Uddesavibhaṅga	Sutta	M iii 223
MN 139: Araṇavibhaṅga	Sutta	M iii 230
MN 140: Dhātuvibhaṅga	Sutta	M iii 237
MN 141: Saccavibhaṅga	Sutta	M iii 248
MN 142: Dakkhiṇāvibhaṅga	Sutta	M iii 253
MN 143: Anāthapiṇḍikovāda	Sutta	M iii 258
MN 144: Channovāda	Sutta	M iii 263
MN 145: Puṇṇovāda	Sutta	M iii 267
MN 146: Nandakovāda	Sutta	M iii 270
MN 147: Cūḷarāhulovāda	Sutta	M iii 277
MN 148: Chachakka	Sutta	M iii 280
MN 149: Mahāsaḷāyatanika	Sutta	M iii 287
MN 150: Nagaravindeyya	Sutta	M iii 290
MN 151: Piṇḍapātapārisuddha	Sutta	M iii 293
MN 152: Indriyabhāvana	Sutta	M iii 298
SN 1.1 (SN 1) Oghataraṇa	Sutta	S i 1 [S i 1]
SN 1.2 (SN 2) Nimokkha	Sutta	S i 2 [S i 2]
SN 1.3 (SN 3) Upanīya	Sutta	S i 2 [S i 4]
SN 1.4 (SN 4) Accenti	Sutta	S i 3 [S i 5]
SN 1.5 (SN 5) Katichinda	Sutta	S i 3 [S i 5]
SN 1.6 (SN 6) Jāgara	Sutta	S i 3 [S i 6]
SN 1.7 (SN 7) Appaṭividita	Sutta	S i 4 [S i 7]
SN 1.8 (SN 8) Susammuṭṭha	Sutta	S i 4 [S i 7]
SN 1.9 (SN 9) Mānakāma	Sutta	S i 4 [S i 8]
SN 1.10 (SN 10) Arañña	Sutta	S i 5 [S i 9]
SN 1.11 (SN 11) Nandana	Sutta	S i 5 [S i 11]
SN 1.12 (SN 12) Nandati	Sutta	S i 6 [S i 11]
SN 1.13 (SN 13) Natthiputtasama	Sutta	S i 6 [S i 12]
SN 1.14 (SN 14) Khattiya	Sutta	S i 6 [S i 13]
SN 1.15 (SN 15) Saṇamāna	Sutta	S i 7 [S i 13]
SN 1.16 (SN 16) Niddātandī	Sutta	S i 7 [S i 14]
SN 1.17 (SN 17) Dukkara	Sutta	S i 7 [S i 15]
SN 1.18 (SN 18) Hirī	Sutta	S i 7 [S i 16]
SN 1.19 (SN 19) Kuṭikā	Sutta	S i 8 [S i 17]
SN 1.20 (SN 20) Samiddhi	Sutta	S i 8 [S i 18]
SN 1.21 (SN 21) Satti	Sutta	S i 13 [S i 27]
SN 1.22 (SN 22) Phusati	Sutta	S i 13 [S i 27]
SN 1.23 (SN 23) Jaṭā	Sutta	S i 13 [S i 28]
SN 1.24 (SN 24) Manonivāraṇa	Sutta	S i 14 [S i 29]
SN 1.25 (SN 25) Arahanta	Sutta	S i 14 [S i 30]
SN 1.26 (SN 26) Pajjota	Sutta	S i 15 [S i 32]
SN 1.27 (SN 27) Sara	Sutta	S i 15 [S i 33]
SN 1.28 (SN 28) Mahaddhana	Sutta	S i 15 [S i 33]
SN 1.29 (SN 29) Catucakka	Sutta	S i 16 [S i 35]
SN 1.30 (SN 30) Eṇijaṅgha	Sutta	S i 16 [S i 35]
SN 1.31 (SN 31) Sabbhi	Sutta	S i 16 [S i 37]
SN 1.32 (SN 32) Macchari	Sutta	S i 18 [S i 39]
SN 1.33 (SN 33) Sādhu	Sutta	S i 20 [S i 41]
SN 1.34 (SN 34) Nasanti	Sutta	S i 22 [S i 46]
SN 1.35 (SN 35) Ujjhānasaññi	Sutta	S i 23 [S i 49]
SN 1.36 (SN 36) Saddhā	Sutta	S i 25 [S i 53]
SN 1.37 (SN 37) Samaya	Sutta	S i 26 [S i 54]
SN 1.38 (SN 38) Sakalika	Sutta	S i 27 [S i 57]
SN 1.39 (SN 39) Paṭhamapajjunnadhītu	Sutta	S i 29 [S i 61]
SN 1.40 (SN 40) Dutiyapajjunnadhītu	Sutta	S i 30 [S i 62]
SN 1.41 (SN 41) Āditta	Sutta	S i 31 [S i 64]
SN 1.42 (SN 42) Kiṃdada	Sutta	S i 32 [S i 66]
SN 1.43 (SN 43) Anna	Sutta	S i 32 [S i 67]
SN 1.44 (SN 44) Ekamūla	Sutta	S i 32 [S i 67]
SN 1.45 (SN 45) Anoma	Sutta	S i 33 [S i 68]
SN 1.46 (SN 46) Accharā	Sutta	S i 33 [S i 69]
SN 1.47 (SN 47) Vanaropa	Sutta	S i 33 [S i 70]
SN 1.48 (SN 48) Jetavana	Sutta	S i 33 [S i 71]
SN 1.49 (SN 49) Macchari	Sutta	S i 34 [S i 72]
SN 1.50 (SN 50) Ghaṭīkāra	Sutta	S i 35 [S i 75]
SN 1.51 (SN 51) Jarā	Sutta	S i 36 [S i 79]
SN 1.52 (SN 52) Ajarasā	Sutta	S i 36 [S i 79]
SN 1.53 (SN 53) Mitta	Sutta	S i 37 [S i 80]
SN 1.54 (SN 54) Vatthu	Sutta	S i 37 [S i 81]
SN 1.55 (SN 55) Paṭhamajana	Sutta	S i 37 [S i 82]
SN 1.56 (SN 56) Dutiyajana	Sutta	S i 37 [S i 82]
SN 1.57 (SN 57) Tatiyajana	Sutta	S i 38 [S i 83]
SN 1.58 (SN 58) Uppatha	Sutta	S i 38 [S i 83]
SN 1.59 (SN 59) Dutiya	Sutta	S i 38 [S i 84]
SN 1.60 (SN 60) Kavi	Sutta	S i 38 [S i 85]
SN 1.61 (SN 61) Nāma	Sutta	S i 39 [S i 86]
SN 1.62 (SN 62) Citta	Sutta	S i 39 [S i 87]
SN 1.63 (SN 63) Taṇhā	Sutta	S i 39 [S i 87]
SN 1.64 (SN 64) Saṃyojana	Sutta	S i 39 [S i 88]
SN 1.65 (SN 65) Bandhana	Sutta	S i 39 [S i 88]
SN 1.66 (SN 66) Attahata	Sutta	S i 40 [S i 88]
SN 1.67 (SN 67) Uḍḍita	Sutta	S i 40 [S i 89]
SN 1.68 (SN 68) Pihita	Sutta	S i 40 [S i 91]
SN 1.69 (SN 69) Icchā	Sutta	S i 40 [S i 91]
SN 1.70 (SN 70) Loka	Sutta	S i 41 [S i 92]
SN 1.71 (SN 71) Chetvā	Sutta	S i 41 [S i 93]
SN 1.72 (SN 72) Ratha	Sutta	S i 41 [S i 93]
SN 1.73 (SN 73) Vitta	Sutta	S i 42 [S i 94]
SN 1.74 (SN 74) Vuṭṭhi	Sutta	S i 42 [S i 95]
SN 1.75 (SN 75) Bhītā	Sutta	S i 42 [S i 95]
SN 1.76 (SN 76) Najīrati	Sutta	S i 43 [S i 96]
SN 1.77 (SN 77) Issariya	Sutta	S i 43 [S i 98]
SN 1.78 (SN 78) Kāma	Sutta	S i 44 [S i 99]
SN 1.79 (SN 79) Pātheyya	Sutta	S i 44 [S i 100]
SN 1.80 (SN 80) Pajjota	Sutta	S i 44 [S i 101]
SN 1.81 (SN 81) Araṇa	Sutta	S i 44 [S i 102]
SN 2.1 (SN 82) Paṭhamakassapa	Sutta	S i 46 [S i 104]
SN 2.2 (SN 83) Dutiyakassapa	Sutta	S i 46 [S i 105]
SN 2.3 (SN 84) Māgha	Sutta	S i 47 [S i 105]
SN 2.4 (SN 85) Māgadha	Sutta	S i 47 [S i 106]
SN 2.5 (SN 86) Dāmali	Sutta	S i 47 [S i 107]
SN 2.6 (SN 87) Kāmada	Sutta	S i 48 [S i 109]
SN 2.7 (SN 88) Pañcālacaṇḍa	Sutta	S i 48 [S i 110]
SN 2.8 (SN 89) Tāyana	Sutta	S i 49 [S i 111]
SN 2.9 (SN 90) Candima	Sutta	S i 50 [S i 114]
SN 2.10 (SN 91) Sūriya	Sutta	S i 51 [S i 115]
SN 2.11 (SN 92) Candimasa	Sutta	S i 51 [S i 117]
SN 2.12 (SN 93) Veṇḍu	Sutta	S i 52 [S i 118]
SN 2.13 (SN 94) Dīghalaṭṭhi	Sutta	S i 52 [S i 119]
SN 2.14 (SN 95) Nandana	Sutta	S i 52 [S i 120]
SN 2.15 (SN 96) Candana	Sutta	S i 53 [S i 121]
SN 2.16 (SN 97) Vāsudatta	Sutta	S i 53 [S i 122]
SN 2.17 (SN 98) Subrahma	Sutta	S i 53 [S i 122]
SN 2.18 (SN 99) Kakudha	Sutta	S i 54 [S i 123]
SN 2.19 (SN 100) Uttara	Sutta	S i 54 [S i 125]
SN 2.20 (SN 101) Anāthapiṇḍika	Sutta	S i 55 [S i 126]
SN 2.21 (SN 102) Siva	Sutta	S i 56 [S i 129]
SN 2.22 (SN 103) Khema	Sutta	S i 57 [S i 131]
SN 2.23 (SN 104) Serī	Sutta	S i 57 [S i 132]
SN 2.24 (SN 105) Ghaṭīkāra	Sutta	S i 60 [S i 137]
SN 2.25 (SN 106) Jantu	Sutta	S i 61 [S i 141]
SN 2.26 (SN 107) Rohitassa	Sutta	S i 61 [S i 142]
SN 2.27 (SN 108) Nanda	Sutta	S i 62 [S i 143]
SN 2.28 (SN 109) Nandivisāla	Sutta	S i 63 [S i 146]
SN 2.29 (SN 110) Susima	Sutta	S i 63 [S i 146]
SN 2.30 (SN 111) Nānātitthiyasāvaka	Sutta	S i 65 [S i 151]
SN 3.1 (SN 112) Dahara	Sutta	S i 70 [S i 156]
SN 3.2 (SN 113) Purisa	Sutta	S i 70 [S i 162]
SN 3.3 (SN 114) Jarāmaraṇa	Sutta	S i 71 [S i 163]
SN 3.4 (SN 115) Piya	Sutta	S i 71 [S i 164]
SN 3.5 (SN 116) Attarakkhita	Sutta	S i 72 [S i 166]
SN 3.6 (SN 117) Appaka	Sutta	S i 73 [S i 168]
SN 3.7 (SN 118) Aḍḍakaraṇa	Sutta	S i 74 [S i 170]
SN 3.8 (SN 119) Mallikā	Sutta	S i 75 [S i 171]
SN 3.9 (SN 120) Yañña	Sutta	S i 75 [S i 172]
SN 3.10 (SN 121) Bandhana	Sutta	S i 76 [S i 174]
SN 3.11 (SN 122) Sattajaṭila	Sutta	S i 77 [S i 176]
SN 3.12 (SN 123) Pañcarāja	Sutta	S i 79 [S i 181]
SN 3.13 (SN 124) Doṇapāka	Sutta	S i 81 [S i 185]
SN 3.14 (SN 125) Paṭhamasaṅgāma	Sutta	S i 82 [S i 187]
SN 3.15 (SN 126) Dutiyasaṅgāma	Sutta	S i 83 [S i 190]
SN 3.16 (SN 127) Mallikā	Sutta	S i 86 [S i 194]
SN 3.17 (SN 128) Appamāda	Sutta	S i 86 [S i 195]
SN 3.18 (SN 129) Kalyāṇamitta	Sutta	S i 87 [S i 197]
SN 3.19 (SN 130) Paṭhamāputtaka	Sutta	S i 89 [S i 201]
SN 3.20 (SN 131) Dutiyāputtaka	Sutta	S i 91 [S i 205]
SN 3.21 (SN 132) Puggala	Sutta	S i 93 [S i 209]
SN 3.22 (SN 133) Ayyikā	Sutta	S i 96 [S i 216]
SN 3.23 (SN 134) Loka	Sutta	S i 98 [S i 218]
SN 3.24 (SN 135) Issatta	Sutta	S i 98 [S i 219]
SN 3.25 (SN 136) Pabbatūpama	Sutta	S i 100 [S i 224]
SN 4.1 (SN 137) Tapokamma	Sutta	S i 103 [S i 231]
SN 4.2 (SN 138) Hatthirājavaṇṇa	Sutta	S i 103 [S i 232]
SN 4.3 (SN 139) Subha	Sutta	S i 105 [S i 233]
SN 4.4 (SN 140) Paṭhamamārapāsa	Sutta	S i 105 [S i 234]
SN 4.5 (SN 141) Dutiyamārapāsa	Sutta	S i 106 [S i 236]
SN 4.6 (SN 142) Sappa	Sutta	S i 106 [S i 237]
SN 4.7 (SN 143) Supati	Sutta	S i 107 [S i 239]
SN 4.8 (SN 144) Nandati	Sutta	S i 107 [S i 240]
SN 4.9 (SN 145) Paṭhamāayu	Sutta	S i 108 [S i 241]
SN 4.10 (SN 146) Dutiyāayu	Sutta	S i 108 [S i 242]
SN 4.11 (SN 147) Pāsāṇa	Sutta	S i 109 [S i 243]
SN 4.12 (SN 148) Kinnusīha	Sutta	S i 109 [S i 244]
SN 4.13 (SN 149) Sakalika	Sutta	S i 110 [S i 245]
SN 4.14 (SN 150) Patirūpa	Sutta	S i 111 [S i 247]
SN 4.15 (SN 151) Mānasa	Sutta	S i 111 [S i 248]
SN 4.16 (SN 152) Patta	Sutta	S i 112 [S i 249]
SN 4.17 (SN 153) Chaphassāyatana	Sutta	S i 112 [S i 251]
SN 4.18 (SN 154) Piṇḍa	Sutta	S i 113 [S i 252]
SN 4.19 (SN 155) Kassaka	Sutta	S i 114 [S i 253]
SN 4.20 (SN 156) Rajja	Sutta	S i 116 [S i 257]
SN 4.21 (SN 157) Sambahula	Sutta	S i 117 [S i 259]
SN 4.22 (SN 158) Samiddhi	Sutta	S i 119 [S i 262]
SN 4.23 (SN 159) Godhika	Sutta	S i 120 [S i 264]
SN 4.24 (SN 160) Sattavassānubandha	Sutta	S i 122 [S i 269]
SN 4.25 (SN 161) Māradhītu	Sutta	S i 124 [S i 273]
SN 5.1 (SN 162) Āḷavikā	Sutta	S i 128 [S i 281]
SN 5.2 (SN 163) Somā	Sutta	S i 129 [S i 283]
SN 5.3 (SN 164) Kisāgotamī	Sutta	S i 129 [S i 284]
SN 5.4 (SN 165) Vijayā	Sutta	S i 130 [S i 286]
SN 5.5 (SN 166) Uppalavaṇṇā	Sutta	S i 131 [S i 287]
SN 5.6 (SN 167) Cālā	Sutta	S i 132 [S i 290]
SN 5.7 (SN 168) Upacālā	Sutta	S i 133 [S i 291]
SN 5.8 (SN 169) Sīsupacālā	Sutta	S i 133 [S i 292]
SN 5.9 (SN 170) Selā	Sutta	S i 134 [S i 294]
SN 5.10 (SN 171) Vajirā	Sutta	S i 134 [S i 296]
SN 6.1 (SN 172) Brahmāyācana	Sutta	S i 136 [S i 298]
SN 6.2 (SN 173) Gārava	Sutta	S i 138 [S i 303]
SN 6.3 (SN 174) Brahmadeva	Sutta	S i 140 [S i 306]
SN 6.4 (SN 175) Bakabrahma	Sutta	S i 142 [S i 310]
SN 6.5 (SN 176) Aññatarabrahma	Sutta	S i 144 [S i 314]
SN 6.6 (SN 177) Brahmaloka	Sutta	S i 146 [S i 318]
SN 6.7 (SN 178) Kokālika	Sutta	S i 148 [S i 322]
SN 6.8 (SN 179) Katamodakatissa	Sutta	S i 149 [S i 322]
SN 6.9 (SN 180) Turūbrahma	Sutta	S i 149 [S i 324]
SN 6.10 (SN 181) Kokālika	Sutta	S i 149 [S i 325]
SN 6.11 (SN 182) Sanaṅkumāra	Sutta	S i 153 [S i 331]
SN 6.12 (SN 183) Devadatta	Sutta	S i 153 [S i 331]
SN 6.13 (SN 184) Andhakavinda	Sutta	S i 154 [S i 333]
SN 6.14 (SN 185) Aruṇavatī	Sutta	S i 155 [S i 333]
SN 6.15 (SN 186) Parinibbāna	Sutta	S i 157 [S i 340]
SN 7.1 (SN 187) Dhanañjānī	Sutta	S i 160 [S i 344]
SN 7.2 (SN 188) Akkosa	Sutta	S i 161 [S i 347]
SN 7.3 (SN 189) Asurindaka	Sutta	S i 163 [S i 350]
SN 7.4 (SN 190) Bilaṅgika	Sutta	S i 164 [S i 351]
SN 7.5 (SN 191) Ahiṃsaka	Sutta	S i 164 [S i 352]
SN 7.6 (SN 192) Jaṭā	Sutta	S i 165 [S i 353]
SN 7.7 (SN 193) Suddhika	Sutta	S i 165 [S i 354]
SN 7.8 (SN 194) Aggika	Sutta	S i 166 [S i 355]
SN 7.9 (SN 195) Sundarika	Sutta	S i 167 [S i 358]
SN 7.10 (SN 196) Bahudhītara	Sutta	S i 170 [S i 365]
SN 7.11 (SN 197) Kasibhāradvāja	Sutta	S i 172 [S i 369]
SN 7.12 (SN 198) Udaya	Sutta	S i 173 [S i 373]
SN 7.13 (SN 199) Devahita	Sutta	S i 174 [S i 375]
SN 7.14 (SN 200) Mahāsāla	Sutta	S i 175 [S i 377]
SN 7.15 (SN 201) Mānatthaddha	Sutta	S i 177 [S i 381]
SN 7.16 (SN 202) Paccanīka	Sutta	S i 179 [S i 385]
SN 7.17 (SN 203) Navakammika	Sutta	S i 179 [S i 386]
SN 7.18 (SN 204) Kaṭṭhahāra	Sutta	S i 180 [S i 388]
SN 7.19 (SN 205) Mātuposaka	Sutta	S i 181 [S i 390]
SN 7.20 (SN 206) Bhikkhaka	Sutta	S i 182 [S i 392]
SN 7.21 (SN 207) Saṅgārava	Sutta	S i 182 [S i 392]
SN 7.22 (SN 208) Khomadussa	Sutta	S i 184 [S i 395]
SN 8.1 (SN 209) Nikkhanta	Sutta	S i 185 [S i 398]
SN 8.2 (SN 210) Arati	Sutta	S i 186 [S i 400]
SN 8.3 (SN 211) Pesala	Sutta	S i 187 [S i 403]
SN 8.4 (SN 212) Ānanda	Sutta	S i 188 [S i 404]
SN 8.5 (SN 213) Subhāsita	Sutta	S i 188 [S i 406]
SN 8.6 (SN 214) Sāriputta	Sutta	S i 189 [S i 408]
SN 8.7 (SN 215) Pavāraṇā	Sutta	S i 190 [S i 410]
SN 8.8 (SN 216) Parosahassa	Sutta	S i 192 [S i 414]
SN 8.9 (SN 217) Koṇḍañña	Sutta	S i 193 [S i 417]
SN 8.10 (SN 218) Moggallāna	Sutta	S i 194 [S i 419]
SN 8.11 (SN 219) Gaggarā	Sutta	S i 195 [S i 420]
SN 8.12 (SN 220) Vaṅgīsa	Sutta	S i 196 [S i 421]
SN 9.1 (SN 221) Viveka	Sutta	S i 197 [S i 424]
SN 9.2 (SN 222) Upaṭṭhāna	Sutta	S i 197 [S i 425]
SN 9.3 (SN 223) Kassapagotta	Sutta	S i 198 [S i 427]
SN 9.4 (SN 224) Sambahula	Sutta	S i 199 [S i 428]
SN 9.5 (SN 225) Ānanda	Sutta	S i 199 [S i 429]
SN 9.6 (SN 226) Anuruddha	Sutta	S i 200 [S i 430]
SN 9.7 (SN 227) Nāgadatta	Sutta	S i 200 [S i 432]
SN 9.8 (SN 228) Kulagharaṇī	Sutta	S i 201 [S i 433]
SN 9.9 (SN 229) Vajjiputta	Sutta	S i 201 [S i 434]
SN 9.10 (SN 230) Sajjhāya	Sutta	S i 202 [S i 435]
SN 9.11 (SN 231) Akusalavitakka	Sutta	S i 203 [S i 436]
SN 9.12 (SN 232) Majjhanhika	Sutta	S i 203 [S i 437]
SN 9.13 (SN 233) Pākatindriya	Sutta	S i 203 [S i 438]
SN 9.14 (SN 234) Gandhatthena	Sutta	S i 204 [S i 440]
SN 10.1 (SN 235) Indaka	Sutta	S i 206 [S i 443]
SN 10.2 (SN 236) Sakkanāma	Sutta	S i 206 [S i 444]
SN 10.3 (SN 237) Sūciloma	Sutta	S i 207 [S i 445]
SN 10.4 (SN 238) Maṇibhadda	Sutta	S i 208 [S i 447]
SN 10.5 (SN 239) Sānu	Sutta	S i 208 [S i 448]
SN 10.6 (SN 240) Piyaṅkara	Sutta	S i 209 [S i 451]
SN 10.7 (SN 241) Punabbasu	Sutta	S i 209 [S i 452]
SN 10.8 (SN 242) Sudatta	Sutta	S i 210 [S i 455]
SN 10.9 (SN 243) Paṭhamasukkā	Sutta	S i 212 [S i 458]
SN 10.10 (SN 244) Dutiyasukkā	Sutta	S i 212 [S i 458]
SN 10.11 (SN 245) Cīrā	Sutta	S i 213 [S i 460]
SN 10.12 (SN 246) Āḷavaka	Sutta	S i 213 [S i 460]
SN 11.1 (SN 247) Suvīra	Sutta	S i 216 [S i 466]
SN 11.2 (SN 248) Susīma	Sutta	S i 217 [S i 469]
SN 11.3 (SN 249) Dhajagga	Sutta	S i 218 [S i 472]
SN 11.4 (SN 250) Vepacitti	Sutta	S i 220 [S i 475]
SN 11.5 (SN 251) Subhāsitajaya	Sutta	S i 222 [S i 479]
SN 11.6 (SN 252) Kulāvaka	Sutta	S i 224 [S i 483]
SN 11.7 (SN 253) Nadubbhiya	Sutta	S i 225 [S i 484]
SN 11.8 (SN 254) Verocanāsurinda	Sutta	S i 225 [S i 485]
SN 11.9 (SN 255) Araññāyatanaisi	Sutta	S i 226 [S i 486]
SN 11.10 (SN 256) Samuddaka	Sutta	S i 226 [S i 487]
SN 11.11 (SN 257) Vatapada	Sutta	S i 228 [S i 492]
SN 11.12 (SN 258) Sakkanāma	Sutta	S i 229 [S i 493]
SN 11.13 (SN 259) Mahāli	Sutta	S i 230 [S i 495]
SN 11.14 (SN 260) Dalidda	Sutta	S i 231 [S i 497]
SN 11.15 (SN 261) Rāmaṇeyyaka	Sutta	S i 232 [S i 498]
SN 11.16 (SN 262) Yajamāna	Sutta	S i 233 [S i 500]
SN 11.17 (SN 263) Buddhavandanā	Sutta	S i 233 [S i 501]
SN 11.18 (SN 264) Gahaṭṭhavandanā	Sutta	S i 234 [S i 502]
SN 11.19 (SN 265) Satthāravandanā	Sutta	S i 235 [S i 504]
SN 11.20 (SN 266) Saṅghavandanā	Sutta	S i 235 [S i 506]
SN 11.21 (SN 267) Chetvā	Sutta	S i 237 [S i 508]
SN 11.22 (SN 268) Dubbaṇṇiya	Sutta	S i 237 [S i 509]
SN 11.23 (SN 269) Sambarimāyā	Sutta	S i 238 [S i 512]
SN 11.24 (SN 270) Accaya	Sutta	S i 239 [S i 513]
SN 11.25 (SN 271) Akkodha	Sutta	S i 240 [S i 514]
SN 12.1 Paṭiccasamuppāda	Sutta	S ii 1
SN 12.2 Vibhaṅga	Sutta	S ii 2
SN 12.3 Paṭipadā	Sutta	S ii 4
SN 12.4 Vipassī	Sutta	S ii 5
SN 12.5 Sikhī	Sutta	S ii 9
SN 12.6 Vessabhū	Sutta	S ii 9
SN 12.7 Kakusandha	Sutta	S ii 9
SN 12.8 Koṇāgamana	Sutta	S ii 9
SN 12.9 Kassapa	Sutta	S ii 9
SN 12.10 Gotama	Sutta	S ii 10
SN 12.11 Āhāra	Sutta	S ii 11
SN 12.12 Moḷiyaphagguna	Sutta	S ii 12
SN 12.13 Samaṇabrāhmaṇa	Sutta	S ii 14
SN 12.14 Dutiyasamaṇabrāhmaṇa	Sutta	S ii 16
SN 12.15 Kaccānagotta	Sutta	S ii 16
SN 12.16 Dhammakathika	Sutta	S ii 18
SN 12.17 Acelakassapa	Sutta	S ii 18
SN 12.18 Timbaruka	Sutta	S ii 22
SN 12.19 Bālapaṇḍita	Sutta	S ii 23
SN 12.20 Paccaya	Sutta	S ii 25
SN 12.21 Dasabala	Sutta	S ii 27
SN 12.22 Dutiyadasabala	Sutta	S ii 28
SN 12.23 Upanisa	Sutta	S ii 29
SN 12.24 Aññatitthiya	Sutta	S ii 33
SN 12.25 Bhūmija	Sutta	S ii 38
SN 12.26 Upavāṇa	Sutta	S ii 41
SN 12.27 Paccaya	Sutta	S ii 42
SN 12.28 Bhikkhu	Sutta	S ii 43
SN 12.29 Samaṇabrāhmaṇa	Sutta	S ii 45
SN 12.30 Dutiyasamaṇabrāhmaṇa	Sutta	S ii 46
SN 12.31 Bhūta	Sutta	S ii 47
SN 12.32 Kaḷāra	Sutta	S ii 50
SN 12.33 Ñāṇavatthu	Sutta	S ii 56
SN 12.34 Dutiyañāṇavatthu	Sutta	S ii 59
SN 12.35 Avijjāpaccaya	Sutta	S ii 60
SN 12.36 Dutiyāvijjāpaccaya	Sutta	S ii 63
SN 12.37 Natumha	Sutta	S ii 64
SN 12.38 Cetanā	Sutta	S ii 65
SN 12.39 Dutiyacetanā	Sutta	S ii 66
SN 12.40 Tatiyacetanā	Sutta	S ii 66
SN 12.41 Pañcaverabhaya	Sutta	S ii 