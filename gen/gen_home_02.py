"""Generator for HOME-02 / HOME-11 embeddings (owner: TASK_C)."""
from __future__ import annotations
import hashlib
import json
import os
import random
import re
TEST_ID_02 = "HOME-02"
TEST_ID_11 = "HOME-11"
SEED = 207
EN_ENTS = ["Kestrel Harbor","Lumen Mill","Ferrostat Bridge","Driftline Market","Cobalt Ferry","Heliotrope Garden","Vantacore Depot","Mistralith Tower","Amber Atrium","Willow Shed","Granite Vault","Cinder Block Yard","Maple Observatory","Juniper Kiln","Opal Greenhouse","Rookery Station","Sable Workshop","Tern Lighthouse","Umber Archive","Vesper Orchard"]
UK_ENTS = ["\u0421\u043e\u043a\u043e\u043b\u0438\u043d\u0435 \u043e\u0437\u0435\u0440\u043e","\u041b\u0456\u0445\u0442\u0430\u0440\u043d\u0438\u0439 \u043c\u043b\u0438\u043d","\u0417\u0430\u043b\u0456\u0437\u043d\u0438\u0439 \u043c\u0456\u0441\u0442","\u0411\u0443\u0440\u0448\u0442\u0438\u043d\u043e\u0432\u0430 \u0432\u0435\u0436\u0430","\u0422\u0438\u0445\u0430 \u0433\u0430\u0432\u0430\u043d\u044c","\u041a\u043b\u0435\u043d\u043e\u0432\u0438\u0439 \u0441\u043a\u043b\u0430\u0434","\u0412\u0456\u0442\u0440\u044f\u043d\u0438\u0439 \u043f\u0430\u0440\u043a","\u041c\u0456\u0434\u043d\u0430 \u0434\u0437\u0432\u0456\u043d\u0438\u0446\u044f","\u041e\u0441\u043e\u043a\u043e\u0440\u043e\u0432\u0438\u0439 \u044f\u0440","\u041f\u043e\u043b\u0443\u0431\u0438\u043d\u0430 \u0434\u043e\u043b\u0438\u043d\u0430"]
def _sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(65536),b""): h.update(c)
    return h.hexdigest()
def _en_passage(rng,ent,asp,idx):
    year=1840+((idx*37)%160); cnt=20+((idx*53)%380); dep=12+((idx*29)%80)
    if asp==0:
        sents=[f"{ent} was established in {year} by a cooperative of river traders seeking a winter mooring.","Early ledgers record {cnt} berths and a single stone warehouse with a slate roof.","A fire in the following decade destroyed the eastern pier, which was rebuilt wider with iron piles.","The founders charter forbade tolls on foot passengers, a rule still painted above the gatehouse.","By the turn of the century the settlement counted three schools and a brass band."]
    elif asp==1:
        sents=[f"{ent} stretches across two basins joined by a {dep}-metre embankment planted with alder trees.","The northern basin holds {cnt} moorings for narrow boats, while the southern basin serves barges.","A clock tower of pale sandstone marks the central quay and houses the harbour office.","Granite steps descend to the water at four points, each lit by gas-style lanterns.","Warehouses of brick and timber line the western edge behind a row of lime trees."]
    elif asp==2:
        sents=[f"Each dawn {cnt} workers rake the channels of {ent} and check the {dep} mooring rings for wear.","Tug crews rotate on eight-hour shifts, logging every tow in a canvas-bound register.","Dredging happens each spring; silt is barged away and sold to brick makers downstream.","Gulls are counted monthly by volunteers, whose tallies exceeded {cnt*2} birds last season.","Night watchmen patrol with lanterns, closing the sluice gates before midnight."]
    else:
        sents=[f"Every autumn {ent} hosts a lantern regatta that draws about {cnt*5} visitors to the quays.","Stalls sell smoked fish, wool scarves and printed charts of the {dep} historic berths.","Children race paper boats between the piers while a choir sings from the clock tower.","The festival closes with fireworks reflected in the basin water after dusk.","Proceeds fund the maintenance of the embankment gardens and the bandstand."]
    fill=[f"Visitors often remark on the calm water near {ent} and the smell of tar and rope.","The keepers publish a small pamphlet each {year%12+2} months describing repairs and sightings.","Local painters favour the eastern quay at sunrise when the mist hangs low."]
    rng.shuffle(fill)
    text=" ".join(sents+fill[:3])
    return text
