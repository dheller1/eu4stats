import sys, types

class Node:
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