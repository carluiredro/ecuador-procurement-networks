import sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
sys.path.insert(0,os.path.join(ROOT,'code'))
os.chdir(ROOT)
import pandas as pd, numpy as np, unicodedata, re
from netanalysis import load
c,P=load(); W=c[c.year.between('2015','2021')].copy()
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().upper()
    return re.sub(r'\s+',' ',re.sub(r'[^A-Z0-9 ]',' ',s)).strip()
W['bname']=W.buyer_id.map(P.name).fillna('').map(norm)
def btype(n):
    has=lambda *k: any(re.search(r'\b'+x+r'\b',n) for x in k)
    if has('PARROQUIAL','PARROQUIALES','JUNTA PARROQUIAL','PARROQUIA'): return 'GAD parroquial'
    if has('EMPRESA','EMMOP','EMAPA','EP','E P','AUSTROGAS','ACERIAS','COMPANIA DE ECONOMIA MIXTA','CORPORACION ELECTRICA','CNEL','PETROECUADOR','S A','C A','CORPORACION NACIONAL'): return 'Empresa pública'
    if has('HOSPITAL','HOSPITALARIA','CENTRO DE ESPECIALIDADES','CENTRO MEDICO','DISPENSARIO','SALUD','IESS','SEGURIDAD SOCIAL','CLINICA','MATERNIDAD'): return 'Salud'
    if has('UNIVERSIDAD','POLITECNICA','INSTITUTO SUPERIOR','INSTITUTO TECNOLOGICO','EDUCACION','COLEGIO','UNIDAD EDUCATIVA','ESCUELA SUPERIOR'): return 'Educación'
    if has('FEDERACION DEPORTIVA','CONCENTRACION DEPORTIVA'): return 'Otros'
    if has('MINISTERIO','SECRETARIA','SUBSECRETARIA','DIRECCION DISTRITAL','DIRECCION ZONAL','COORDINACION ZONAL','AGENCIA','SERVICIO NACIONAL','INSTITUTO NACIONAL','CONSEJO NACIONAL','BRIGADA','EJERCITO','POLICIA','FUERZA','ARMADA','DIGMAT','COMANDO','DIRECCION GENERAL','SUPERINTENDENCIA','CONTRALORIA','FISCALIA','CONSEJO DE LA JUDICATURA','ASAMBLEA','PRESIDENCIA','DEFENSORIA','CORTE','TRIBUNAL','CNE','CONSEJO NACIONAL ELECTORAL','BANCO','SERVICIO DE RENTAS','SRI','CUERPO DE INGENIEROS','FUERZAS ARMADAS','ESCUELA MILITAR','DIRECCION PROVINCIAL','DELEGACION PROVINCIAL','JUDICATURA','DIRECCION REGIONAL','REGISTRO CIVIL','GOBERNACION','INSTITUTO ECUATORIANO','SERVICIO ECUATORIANO','UNIDAD DE','BASE NAVAL','ESTACION NAVAL','ESTACION AERONAVAL','BASE AEREA','ALA DE COMBATE','DIVISION','ISSFA','ISSPOL','COMANDANCIA','SUBZONA','INSTITUTO GEOGRAFICO MILITAR','BANECUADOR','COMISION DE TRANSITO','ECU 911','CENACE','OPERADOR NACIONAL','SERVICIO DE DRAGAS','ESTACION EXPERIMENTAL','DIRECCION NACIONAL','CONSEJO DE GOBIERNO','PARQUE NACIONAL','ARMADA','NAVAL','AEREA','MILITAR'): return 'Gobierno central'
    if has('GOBIERNO PROVINCIAL','GOB PROV','PREFECTURA','CONSEJO PROVINCIAL','H CONSEJO PROVINCIAL') or (has('GOBIERNO AUTONOMO DESCENTRALIZADO','GOBIERNO AUTONOMO','GAD') and has('PROVINCIA','PROVINCIAL')) and not has('MUNICIPAL','MUNICIPIO','CANTON','MUNICIPALIDAD'): return 'GAD provincial'
    if has('MUNICIPAL','MUNICIPIO','MUNICIPALIDAD','CANTON','CANTONAL','METROPOLITANO','GOBIERNO AUTONOMO DESCENTRALIZADO','GOBIERNO AUTONOMO','GADM','GAD','ILUSTRE','CUERPO DE BOMBEROS','BOMBEROS','REGISTRO DE LA PROPIEDAD'): return 'GAD municipal'
    return 'Otros'
names=W[['buyer_id','bname']].drop_duplicates('buyer_id')
names['btype']=names.bname.map(btype)
W=W.merge(names[['buyer_id','btype']],on='buyer_id',how='left')
REG={'COSTA':['ESMERALDAS','MANABI','LOS RIOS','GUAYAS','SANTA ELENA','EL ORO','SANTO DOMINGO DE LOS TSACHILAS'],
     'SIERRA':['CARCHI','IMBABURA','PICHINCHA','COTOPAXI','TUNGURAHUA','BOLIVAR','CHIMBORAZO','CANAR','CAÑAR','AZUAY','LOJA'],
     'AMAZONIA':['SUCUMBIOS','ORELLANA','NAPO','PASTAZA','MORONA SANTIAGO','ZAMORA CHINCHIPE'],'INSULAR':['GALAPAGOS']}
r={p:k for k,v in REG.items() for p in v}
W['region']=W.breg.map(r)
W['local_sup']=(W.breg==W.sreg).astype(int)
# market thickness: distinct winning suppliers active in buyer province x CPC2 x year
th=W.groupby(['breg','cpc2','year']).supplier_id.nunique().rename('n_sup_market')
W=W.join(th,on=['breg','cpc2','year'])
bs=W.groupby('buyer_id').size().rename('buyer_n'); W=W.join(bs,on='buyer_id')
W.to_parquet(os.path.join(HERE,'contracts_ic.parquet'))
print(names.btype.value_counts().to_string())
print(W.btype.value_counts().to_string())
print(W.region.value_counts(dropna=False).to_string())
