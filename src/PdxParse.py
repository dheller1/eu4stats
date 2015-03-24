# -*- encoding: utf-8 -*-
import csv, re, sys, types

class Node:
   DateRegex = re.compile('^\d{1,4}\.\d{1,2}\.\d{1,2}$') # finds all '1499.6.13', '1000.1.1', '1.1.1' date strings
   
   def __init__(self, name, id = -1, level = 0, data = None):
      self.id = id
      self.level = level
      self.name = name
      self.data = data
      self.parent = None
      self.children = {}
      self.numChildren = 0
   
   def __str__(self):
      indent = "   " * self.level
      s = ""
      s += indent + "'%s' : {\n" % self.name
      s += indent + "         id=%d, level=%d, numChildren=%d,\n" % (self.id, self.level, self.numChildren)
      if self.data is not None:
         s += indent + "         data(%s)=%s\n" % (type(self.data), self.data)
      if self.numChildren > 0:
         s += indent + "         children:\n"
         for key,val in self.children.items():
            s += str(val)
      s += indent + "       }\n"
      
      return s
      
   def addChild(self, child):
      child.level = self.level + 1
      child.parent = self
      child.id = len(self.children.keys())
      
      self.numChildren += 1
      
      if child.name in self.children:
         self.children[child.name+str(child.id)] = child
      else: self.children[child.name] = child
      
      return child
   
   # return all '1444.12.31'-style child nodes
   # where the date is between start (without the
   # exact start date; unless includeStart==True)
   # and end (including the end date)
   def getDateChilds(self, start='0.0.0', end='9999.99.99', includeStart = False):
      # find all date children
      dateChilds = []
      for k in self.children.keys():
         if Node.DateRegex.match(k) != None:
            dateChilds.append(self.children[k])
      
      # sort by date
      dateChilds.sort(key=lambda c: c.name)
      
      # filter between start and end date
      filteredChilds = []
      for c in dateChilds:
         if start < c.name <= end or (includeStart and start <= c.name <= end):
            filteredChilds.append(c)
      
      # return result
      return filteredChilds
   
   def hierarchyStr(self):
      ancestors = []
      p = self.parent
      while p is not None:
         ancestors.append(p.name)
         p = p.parent
      
      ancestors.reverse()
      print ancestors
      if len(ancestors)>0:
         s = "->".join(ancestors + [self.name,])
      else:
         s = self.name
         
      return s

