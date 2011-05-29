#!/usr/bin/env python

import sys
import urllib
import httplib2
from lxml import etree
import re
import cPickle
import time

#class philowiki

_titleCache = {}
try:
  with open(".cache", "r") as cacheFile:
    _titleCache = cPickle.load(cacheFile) 
except:
  pass

def saveTitleCache():
  try:
    with open(".cache", "w") as cacheFile:
      now = time.time()
      for title in _titleCache:
        if _titleCache[title][1] < now:
          del _titleCache[title]
      cPickle.dump(_titleCache, cacheFile)
  except:
    pass


_h = httplib2.Http()
_urlTitle = re.compile(r"^http://en.wikipedia.org/wiki/([^:]*)$")
_headers = {"User-Agent": "PhiloWiki/1.0"}

def getPage(title):
  url = "http://en.wikipedia.org/w/index.php?action=render&title=%s" % (title)
  resp, content = _h.request(url, headers=_headers)
  return etree.fromstring("<root>%s</root>" % (content))

def findFirst(ele, level=0):
  for item in ["table", "i"]:
    if ele.tag == item:
      return

  if "class" in ele.attrib:
    classes = ele.attrib["class"].split(" ")
    for item in ["dablink", "tright", "rellink", "seealso"]:
      if item in classes:
        return

  if "id" in ele.attrib:
    id = ele.attrib["id"]
    for item in ["coordinates"]:
      if item == id:
        return

  if ele.tag == "a":
    title = _urlTitle.findall(ele.attrib["href"])
    if len(title) and not inParenth(ele):
      return title[0].split("#")[0].split("?")[0]
    else:
      return

  #print level*"> " + ele.tag#, ele.attrib

  for child in ele.iterchildren(tag=etree.Element):
    result = findFirst(child, level+1)
    if result:
      return result

def inParenth(ele):
  text = getPreText(ele)
  count = 0
  for char in reversed(text):
    if char == "(":
      if count:
        count -= 1
      else:
        return True
    elif char == ")":
      count += 1
  return False

_preTextCache = {}
def getPreText(ele):
  if ele not in _preTextCache:
    parent = ele.getparent()
    text = []
    if parent is not None:
      text.append(getPreText(parent))
      if parent.text:
        text.append(parent.text)
      for child in parent.iterchildren():
        if child is ele:
          break
        for t in child.itertext():
          text.append(t)
        if child.tail:
          text.append(child.tail)
    
    _preTextCache[ele] = "".join(text)
      
  return _preTextCache[ele]

def getNextTitle(title):
  if title not in _titleCache or _titleCache[title][1] < time.time():
    _preTextCache = {}
    root = getPage(title)
    _titleCache[title] = (findFirst(root), time.time() + 60*60) # Hour experation

  return _titleCache[title][0]

def main():
  if (len(sys.argv) <= 1):
    raise Error("Please specify a start page")
    return 1
  
  title = urllib.quote("_".join(sys.argv[1:]))
  
  count = 0
  history = []
  while title != "Philosophy":
    print urllib.unquote(title.replace("_", " ")), "->",
    history.append(title)
    title = getNextTitle(title)
    print title
    if title is None:
      print "Found dead end :("
      return 1
    if title in history:
      print "Found infinate loop!"
      return 1
    count += 1

  print "Found Philosophy in %d steps!" % (count)
  saveTitleCache()

  return 0

if __name__ == '__main__':
  main()
