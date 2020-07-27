from bs4 import BeautifulSoup

text = "<tr><td>7410</td><td><div>Hoạt động thiết kế chuyên dụng</div><div>chi tiết: Thiết kế thi công cảnh quan sân vườn; Thiết kế hòn non bộ, dòng suối, thác nước </div></td></tr>"

page = BeautifulSoup(text,"lxml")

tr = page.find_all("tr")

print({row.contents[0].string:"\n".join([div.string for div in row.contents[1].contents]) for row in tr})