class Parser:
   def __init__(self, file = None):
      self.file = file
      
   def read2(self):
      if not self.file: raise ValueError("No file opened!")
      
      root = Node(id=0, name="root", level=0)
      curNode = root
      
      with open(self.file, 'rU') as f:
         lines = f.readlines()
         
         uncommentedLines = []
         
         #======================================================================
         # cut all comments and skip completely blank lines
         #======================================================================
         for line in lines:
            if line.count('#')>0:
               if line.startswith('#'):
                  continue
               
               # check if it's really a comment or within a string
               inString = False
               idx = 0
               for c in line:
                  if c == '"': inString = not inString
                  if c == '#' and not inString:
                     if len(line[:idx].strip())>0:
                        uncommentedLines.append(line[:idx]) 
                        break
                  idx += 1
            else:
               if len(line.strip()) > 0:
                  uncommentedLines.append(line)
               
         del lines
         
         inBlockMode = False
         lineNum = -1
         
         for line in uncommentedLines:
            
            lineNum += 1
            #======================================================================
            # Case 0: still parsing a block opened beforehand
            #
            #   criteria:
            #   * inBlockMode == True
            #======================================================================
            if inBlockMode:
               idx = 0
               for c in line:
                  block += c
                  
                  if(c=='{'): numBracketsOpen += 1
                  if(c=='}'):
                     numBracketsOpen -= 1
                     
                     if numBracketsOpen == 0: # end of block
                        inBlockMode = False
                        
                        # cut last } character from block and parse it
                        block = block[:-1]
                        self._ParseBlock(block, name, parentNode=curNode)
                        
                        # handle rest of line by prepending it to the next line
                        if len(line[idx+1:].strip()) > 0:
                           uncommentedLines[lineNum + 1] = line[idx+1:] + ' ' + uncommentedLines[lineNum + 1]
                  
                  idx += 1
               
               continue
            
            #======================================================================
            # Case 1: ' val = var ' line
            #   variations:
            #      ' val = "var" '
            #      ' "val #0" = var '
            #      ' val = var1 var2 var3 ' --- NOT IMPLEMENTED -- (does it really occur?)
            #
            #   criteria:
            #   * exactly one equal sign =
            #   * no curly brackets {}
            #======================================================================
            elif line.count('=') == 1 and line.count('{') == line.count('}') == 0:
               name, value = line.split('=')[0].strip(), line.split('=')[1].strip()
               
               # name might be enclosed in " quotation marks, in this case, strip them
               if name.count('"') == 2:
                  name = name.replace('"','')
               
               # value might be a list of values
               if value.count('"') < 2 and value.count(' ')>0:
                  raise BaseException("Not yet implemented!")
               
               # value might be a " quotation mark enclosed string, in this case, strip them
               elif value.count('"') == 2:
                  value = value.replace('"','')
               
               # value might be an integer, cast to Int
               elif value.isdigit():
                  value = int(value)
                  
               # data okay, generate child node
               curNode.addChild(Node(name=name, data=value))
               
             
            #===================================================================
            # Case 1.5: multiple assignments ' val1 = var1 val2 = var2 ' line
            #
            #   criteria:
            #   * number of = equal signs > 1
            #   * no curly brackets
            #===================================================================
            elif line.count('=') > 1 and line.count('{') == line.count('}') == 0:
               numAssignments = line.count('=')
               
               # make sure split() isolates all equal signs
               line2 = line.replace('=',' = ')
               
               # split words
               words = csv.reader([line2,], delimiter=' ').next()
               
               # remove empty words
               while '' in words: words.remove('')
               
               assert(len(words)%3 == 0)
               
               # add child node for each assignment
               wordsParsed = 0
               childTextCounter = 0
               for word in words:
                  if (wordsParsed%3) == 0: # name
                     name = word
                  elif(wordsParsed%3) == 1: # equals sign
                     assert(word=='=')
                  elif(wordsParsed%3) == 2: # data, finished parsing one assignment
                     data = word
                     if(data.isdigit()): data = int(word)
                     child = curNode.addChild(Node(name=name, data=data))
                     
                  wordsParsed += 1
               
            #======================================================================
            # Case 2: ' val = { ANYTHING } ' line
            #   variations:
            #     - none
            #
            #   criteria:
            #   * at least one = equals sign
            #   * at least one opened and one closed curly bracket, equal count of
            #     opened and closed curly brackets
            #   * (stripped) assignment operand starts with opening curly bracket
            #   * (stripped) line ends with } closing curly bracket
            #   * ANYTHING can contain other blocks, brackets, assignments, etc.
            #======================================================================
            elif line.count('=') > 0 and line.count('{')>0 and line.count('}')>0 and line.count('{') == line.count('}') \
               and line.split('=')[1].strip().startswith('{') and line.strip().endswith('}'):
               
               nonBlockText = ""
               blockText = ""
               insideBlock = False
               for c in line:
                  if c=='{' and not insideBlock:
                     nonBlockText += '{'
                     insideBlock = True
                  elif c=='}' and insideBlock:
                     nonBlockText += '}'
                     insideBlock = False
                  elif insideBlock:
                     blockText += c
                  else:
                     nonBlockText += c
                     
               name = nonBlockText.split('=')[0].strip()
               self._ParseBlock(blockText, name, parentNode=curNode)
               
            #======================================================================
            # Case 3: ' val = { ANYTHING \n ANYTHING ... \n ANYTHING } '
            #   variations:
            #     - none
            #
            #   criteria:
            #   * at least one = equals sign
            #   * at least one opened curly bracket to start, more opened than closed curly brackets
            #   * parse block until closed curly bracket
            #   * (stripped) assignment operand starts with opening curly bracket
            #   * (stripped) line ends with } closing curly bracket
            #   * ANYTHING can contain other blocks, brackets, assignments, etc.
            #======================================================================
            elif line.count('=') > 0 and line.count('{') > 0 and line.count('{')>line.count('}') \
               and line.split('=')[1].strip().startswith('{'):
               
               
               nonBlockText = ""
               blockText = ""
               insideBlock = False
               for c in line:
                  if c=='{' and not insideBlock:
                     nonBlockText += '{'
                     insideBlock = True
                  # block won't be closed in this line, no need to check for '}' characters
                  elif insideBlock:
                     blockText += c
                  else:
                     nonBlockText += c
                     
               name = nonBlockText.split('=')[0].strip()
               
               block = blockText
               
               numBracketsOpen = 0
               inBlockMode = True
               
               for c in line:
                  if(c=='{'): numBracketsOpen += 1
                  if(c=='}'): numBracketsOpen -= 1
               
               continue
            
            #===================================================================
            # Case 5: EXCEPTIONS
            #===================================================================
            else:
               raise BaseException("Invalid line %d: '%s', file %s" % (uncommentedLines.index(line), line, self.file))
            
      return root
               
   def _ParseBlock(self, text, name, parentNode=None):
      if parentNode:
         node = parentNode.addChild(Node(name=name))
      else:
         node = Node(name=name)
         
      if len(text)==0:
         return node
      
      # Parse block string
      
      #=============================================================
      # Case 1:
      #  e.g. 123 456 789
      #       101 112 131
      #       151 617 181
      #  pure data
      #
      #  criteria:
      #   - no child nodes i.e. no curly brackets
      #   - no assignments i.e. no equal signs
      #   - one or multiple lines
      #=============================================================
      if text.count('{') == text.count('}') == text.count('=') == 0:
         # separate words in string using CSV-reader to split by blanks without splitting inside of
         # "" quotation mark-escaped strings
         
         # first, replace all whitespaces with blanks
         text2 = text.replace('\t',' ').replace('\n',' ').replace('\r','')
         
         # now, split the words
         words = csv.reader([text2,], delimiter=' ').next()
         
         # drop empty words
         while '' in words: words.remove('')
         
         # check if words could be integers
         allInt = True
         for w in words:
            if not w.isdigit():
               allInt = False
               break
            
         if allInt:
            words = [int(w) for w in words]
            
         # set as data for the node
         node.data = words
         
         # done
         return node
      
      #=============================================================
      # Case 2:
      #  e.g. revolt = { type = pretender_rebels size = 1 leader = "Karl Knutsson Bonde" } controller = REB
      #  
      #  text contains assignments and child nodes
      #
      #  criteria:
      #   - at least one equals sign or curly bracket
      #=============================================================
      else:
         # first, crop all text in between {} curly brackets and store it in a list where further
         # child nodes will be parsed from.
         
         childText = []
         
         croppedText = ""
         insideBrackets = False
                  
         for c in text:
            if c=='{' and not insideBrackets:
               insideBrackets = True
               curChildText = ""
               croppedText += "{" # store the '{}' pair in the cropped text to find childText locations later
               
            elif c=='}' and insideBrackets:
               insideBrackets = False
               childText.append(curChildText)
               croppedText += "}" # store the '{}' pair in the cropped text to find childText locations later
               
            elif insideBrackets:
               curChildText += c
               
            else: # not inside brackets
               croppedText += c
               
         assert(croppedText.count('{}') == len(childText))
         
         # split 'name = data' assignment pairs
         # first, replace all whitespaces with blanks
         croppedText = croppedText.replace('\t',' ').replace('\n',' ').replace('\r','')
         
         # also, make sure that every = equal sign is surrounded by whitespaces to be
         # able to be separated by split()
         croppedText = croppedText.replace('=', ' = ')
         
         # now, split the words
         words = csv.reader([croppedText,], delimiter=' ').next()
         
         # remove empty words
         while '' in words: words.remove('')
         
         assert(len(words)%3 == 0)
         
         # add child node for each assignment
         wordsParsed = 0
         childTextCounter = 0
         for word in words:
            if (wordsParsed%3) == 0: # name
               name = word
            elif(wordsParsed%3) == 1: # equals sign
               assert(word=='=')
            elif(wordsParsed%3) == 2: # data, finished parsing one assignment
               data = word
               if(data.isdigit()): data = int(word)
               
               # check if a 'full' child node must be generated recursively
               if data == '{}':
                  child = self._ParseBlock(text=childText[childTextCounter], name=name, parentNode=node)
                  node.addChild(child)
                  childTextCounter += 1
               else: #if data != '{}':
                  child = node.addChild(Node(name=name, data=data))
               
            wordsParsed += 1
            
         return node
            
   def read(self):
      if not self.file: raise ValueError("No file opened!")
      
      with open(self.file, 'r') as f:
         lines = f.read().splitlines()
      
      root = Node(id=0, name="root", level=0)

      curNode = root
      blocksOpened = 0
      
      for line in lines:
         if curNode == None:
            raise BaseException("WTF! (file=%s)" % self.file)
         
         # strip whitespaces
         l = line.strip()
         
         # skip comments and blank lines
         if len(l) == 0 or l.startswith('#'):
            continue
         
         # strip everything after a '#', except if it is within "quotation marks"
         if l.count('#') >= 1:
            inString = False
            idx = 0
            for c in l:
               if c=='"': inString = not inString
               if c=='#' and not inString:
                  l = l[:idx]
                  break
               idx += 1
         
         # assignment?
         if l.count('=') > 1:
            sys.stdout.write('Warning (line ignored)')
            print("Invalid line - multiple '=' assignments!\nline: '"+l+"'\n(file "+self.file+")")
            continue
         
         elif l.count('=') == 1:
            var, val = l.split('=')[0].strip().replace('"',''), l.split('=')[1].strip().replace('"','')
             
            # check if value is valid (no { block opened, not empty)
            if len(val) > 0 and val.count('{') == 0 and val.count('}') == 0:
               if val.isdigit():
                  val = int(val)
                  
               curNode.addChild(Node(name=var, data=val))
            
            # single line block?
            elif val.count('{') == val.count('}'):
               strpVal = val.replace('{','').replace('}','').strip() # strip blanks and brackets
               
               if strpVal.count('"') > 0: # probably a string, strip the quotation marks
                  strpVal = strpVal.replace('"', '')
               else:
                  spl = strpVal.split()
                  if len(spl) > 1: # probably a list, try to convert to integers
                     li = []
                     for itm in spl:
                        if itm.isdigit(): li.append(int(itm)) # IntList
                        else: li.append(itm)                  # StringList
                     strpVal = li
               
               curNode.addChild(Node(name=var, data=strpVal))
            
            # check if { block is opened 
            elif val.startswith('{'):
               
               blocksOpened += 1
               curNode = curNode.addChild(Node(name=var))
               
               # parse rest of line as data
               if len(val)>1:
                  val = val[1:].strip()
                  
                  if val.isdigit(): val = int(val)
                  else: val = val.replace('"','')
                  curNode.data = val 
         
         # block opened/closed?
         elif l.count('{')==1:
            raise BaseException("Not yet supported.")
         elif l == '}':
            # before finalizing the block, try to get some insight on the data
            if curNode.data:
               if curNode.data.count('"') > 0: # probably a string, strip the quotation marks
                  curNode.data.replace('"','')
               else:
                  spl = curNode.data.split()
                  if len(spl) > 1: # probably a list, try to convert to integers
                     li = []
                     for itm in spl:
                        if itm.isdigit(): li.append(int(itm)) # IntList
                        else: li.append(itm)                  # StringList
                     curNode.data = li
            curNode = curNode.parent
            blocksOpened -= 1
            
         else: # no assignments, not blank - this would be (multiline) data for the current object
            # check if there's a block being closed somewhere
            if l.count('}') == 1:
               if curNode is root:
                  raise BaseException("WTF?! %s, '%s'" % (self.file, l))
               tpl = l.split('}')
               
               itm = tpl[0].strip()
               if itm.count('"') > 0:
                  itm = itm.replace('"','')
               elif itm.isdigit():
                  itm = int(itm)
                  
               if not curNode.data: curNode.data = itm
               elif type(curNode.data) in types.StringTypes: curNode.data += itm
               else: curNode.data.append(itm)
               
               curNode = curNode.parent
               blocksOpened -= 1
               
               if len(tpl) > 1 and tpl[1]!='':
                  print tpl
                  raise BaseException("Anything after a } in the same line will be ignored. (file=%s, line='%s')" % (self.file, l))
            elif not (l.count('{') == l.count('}') == 0):
               raise BaseException("WTF? file=%s" % self.file)
            
            if curNode.data:
               curNode.data = " ".join([curNode.data, l.strip()])
            else:
               curNode.data = l.strip()
            
      if blocksOpened != 0:
         print root
         raise BaseException("Number of opened and closed blocks does not match: %d blocks open. (%s)" % (blocksOpened, self.file))
      
      return root