def _uk_passage(rng,ent,asp,idx):
    year=1860+((idx*41)%120); cnt=15+((idx*47)%300); dep=8+((idx*31)%60)
    if asp==0:
        sents=[f"{ent} \u0437\u0430\u0441\u043d\u043e\u0432\u0430\u043d\u0435 \u0443 {year} \u0440\u043e\u0446\u0456 \u0430\u0440\u0442\u0456\u043b\u043b\u044e \u0440\u0438\u0431\u0430\u043b\u043e\u043a, \u044f\u043a\u0456 \u0448\u0443\u043a\u0430\u043b\u0438 \u0437\u0438\u043c\u043e\u0432\u0443 \u0441\u0442\u043e\u044f\u043d\u043a\u0443.","Перші книги обліку згадують {cnt} причалів і одну кам\u0027яну комору під шифером.".replace("{cnt}",str(cnt)),f"Пожежа наступного десятиліття знищила східний пірс, який відбудували ширшим на залізних палях.","Статут засновників забороняв брати плату з пішоходів, правило досі написане над брамою.","На зламі століть тут діяли три школи та духовий оркестр."]
    elif asp==1:
        sents=[f"{ent} тягнеться через дві затоки, з\u0027єднані насипом завдовжки {dep} метрів з вільхами.","Північна затока має {cnt} стоянок для вузьких човнів, південна приймає баржі.".replace("{cnt}",str(cnt)),"Вежа з блідого пісковику позначає центральний причал, там міститься контора.","Гранітні сходи спускаються до води в чотирьох місцях, освітлені ліхтарями.","Цегляні й дерев\u0027яні склади стоять уздовж західного краю за липами."]
    elif asp==2:
        sents=[f"Щоранку {cnt} працівників чистять канали біля {ent} і перевіряють причальні кільця.".replace("{cnt}",str(cnt)),"Буксирні команди змінюються кожні вісім годин і записують кожне буксирування в журнал.","Днопоглиблення відбувається щовесни, мул вивозять баржами для цегелень.","Волонтери щомісяця рахують чайок, торік нарахували понад сотню птахів.","Нічні сторожі з ліхтарями обходять територію і зачиняють шлюзи до півночі."]
    else:
        sents=[f"Щоосені {ent} приймає свято ліхтарів, яке збирає сотні гостей на набережних.","Ятки торгують копченою рибою, вовняними шалями та картами історичних причалів.","Діти пускають паперові човники між пірсами, а хор співає з вежі.","Свято завершується феєрверком над водою після сутінків.","Кошти йдуть на догляд садів на насипу та альтанки."]
    fill=[f"Гості часто згадують спокійну воду біля {ent} і запах смоли та канатів.","Доглядачі видають невеличкий бюлетень з описом ремонтів і спостережень.","Місцеві художники люблять східний причал на світанку, коли стелиться туман.",f"Увечері над {ent} чути дзвони з сусідньої вежі і голоси рибалок.",f"Навесні сюди прилітають лелеки і гніздяться на старих стовпах біля {ent}."]
    rng.shuffle(fill)
    return " ".join(sents+fill)
def _words(s): return re.findall(r"[0-9A-Za-z\u0400-\u04FF']+",s.lower())
def _grams(ws,n=4):
    return {" ".join(ws[i:i+n]) for i in range(len(ws)-n+1)} if len(ws)>=n else set()
def _check(query,passage):
    assert not (set(re.findall(r"\d",query)) & set(re.findall(r"\d",passage))), f"digit overlap {query!r}"
    qg=_grams(_words(query),4); pg=_grams(_words(passage),4)
    ov=qg & pg
    assert not ov, f"phrase overlap {ov} in {query!r}"
def _en_q(ent,asp):
    if asp==0: return f"How did {ent} come into being and what shaped its early years?"
    if asp==1: return f"What does {ent} look like and how is it laid out?"
    if asp==2: return f"How does {ent} function day to day and who keeps it running?"
    return f"What gatherings or traditions take place at {ent}?"
