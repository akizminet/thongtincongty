import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def format(maso):
  """
  Kiểm tra định dạng mã số thuế 10 hoặc 13 chữ số
  """
  if (len(maso) == 10 or len(maso) == 14): 
    if maso[0:10].isnumeric() and maso[-3:].isnumeric():
      return maso
  return False
      
class ThongTinDoanhNghiep:
  def __init__(self,masothue:str):
    # Khoi tao Session
    self.s = requests.Session()
    r = self.s.get("https://dichvuthongtin.dkkd.gov.vn/inf/default.aspx",verify=False)

    defaultPage = BeautifulSoup(r.text,'lxml')
    self.hdParameter = defaultPage.find("input",id="ctl00_hdParameter")
    self.nonceKeyFld = defaultPage.find("input",id="ctl00_nonceKeyFld")
    self.EVENTVALIDATION = defaultPage.find("input",id="__EVENTVALIDATION")
    self.masothue = masothue

  def GetSearchID(self):
    """
    Get Search ID from dichvuthongtin.dkkd.gov.vn.
    This ID will be used for many post requests
    """
    maso = format(self.masothue)
    if not(maso):
      raise RuntimeError("Mã số thuế không đúng: "+self.masothue)
    self.masothue = maso

    data = dict()
    data['h'] = self.hdParameter["value"]
    data["searchField"] = self.masothue
    url = "https://dichvuthongtin.dkkd.gov.vn/inf/Public/Srv.aspx/GetSearch"
    header = dict()
    header["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
    header["Referer"] = "https://dichvuthongtin.dkkd.gov.vn/inf/default.aspx"
    searchResult = self.s.post(url,json = data,headers=header,verify=False)
    if searchResult.status_code == 200:
      thongtincongty = searchResult.json()
      if 'd' in thongtincongty.keys():
        danhsach = thongtincongty['d']
      try:
        for ketqua in danhsach:
          if ketqua['Enterprise_Gdt_Code'] == self.masothue:
            return ketqua['Id']
        raise RuntimeError("Không tìm thấy mã số thuế "+ self.masothue)
      except:
        raise RuntimeError("Không tìm thấy mã số thuế "+ self.masothue)
    raise RuntimeError("Quá trình lấy ID thất bại! Mã thuế sai hoặc mạng có vấn đề!")

  def getInfo(self):

    redirectedPage = "https://dichvuthongtin.dkkd.gov.vn/inf/default.aspx"

    # form parameters (need all of them)
    ctl00 = dict()
    ctl00["__EVENTTARGET"]=""
    ctl00["__EVENTARGUMENT"]="" 
    ctl00["__VIEWSTATE"]=""
    ctl00["__EVENTVALIDATION"] = self.EVENTVALIDATION["value"]
    ctl00["ctl00$nonceKeyFld"]=""
    ctl00["ctl00$hdParameter"] = self.hdParameter["value"]
    ctl00["ctl00$FldSearch"] = self.masothue
    try:
      ctl00["ctl00$FldSearchID"] = self.GetSearchID()
    except Exception as e:
      print(e)
      return {'code':self.masothue, 'error':True}
    ctl00["ctl00$btnSearch"] =  "Tìm kiếm >>"
    ctl00["ctl00$searchtype"] =  1

    f = self.s.post(redirectedPage,data=ctl00,allow_redirects=False,verify=False)
    if f.status_code == 302:
      url = "https://dichvuthongtin.dkkd.gov.vn"+f.headers["Location"]
      r = self.s.get(url)
      infoPage = BeautifulSoup(r.text,"lxml")
      info = dict()
      info["id"] = ctl00["ctl00$FldSearchID"]

      # Check if every object is existed to avoid error
      vietnameseName = infoPage.find("span",id="ctl00_C_NAMEFld")
      if vietnameseName:
        info["tentiengViet"] = vietnameseName.get_text().strip()
      foreignName = infoPage.find("span",id="ctl00_C_NAME_FFld")
      if foreignName:
        info["tennuocngoai"] = foreignName.get_text().strip()
      status = infoPage.find("span",id="ctl00_C_STATUSNAMEFld")
      if status:
        info["tinhtranghoatdong"] = status.get_text().strip()
      code = infoPage.find("span",id="ctl00_C_ENTERPRISE_GDT_CODEFld")
      if code:
        info["masothue"] = code.get_text().strip()
      loaihinh = infoPage.find("span",id="ctl00_C_ENTERPRISE_TYPEFld")
      if loaihinh:
        info["loaihinh"] = loaihinh.get_text().strip()
      foundDate = infoPage.find("span",id="ctl00_C_FOUNDING_DATE")
      if foundDate:
        info["ngaythanhlap"] = foundDate.get_text().strip()
      address = infoPage.find("span",id="ctl00_C_HO_ADDRESS")
      if address:
        info["diachi"] = address.get_text().strip()
      
      #Get registered business activities
      PageIndex = 0
      nganh = dict()

      bang = infoPage.find("div",id="i_DataMain").find("table").find_all("tr")[1]
      first = bang.find_all("td")[1].get_text().strip()
      nganh.update({"default":first})
      loadmoreUrl = "https://dichvuthongtin.dkkd.gov.vn/inf/Forms/Searches/EnterpriseInfo.aspx/LoadMore"
      while True:
        r = self.s.post(loadmoreUrl,json={'PageIndex':PageIndex,'EnterpriseID':info["id"]},headers={'Referer':url})
        if r.status_code == 200:
          rows = r.json()['d']
          if len(rows) > 0:
            rows = BeautifulSoup(rows,'lxml')
            tr = rows.find_all("tr")
            nganh.update({row.contents[0].string:\
              "\n".join([div.string if div.string is not None else ''\
              for div in row.contents[1].contents]) for row in tr})
          else:
            break
        else:
          break
        PageIndex+=1
      info['nganh'] = nganh
      return info