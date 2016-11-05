import re, requests
from fuzzywuzzy import fuzz
from PIL import Image
from io import BytesIO

class html_sniffer: 
    def __init__(self,content, url):
        self.title = ""
        self.image = ""
        self.price = ""
        self.btn = ""
        self.debug = False
        self.search_term = "Scraping. Betch."
        debug_log_name = "scraper_log"
        if self.debug:
          self.debug_log = open(debug_log_name,'w+')
        self.root_url = url.split(".com")[0] + ".com"
        self.content = content
        self.refined_html = ""
        self.pattern = []
          
    def price_title_image(self):
        self.btn = self.check_buy_button()
        if self.btn == False:
            return False
        else:
            btn = self.btn
        btn_index = self.find_lines(btn,self.content)[0]
        title, title_index = self.find_header_lines(btn_index, self.content)
        self.refine_html(btn_index,title_index,self.content)
        dollas = self.find_dolla_lines(self.refined_html)
        price = self.price_is_right(dollas[1])
        if self.debug:
            self.debug_log.write("\n Button index: "+ str(btn_index)+" \n")
        if self.check_og(self.content):
          image = self.get_og_image(self.content)
        else:
          image = self.find_image(self.content,btn_index)
        return price, title, image
      
  # truncate HTML based on location of buy button
    def refine_html(self,btn_index,header_index,html):
        lines = html.split("\n")
        index = int(btn_index)
        new_html = ""
        one_line_offset = 100
        start = header_index
        end = index 
        if btn_index == header_index:
            #print(self.btn)
            for line in lines:
                if self.btn in line:
                    self.refined_html = line
                    return
        for line in lines[start:end]:
            new_html += line+"\n"
        self.refined_html = new_html

  # Conducts fuzzy search on a provided string (line) for a 
  # search term and returns a match score 
    def match_score(self,search_term,string_to_search):
        if "&#" in string_to_search:
          string_to_search = re.sub('&#(.*?);',"",string_to_search).replace("  "," ")
        score = fuzz.ratio(search_term,string_to_search)
        return score
      
  # Looks through the provided html for any of the pre-established
  # buy buttons, and then returns the first button it finds
    def check_buy_button(self):
        html_to_search = self.content
        buttons = ['Add To Cart','Add to Cart','Add to cart','ADD TO CART','Add to Bag','Add to Shopping Bag','Buy Now',"Add To Basket"]
        for button in buttons:
            rexp = re.compile(re.escape(button) + '(.*?)<\/button>',re.DOTALL)
            if rexp.search(html_to_search) is not None:
                return button
        return False
  
    # Searches a provided html for a given regex and returns all the 
    # lines where that regex occurs
    def find_lines(self,search_term,html_to_search):
      lines = []
      for m in re.finditer(search_term,html_to_search):
        start = m.start()
        lineno = html_to_search.count('\n',0,start)
        lines.append(lineno)
      return lines

  # Looks through provided html and returns whether or not there's
  # any open graph tags in the html
    def check_og(self, html_to_search):
      return '\"og:' in html_to_search
  
    def get_og_image(self, html_to_search):
      image = re.findall('og:image\"\ content=\"(.*?)\"',html_to_search)
      return image
  
    def get_og_title(self, html_to_search):
      title = re.findall('og:title\"\ content=\"(.*?)\"',html_to_search)
      return title

    def min_diff_index_values(self,index, array_to_diff,value_array):
        min_diff=10000
        min_index=0
        v = 0
        for i in array_to_diff:
            diff = int(index)-int(i)
            if diff == 0:
                min_index = index
                val = value_array[array_to_diff.index(min_index)]
                return min_index, val
            elif len(array_to_diff)==1:
                return array_to_diff[0], value_array[0]
            elif diff < 0:
                val = value_array[array_to_diff.index(min_index)]
                return min_index, val
            elif v == len(value_array)-1:
                val = value_array[array_to_diff.index(min_index)]
                return min_index, val
            v += 1
            if diff < min_diff:
                min_diff=diff
                min_index = i
       
    def btn_num(self,btn):
        btns = re.findall(btn,self.content)
        return len(btns)
     

    def price_is_right(self,prices):
        price_set = list(set(prices))
        for price in price_set:
            if '.' not in price:
                price_set.remove(price)
                #print(price_set)
            if len(price_set) == 1:
                return price_set[0]
            elif len(price_set) ==2:
                price_set = [float(price.replace(',','')) for price in price_set]
                if min(price_set)/max(price_set) > .5: 	      
                    return min(price_set)
                else:
                    return max(price_set)
            else:
                lag = 0.1
                float_set = [float(price.replace(',','')) for price in price_set]
                for p in float_set:
                    for c in [x for x in float_set if x != p]:
                        if min(c,p)/max(c,p) > .5: 	      
                            return '%.2f' % min(p,c)


  # looks through provided html for a price regular expression
  # returns lines_numbers, dollar_values
    def find_dolla_lines(self, html_to_search):
    #consider looking for dictionary pattern i.e 'price': "210.00"
        lines = []
        values = []
        dolla_search = r'\$((?:\d+,)?\d+(?:\.\d{2})?)'
        for m in re.finditer(dolla_search,html_to_search):
            start = m.start()
            lineno = html_to_search.count('\n',0,start)
            if len(m.group(1))> 1:
                lines.append(lineno)
                values.append(m.group(1))
        lag = 1
        for dex in lines:
            if dex == lag:
                lag_val = float(values[lines.index(lag)].replace(',',''))
                dex_val = float(values[lines.index(dex)].replace(',',''))
            lag = dex
        if self.debug:
            for l,v in zip(lines,values):
                self.debug_log.write("line "+str(l) +",value "+ str(v)+"  ")
        return (lines,values)

  # takes in an image url and returns the width, height dimensions
  # of the image. PIL Image requires pip install Pillow
    def get_image_size(self,image_url):
      try:
        data = requests.get(image_url).content
        im = Image.open(BytesIO(data))
        return im.size
      except:
     #   print("failed to load url trying to get image size \n" +image_url)
        return (1,1)
     
    def find_big_image(self,urls):
        for url in urls:
            try:
                width, height = self.get_image_size(url)
                if int(width) > 200 and int(height) > 200:
                    return url 
            except:
                print("effffed")
                print(url)

  # searches html for images and returns their line numbers
    def find_image_lines(self):
      html_to_search = self.content
      lines = []
      #values = []
      dolla_search = 'src=(\"|\')(.*?)(\"|\')'
      for m in re.finditer(dolla_search,html_to_search):
        start = m.start()
        lineno = html_to_search.count('\n',0,start)
        lines.append(lineno)
       # value=m.group(0).replace("src=","").replace("\"","").replace("\'","")
        #values.append(value)
      return lines #, values
  
    def find_btn_lines(self):
      html_to_search = self.content
      lines = []
      #values = []
      dolla_search = re.escape(self.btn) + '<\/'
      for m in re.finditer(dolla_search,html_to_search):
        start = m.start()
        lineno = html_to_search.count('\n',0,start)
        lines.append(lineno)
      return lines #, values

  # takes the line numbers of a characteristic for a potential pattern and
  # returns the line # start and line # end of a pattern, as well as diff if it occurs
  # E.g. input the line numbers of images to see if there's a pattern
    def find_line_pattern(self, line_index_array):
      last = 0
      last_diff = 0
      num = 0
      pattern_diffs = []
      pattern_lines = []
      pattern_indexes = []
      for dex in line_index_array:
          diff = int(dex) - last
          if diff > 5 and diff < last_diff + 5 and diff > last_diff -5:
                pattern_diffs.append(diff)
                pattern_lines.append(last)
          last_diff = diff
          last = dex
      total = len(pattern_diffs)
    #print(pattern_diffs)
      if total > 5:
          avg = sum(pattern_diffs)/total
          limit = float(avg)*.75
          num = 0
          for p in pattern_diffs:
              if p < avg + limit and p > avg - limit:
                  pattern_indexes.append(pattern_lines[num])
              num += 1
        #print(pattern_indexes)
          pattern_range = pattern_indexes[0], pattern_indexes[len(pattern_indexes)-1]
          self.pattern = pattern_range
          return pattern_range 

    def pattern_fuzz_finder(self, start_pattern_line, end_pattern_line):
      html_to_search = self.content
      lines = html_to_search.split("\n")
      html_pattern_section = ""
      for line in lines[start_pattern_line:end_pattern_line]:
        html_pattern_section += line  
      hrefs = re.findall('href=(\"|\')(.*?)(\"|\')',html_pattern_section.encode('ascii','ignore'))
      #getting rid of random anchors and quotes 
      good_hrefs = []
      for ref in hrefs:
        if len(str(ref[1])) > 10:
            good_hrefs.append(ref)
      return self.interpret_url(good_hrefs[0])
  
    def interpret_url(self,value):
        if len(value) > 1:
            for val in value:
                if len(val) > 10:
                      value = val
        try:
          if value[0] == "/" and value[1] == "/":
            url = "http:"+ value        
            return url
          elif value[0] == "/" and value[1] != "/":
            url = self.root_url + value
            return url
          elif 'http:' not in value:
            url = self.root_url +"/"+ value
            return url
          else:
              return value
        except :
            return value
  
    def find_image(self,html_to_search,base_index):
      lines = []
      values = []
      dolla_search = 'src=(\"|\')(.*?)(\"|\')'
      for m in re.finditer(dolla_search,html_to_search):
        start = m.start()
        lineno = html_to_search.count('\n',0,start)
        lines.append(lineno)
        value=m.group(0).replace("src=","").replace("\"","").replace("\'","")
        try:
          if value[0] == "/" and value[1] == "/":
            url = "http:"+ value        
            values.append(url)
          elif value[0] == "/" and value[1] != "/":
            url = self.root_url + value
            values.append(url)
          elif 'http:' not in value:
            url = self.root_url +"/"+ value
            values.append(url)
          else :
            values.append(value)
        except:
            if self.debug:
              self.debug_log.write(value +"\n is ate upppp")
            values.append("none")
      start_index = self.min_diff_index_values(base_index,lines,values)
      dim = self.get_image_size(start_index[1])
      if int(dim[0]) > 200 and int(dim[1])> 200:
        return start_index[1]
      else:
        line_start_index = lines.index(start_index[0])
        likely_image_urls = values[line_start_index-10:line_start_index +10]
        if self.debug:
            self.debug_log.write("\n Here are the most likely urls \n")
            self.debug_log.write("index of line start: "+str(start_index[0]) +"\n")
            self.debug_log.write("value of line start: "+str(start_index[1]) +"\n")
            for url in likely_image_urls:
                self.debug_log.write(url+"\n")
        image = self.find_big_image(list(reversed(likely_image_urls)))
        return image


    def find_header_lines(self,btn_index,html_to_search):
          vals_above_btn = 10 
          header_search = '<(h[1-6](.*?)>)(.*?)<\/h[1-6]>'
          span_search = '<(span(.*?)>)(.*?)<\/span>'
          title_match = re.search('<title>(.*?)<\/title>',html_to_search,re.DOTALL)
          page_title = title_match.group(1)[:20].replace('\n','')
          def vals_lines_search(reg_search):
                  lines = []
                  values = []
                  for m in re.finditer(reg_search,html_to_search,re.DOTALL):
                    start = m.start()
                    lineno = html_to_search.count('\n',0,start)
                    if int(lineno) <= int(btn_index):
                      lines.append(lineno)
                      values.append(m.group(3))
                    else:
                      break
                  return lines, values
          hlines, hvals = vals_lines_search(header_search)
          slines, svals = vals_lines_search(span_search)
          lines = []
          values = []
          for hline, hval, sline,sval in zip(hlines[-vals_above_btn:],hvals[-vals_above_btn:],slines[-vals_above_btn:],svals[-vals_above_btn:]):
            lines.append(hline)
            lines.append(sline)
            values.append(hval)
            values.append(sval)
          clean_values = []
          high_score=0
          high_score_line = 0
          high_score_val =  ""
          for dval,line in zip(values,lines):
            cval = re.sub('<(.*?)>','',dval)
            if "\n" in cval:
              clean_values.append(cval.replace("\n","").replace("\t",""))
            else:
                clean_values.append(cval)
            score = self.match_score(page_title,cval)	
            if score > high_score:
              high_score = score
              high_score_line = line
              high_score_val = str(cval)
          if high_score < 30:
            high_score_val = page_title
          #print('score:  '+ str(high_score))
          return (high_score_val,high_score_line)

