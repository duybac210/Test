import requests, re
s = requests.Session()
r = s.get('http://127.0.0.1:8000/dang-nhap/')
csrf = r.cookies['csrftoken']
r2 = s.post('http://127.0.0.1:8000/dang-nhap/', data={'username':'098765', 'password':'123', 'csrfmiddlewaretoken': csrf})
r3 = s.get('http://127.0.0.1:8000/tao-van-ban/')
select_html = r3.text.split('id="loai-van-ban"')[1].split('</select>')[0]
options = re.findall(r'<option value="([^"]+)">([^<]+)</option>', select_html)
print([opt[0] for opt in options])
