"""Manual source roof perimeter annotations, retained separately from fitted geometry."""
import json
from pathlib import Path
out=Path('work/rebuild4/architecture')
data=[
('P001','红色三层平屋顶住宅','flat',3,[[350,677],[415,629],[569,638],[510,688]]),
('P002','灰色四层凹口平屋顶住宅','flat',4,[[428,567],[516,514],[708,537],[644,567],[590,562],[570,578]]),
('P003','未完工砖混住宅主楼','flat',3,[[712,665],[749,650],[843,664],[813,681]]),
('P003W1','砖混主楼左低层附房','flat',2,[[655,709],[690,700],[713,703],[713,732],[655,728]]),
('P003W2','砖混主楼右低层附房','flat',2,[[809,743],[842,713],[891,719],[865,750]]),
('P004','深蓝复合坡屋顶白色住宅','hip',3,[[978,594],[1031,529],[1149,543],[1134,568],[1118,566],[1110,582],[1064,579],[1054,599]]),
('P005','青蓝金属屋顶住宅','metal',3,[[800,816],[832,787],[1066,803],[1038,833]]),
('P006','白色凹口住宅及阳台','flat',3,[[685,632],[760,574],[884,586],[844,626],[820,623],[808,642]]),
('P007','后排白色平屋顶住宅','flat',3,[[753,565],[797,536],[912,543],[888,574]]),
('P008','池塘西南白色凹口住宅','flat',3,[[899,429],[937,408],[1048,423],[1025,443],[1003,440],[994,448]]),
('P010','蓝色坡屋顶前低层旧屋','flat',1,[[943,755],[980,698],[1193,705],[1167,767]]),
('P011','临街粉色三层住宅','flat',3,[[1176,748],[1200,691],[1320,703],[1301,760]]),
('P012','红屋前浅粉三层住宅','flat',3,[[458,835],[557,745],[771,756],[687,853]]),
]
entries=[]
for id,name,kind,floors,poly in data:
 entries.append(dict(id=id,name=name,roof_type=kind,floor_count=floors,floor_count_status='agent visual estimate; confirm against rectified facades',source_image='frame_044.00.jpg',roof_polygon_px=poly,annotation='manual approximate source-visible outside roof perimeter, before geometric fitting',parent_id='P003' if 'W' in id else None))
(out/'pilot_source_annotations.json').write_text(json.dumps(dict(status='manual proposed perimeters; dense surface fit and multiview review pending',entries=entries),indent=2,ensure_ascii=False))
