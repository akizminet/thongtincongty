from DichVuThongTin import ThongTinDoanhNghiep
import json
import time
result = []
data_source = open("masothue.txt",'r',encoding='utf-8').readlines()
tong = len(data_source)
i = 1
for masothue in data_source:
  print('{}/{}'.format(i,tong))
  result.append(ThongTinDoanhNghiep(masothue).getInfo())
  i+=1

with open("ketqua.json",'w',encoding="utf-8") as ketqua:
  json.dump(result,ketqua,ensure_ascii=False)