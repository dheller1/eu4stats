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
         lines = f.readlines()
      
      root = Node(id=0, name="root", level=0)

      curNode = root
      blocksOpened = 0
      
      for line in lines:
         # strip whitespaces
         l = line.strip()
         
         # skip comments and blank lines
         if len(l) == 0 or l.startswith('#'):
            continue
         
         # assignment?
         if l.count('=') > 1: raise BaseException("Invalid line - multiple '=' assignments! "+l)
         elif l.count('=') == 1:
            var, val = l.split('=')[0].strip(), l.split('=')[1].strip()
             
            # check if value is valid (no { block opened, not empty)
            if len(val) > 0 and val.count('{') == 0 and val.count('}') == 0:
               if val.count('"') > 0: # probably a string, strip the quotation marks
                  val.replace('"','')
               elif val.isdigit():
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
            elif val=='{':
               blocksOpened += 1
               curNode = curNode.addChild(Node(name=var))
               print "Adding empty child node %s." % curNode.hierarchyStr()
         
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
            assert (l.count('{') == l.count('}') == 0)
            if curNode.data:
               curNode.data = " ".join([curNode.data, l.strip()])
            else:
               curNode.data = l.strip()
            
      if blocksOpened != 0:
         raise BaseException("Number of opened and closed blocks does not match: %d blocks open." % blocksOpened)
      
      return root