def _uk_q(ent,asp):
    if asp==0: return f"\u042f\u043a \u0432\u0438\u043d\u0438\u043a\u043b\u043e {ent} \u0456 \u0449\u043e \u0432\u043f\u043b\u0438\u043d\u0443\u043b\u043e \u043d\u0430 \u0439\u043e\u0433\u043e \u043f\u0435\u0440\u0448\u0456 \u0440\u043e\u043a\u0438?"
    if asp==1: return f"\u042f\u043a \u0432\u0438\u0433\u043b\u044f\u0434\u0430\u0454 {ent} \u0456 \u044f\u043a \u0432\u043e\u043d\u043e \u0432\u043b\u0430\u0448\u0442\u043e\u0432\u0430\u043d\u0435?"
    if asp==2: return f"\u042f\u043a \u043f\u0440\u0430\u0446\u044e\u0454 {ent} \u0449\u043e\u0434\u0435\u043d\u043d\u043e \u0456 \u0445\u0442\u043e \u0437\u0430 \u043d\u0435\u0454 \u0434\u0431\u0430\u0454?"
    return f"\u042f\u043a\u0456 \u0441\u0432\u044f\u0442\u0430 \u0447\u0438 \u0437\u0432\u0438\u0447\u0430\u0457 \u0432\u0456\u0434\u0431\u0443\u0432\u0430\u044e\u0442\u044c\u0441\u044f \u0432 {ent}?"
def _de_q(ent,asp):
    if asp==0: return f"Wie entstand {ent} und was pr\u00e4gte seine fr\u00fchen Jahre?"
    if asp==1: return f"Wie sieht {ent} aus und wie ist es angelegt?"
    if asp==2: return f"Wie funktioniert {ent} im Alltag und wer h\u00e4lt es instand?"
    return f"Welche Feste oder Br\u00e4uche gibt es bei {ent}?"
def _es_q(ent,asp):
    if asp==0: return f"\u00bfC\u00f3mo naci\u00f3 {ent} y qu\u00e9 marc\u00f3 sus primeros a\u00f1os?"
    if asp==1: return f"\u00bfC\u00f3mo es {ent} y c\u00f3mo est\u00e1 organizado?"
    if asp==2: return f"\u00bfC\u00f3mo funciona {ent} cada d\u00eda y qui\u00e9n lo mantiene?"
    return f"\u00bfQu\u00e9 fiestas o tradiciones hay en {ent}?"
