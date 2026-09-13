"""Fresh manual source census: roof search boxes and identities, before fitting.
Coordinates refer to the exact 2400-pixel SfM frame, never a previous model.
These boxes locate roof surfaces for segmentation and review; they are not geometry.
"""
import json
from pathlib import Path
P=Path('work/rebuild4/architecture');P.mkdir(exist_ok=True)
# ID, roof appearance, source box, provisional floors, relationship / review note.
rows256=[
(1,'flat',[280,10,383,66],4,'pond east standalone gray building'),
(2,'metal',[121,46,299,82],1,'pond service compound long blue roof'),
(3,'flat',[32,51,112,91],2,'pond service compound west white building'),
(4,'metal',[14,78,73,113],1,'pond service compound west white canopy'),
(5,'metal',[86,76,150,107],1,'pond service compound gray canopy'),
(6,'metal',[167,69,208,99],1,'pond service compound white lean-to'),
(7,'metal',[237,62,297,105],1,'pond service compound east gray roof'),
(8,'flat',[98,242,212,309],None,'west pond bank cream flat roof'),
(9,'flat',[207,239,328,306],None,'west pond bank pale green flat roof'),
(10,'flat',[310,255,449,313],None,'west pond bank terracotta terrace roof'),
(11,'metal',[309,218,399,258],1,'white canopy behind terrace-roof building'),
(12,'flat',[148,335,270,404],None,'blue waterproofed flat roof'),
(13,'flat',[270,342,369,399],None,'terracotta terrace of narrow tall dwelling'),
(14,'flat',[429,386,557,432],2,'dark flat roof with raised roof room'),
(15,'flat',[437,339,507,375],1,'raised roof room; attach to V0014 after height review'),
(16,'flat',[565,279,674,354],None,'brown narrow tall dwelling'),
(17,'flat',[697,300,792,369],None,'white flat roof with red parapet trim'),
(18,'metal',[132,448,283,559],1,'large white sheet roof over old low dwelling'),
(19,'flat',[278,448,354,529],None,'narrow gray flat roof dwelling'),
(20,'metal',[358,461,435,509],1,'striped lean-to beside narrow dwelling'),
(21,'gable',[402,461,553,529],1,'wide yellow old dwelling with tile roof'),
(22,'metal',[569,419,621,505],1,'garden-side narrow blue gray shelter'),
(23,'gable',[556,523,608,590],1,'narrow old red tile roof beside garden'),
(24,'hip_metal',[673,469,841,562],1,'red public hall roof; open stage facade, not residential template'),
(25,'metal',[300,555,377,604],1,'small red sheet roof building'),
(26,'gable',[367,598,414,655],1,'small tiled courtyard wing'),
(27,'flat',[203,625,286,670],None,'small flat rooftop and cylindrical tank'),
(28,'metal',[170,593,220,623],1,'small white lean-to'),
(29,'gable',[283,619,311,661],1,'narrow tile roof beside small red roof'),
(30,'gable',[439,596,518,645],1,'old tile roof with pale adjoining wall'),
(31,'metal',[438,575,482,604],1,'white courtyard canopy'),
(32,'metal',[414,610,455,631],1,'slender white courtyard awning'),
(33,'flat',[435,685,519,803],3,'tall narrow white roof; horizontal courtyard canopy is separate V0073'),
(34,'gable',[80,695,172,780],1,'dark tiled roof under tall white building'),
(35,'gable',[177,649,281,724],1,'red tile roof above weathered concrete terrace'),
(36,'flat',[181,721,282,773],1,'weathered low flat roof'),
(37,'flat',[247,773,303,815],1,'weathered extension beside white L roof'),
(38,'gable',[147,810,248,876],1,'gray gable building with red tiles'),
(39,'flat',[96,814,184,869],1,'dark low terrace beside gable building'),
(40,'gable',[-20,866,119,958],1,'left image edge incomplete; requires another source view'),
(41,'gable',[113,868,183,946],1,'left tiled row west unit'),
(42,'gable',[179,867,243,946],1,'left tiled row east unit'),
(43,'gable',[247,869,445,946],1,'long tiled dwelling with three facade bays'),
(44,'gable',[513,782,592,861],1,'narrow yellow tiled dwelling'),
(45,'gable',[639,775,792,865],1,'wide yellow tiled dwelling'),
(46,'gable',[594,744,633,792],1,'narrow tiled wing between roof rows'),
(47,'flat',[529,729,596,772],1,'small weathered red roof surface'),
(48,'flat',[642,744,700,781],1,'red low extension beneath white building'),
(49,'gable',[425,892,505,1004],1,'long perpendicular tiled dwelling beside garden'),
(50,'flat',[494,918,552,1008],1,'weathered flat courtyard room'),
(51,'metal',[713,885,782,977],1,'cyan roof beside vegetable garden'),
(52,'metal',[744,867,798,915],1,'red rear section of cyan roof compound'),
(53,'gable',[771,908,846,1005],1,'tiled building east of cyan roof'),
(54,'gable',[711,1000,761,1101],1,'narrow tiled house at garden end'),
(55,'flat',[644,1030,712,1113],1,'weathered terracotta low roof'),
(56,'gable',[590,1018,650,1120],1,'narrow tiled low dwelling'),
(57,'gable',[390,1049,578,1118],1,'long tiled courtyard wing'),
(58,'gable',[200,981,274,1061],1,'narrow yellow dwelling by garden'),
(59,'metal',[146,974,205,1047],1,'long pale canopy beside narrow yellow dwelling'),
(60,'gable',[163,1065,369,1130],1,'courtyard compound north tiled wing'),
(61,'gable',[149,1097,231,1200],1,'courtyard compound west tiled wing, related V0060'),
(62,'gable',[-20,1067,120,1198],1,'left image edge incomplete; requires another source view'),
(63,'gable',[558,1167,753,1271],1,'large old tiled dwelling beside tall gray house'),
(64,'flat',[689,1118,751,1172],1,'ambiguous dark terrace or low roof; ground classification required'),
(65,'flat',[735,1211,817,1355],None,'large gray flat roof at image bottom; alternate view required'),
(66,'flat',[292,1087,456,1246],None,'tall gray dwelling with yellow roof finish'),
(67,'flat',[188,1115,299,1276],None,'narrow tall dwelling with weathered roof and tank'),
(68,'flat',[442,1296,531,1370],None,'bottom image edge incomplete; requires another source view'),
(69,'flat',[302,1324,416,1405],None,'bottom image edge incomplete; requires another source view'),
(70,'gable',[96,1246,238,1346],1,'large lower-left old tiled dwelling'),
(71,'gable',[2,1215,91,1280],1,'small old tile roof near left border'),
(72,'gable',[-20,1267,33,1358],1,'left and bottom edges incomplete; alternate view required'),
]
rows256 += json.loads((P/'census_center_rows.json').read_text())
rows256 += json.loads((P/'census_right_rows.json').read_text())
entries=[]
allrows=[('frame_256.00.jpg',row) for row in rows256]
for file,name in [('census_south_rows.json','frame_000.00.jpg'),('census_north64_rows.json','frame_064.00.jpg'),('census_north90_rows.json','frame_090.00.jpg'),('census_hill120_rows.json','frame_120.00.jpg')]:
 if (P/file).exists():allrows += [(name,row) for row in json.loads((P/file).read_text())]
for name,(i,form,box,floors,note) in allrows:
 entries.append(dict(id=f'V{i:04}',source_image=name,roof_type=form,search_box_px=box,floor_count=floors,floor_status='manual preliminary; facade review pending' if floors else 'not yet counted',note=note,source_identity_status='manual located roof surface; duplicate and main-body/wing adjudication pending',partial_image_boundary=any([box[0]<3,box[1]<3,box[2]>2397,box[3]>1347])))
(P/'census_box_annotations.json').write_text(json.dumps(dict(status='fresh source search-box census under construction; not a completed count',entries=entries),indent=2,ensure_ascii=False));print('SOURCE_IDENTITIES_LOCATED',len(entries))
