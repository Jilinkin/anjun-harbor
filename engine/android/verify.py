from pathlib import Path
import zipfile,hashlib,struct
root=Path(__file__).resolve().parent
jar=root/"build"/"harbor.jar"
with zipfile.ZipFile(jar) as z:
    dex=z.read("classes.dex")
    assert dex[:4]==b"dex\n"
    assert all(not n.endswith(".class") for n in z.namelist())
def u32(off): return struct.unpack_from("<I",dex,off)[0]
string_count,string_off=u32(56),u32(60)
type_count,type_off=u32(64),u32(68)
class_count,class_off=u32(96),u32(100)
def get_string(i):
    assert i<string_count
    p=u32(string_off+4*i)
    while dex[p]&128:p+=1
    p+=1
    return dex[p:dex.index(b"\0",p)].decode("utf-8")
classes=[]
for i in range(class_count):
    idx=u32(class_off+32*i)
    assert idx<type_count
    classes.append(get_string(u32(type_off+4*idx)))
assert set(classes)=={"Lcom/github/catvod/spider/Harbor;","Lcom/github/catvod/spider/Init;","Lcom/github/catvod/spider/HarborCatalog;","Lcom/github/catvod/spider/HarborData;","Lcom/github/catvod/spider/HarborRules;","Lcom/github/catvod/spider/HarborRegistry;","Lcom/github/catvod/spider/HarborNetwork;"},classes
digest=hashlib.sha256(jar.read_bytes()).hexdigest()
(root/"build"/"sha256.txt").write_text(digest+"  harbor.jar\n")
print("Verified DEX classes:",classes,"SHA256:",digest)
