import pegpy

parser = pegpy.generate('cj.tpeg')

t = parser('赤いボールと緑のたぬき')
print(t)
print(repr(t))
print('tag', t.tag)
print('子ノードの数', len(t))
print('0番目', t[0])
for sub in t:
  print(sub)

def conv(t):
  if t.tag == 'S':
    print(t)

def Verb(t): #Verbを処理
  #処理を書く
  koinu(t[0])

func = globals()
def koinu(t):
  if t.tag in func:
    func[t.tag](t)  #Verb
  else:
    print('TODO: define tag')