def main():
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rng=random.Random(SEED)
    corpus=[]
    idx=0
    for ei,ent in enumerate(EN_ENTS):
        for asp in range(4):
            did=f"D{idx+1:03d}"; idx+=1
            txt=_en_passage(random.Random(SEED*1000+idx),ent,asp,idx)
            wc=len(txt.split())
            assert 100 <= wc <= 250, (did,wc)
            corpus.append({"id":did,"text":txt,"lang":"en","entity":ent,"aspect":asp})
    for ei,ent in enumerate(UK_ENTS):
        for asp in range(4):
            did=f"D{idx+1:03d}"; idx+=1
            txt=_uk_passage(random.Random(SEED*2000+idx),ent,asp,idx)
            wc=len(txt.split())
            assert 100 <= wc <= 250, (did,wc)
            corpus.append({"id":did,"text":txt,"lang":"uk","entity":ent,"aspect":asp})
    assert len(corpus)==120
    by_id={p["id"]:p for p in corpus}
    en_ids=[p["id"] for p in corpus if p["lang"]=="en"]; uk_ids=[p["id"] for p in corpus if p["lang"]=="uk"]
    def sib(pid):
        p=by_id[pid]
        cands=[q for q in corpus if q["entity"]==p["entity"] and q["id"]!=pid]
        cands.sort(key=lambda x:x["id"])
        return cands[0]["id"] if cands else None
    rng2=random.Random(SEED+1)
    uk_pool=sorted(uk_ids)[:40]; en_pool=sorted(en_ids)
    q02=[]
    for i,pid in enumerate(uk_pool[:10]):
        p=by_id[pid]; q=_en_q(p["entity"],p["aspect"]); _check(q,p["text"])
        q02.append({"q":q,"ql":"en","pid":pid,"kind":"en-uk"})
    uk_q_pool=sorted(en_ids)[:10]
    for i,pid in enumerate(uk_q_pool):
        p=by_id[pid]; q=_uk_q(p["entity"],p["aspect"]); _check(q,p["text"])
        q02.append({"q":q,"ql":"uk","pid":pid,"kind":"uk-en"})
    for i,pid in enumerate(sorted(en_ids)[10:20]):
        p=by_id[pid]; q=_de_q(p["entity"],p["aspect"]); _check(q,p["text"])
        q02.append({"q":q,"ql":"de","pid":pid,"kind":"de-en"})
    for i,pid in enumerate(sorted(en_ids)[20:30]):
        p=by_id[pid]; q=_es_q(p["entity"],p["aspect"]); _check(q,p["text"])
        q02.append({"q":q,"ql":"es","pid":pid,"kind":"es-en"})
    assert len(q02)==40
    left_en=[pid for pid in sorted(en_ids) if pid not in [x["pid"] for x in q02]][:30]
    q11=[]
    for pid in left_en:
        p=by_id[pid]; q=_en_q(p["entity"],p["aspect"]); _check(q,p["text"])
        q11.append({"q":q,"ql":"en","pid":pid,"kind":"en-en"})
    assert len(q11)==30
    def mkcases(qlist,test,tiercyc):
        out=[]
        for i,e in enumerate(qlist):
            hard=sib(e["pid"])
            qrels={e["pid"]:2}
            if hard: qrels[hard]=1
            tgt=by_id[e["pid"]]["lang"]
            out.append({"id":f"{test}-{i+1:02d}","test_id":test,"tier":tiercyc[i%len(tiercyc)],"lang":e["ql"],"input":{"query":e["q"],"query_lang":e["ql"],"target_lang":tgt},"expected":{"qrels":qrels},"meta":{"kind":e["kind"],"primary":e["pid"],"target_lang":tgt}})
        by={"easy":[],"medium":[],"hard":[]}
        for c in out: by[c["tier"]].append(c)
        for v in by.values(): v.sort(key=lambda x:x["id"])
        order=[]; idxd={"easy":0,"medium":0,"hard":0}; cyc=["easy","medium","hard"]; ci=0
        while len(order)<len(out):
            ok=False
            for _ in range(3):
                t=cyc[ci%3]; ci+=1
                if idxd[t]<len(by[t]): order.append(by[t][idxd[t]]); idxd[t]+=1; ok=True; break
            if not ok: break
        for i,c in enumerate(order): c["id"]=f"{test}-{i+1:02d}"
        return order
    tiers02=["easy","medium","hard","easy","medium","hard","easy","medium"]
    c02=mkcases(q02,TEST_ID_02,["easy","medium","hard"])
    c11=mkcases(q11,TEST_ID_11,["easy","medium","hard"])
    d02=os.path.join(root,"fixtures","HOME-02"); os.makedirs(d02,exist_ok=True)
    with open(os.path.join(d02,"corpus.jsonl"),"w",encoding="utf-8",newline="\n") as f:
        for p in corpus: f.write(json.dumps({"id":p["id"],"text":p["text"],"lang":p["lang"],"entity":p["entity"],"aspect":p["aspect"]},ensure_ascii=False,sort_keys=True)+"\n")
    with open(os.path.join(d02,"cases.jsonl"),"w",encoding="utf-8",newline="\n") as f:
        for c in c02: f.write(json.dumps(c,ensure_ascii=False,sort_keys=True)+"\n")
    files={fn:_sha(os.path.join(d02,fn)) for fn in sorted(os.listdir(d02)) if fn!="manifest.json"}
    with open(os.path.join(d02,"manifest.json"),"w",encoding="utf-8",newline="\n") as f: f.write(json.dumps({"test_id":TEST_ID_02,"seed":SEED,"n_cases":len(c02),"files":files},ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    d11=os.path.join(root,"fixtures","HOME-11"); os.makedirs(d11,exist_ok=True)
    with open(os.path.join(d11,"cases.jsonl"),"w",encoding="utf-8",newline="\n") as f:
        for c in c11: f.write(json.dumps(c,ensure_ascii=False,sort_keys=True)+"\n")
    files={fn:_sha(os.path.join(d11,fn)) for fn in sorted(os.listdir(d11)) if fn!="manifest.json"}
    with open(os.path.join(d11,"manifest.json"),"w",encoding="utf-8",newline="\n") as f: f.write(json.dumps({"test_id":TEST_ID_11,"seed":SEED,"n_cases":len(c11),"files":files},ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    return d02
if __name__=="__main__":
    print(main())
