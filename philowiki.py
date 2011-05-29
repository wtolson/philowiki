#!/usr/bin/env python

import sys
import urllib
import httplib2
from lxml import etree
import re
import cPickle
import time

class philowiki(object):
  __shared_state = {}

  def __init__(self):
    self.__dict__ = self.__shared_state
    if not hasattr(self, "_titleCache"):
      self._setup()

  def _setup(self):
    self.EXP_TIME = 60*60
    self._h = httplib2.Http()
    self._urlTitle = re.compile(r"^http://en.wikipedia.org/wiki/([^:]*)$")
    self._headers = {"User-Agent": "PhiloWiki/1.0"}
    self._preTextCache = {}
    self._titleCache = {}
    try:
      with open(".cache", "r") as cacheFile:
        self._titleCache = cPickle.load(cacheFile) 
    except:
      pass

  def saveTitleCache(self):
    try:
      with open(".cache", "w") as cacheFile:
        now = time.time()
        for title in self._titleCache:
          if self._titleCache[title][1] < now:
            del self._titleCache[title]
        cPickle.dump(self._titleCache, cacheFile)
        return True
    except:
      return False

  
  def _getPage(self, title, parse=True):
    url = "http://en.wikipedia.org/w/index.php?action=render&title=%s" % (title)
    resp, content = self._h.request(url, headers=self._headers)
    if parse:
      return etree.fromstring("<root>%s</root>" % (content))
    else:
      return (resp, content)

  def _findFirst(self, ele, level=0):
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
      title = self._urlTitle.findall(ele.attrib["href"])
      if len(title) and not self._inParenth(ele):
        return title[0].split("#")[0].split("?")[0]
      else:
        return

    #print level*"> " + ele.tag#, ele.attrib

    for child in ele.iterchildren(tag=etree.Element):
      result = self._findFirst(child, level+1)
      if result:
        return result

  def _inParenth(self, ele):
    text = self._getPreText(ele)
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

  def _getPreText(self, ele):
    if ele not in self._preTextCache:
      parent = ele.getparent()
      text = []
      if parent is not None:
        text.append(self._getPreText(parent))
        if parent.text:
          text.append(parent.text)
        for child in parent.iterchildren():
          if child is ele:
            break
          for t in child.itertext():
            text.append(t)
          if child.tail:
            text.append(child.tail)
      
      self._preTextCache[ele] = "".join(text)
        
    return self._preTextCache[ele]

  def getNextTitle(self, title):
    if title not in self._titleCache or self._titleCache[title][1] < time.time():
      self._preTextCache = {}
      root = self._getPage(title)
      self._titleCache[title] = (self._findFirst(root), time.time() + self.EXP_TIME) # Hour experation

    return self._titleCache[title][0]

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.saveTitleCache()

def main():
  if (len(sys.argv) <= 1):
    raise Error("Please specify a start page")
    return 1
  
  with philowiki() as pw:
    title = urllib.quote("_".join(sys.argv[1:]))
    
    count = 0
    history = []
    while title != "Philosophy":
      print urllib.unquote(title.replace("_", " ")), "->",
      history.append(title)
      title = pw.getNextTitle(title)
      print title
      if title is None:
        print "Found dead end :("
        return 1
      if title in history:
        print "Found infinate loop!"
        return 1
      count += 1

    print "Found Philosophy in %d steps!" % (count)

  return 0

if __name__ == '__main__':
  main()
