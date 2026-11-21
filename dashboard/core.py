"""Fictional patient workflow. Not a medical device or clinical triage."""
import datetime, json, os, sqlite3, threading, uuid
from pathlib import Path
GOALS = {'reception':(-6.65,-3.55,90),'waiting':(-6.65,3.15,90),'general_medicine':(0,3.15,90),'orthopedics':(6.65,3.15,90),'nurse_station':(0,-3.15,-90),'laboratory':(6.65,-3.15,-90),'corridor':(-6.65,0,90)}
LABELS = dict(zip(GOALS,['Reception','Waiting Area','General Medicine','Orthopedics','Nurse Station','Laboratory','Central Corridor']))
VITALS={'pulse':76,'spo2':98,'bp':'120/80','temperature':36.8,'source':'SIMULATED — not measured'}

def route(reason, referral):
    t=' '.join(reason.lower().replace('’',"'").split())
    urgent=('chest pain','difficulty breathing','shortness of breath',"can't breathe",'cannot breathe','cant breathe','severe bleeding','unconscious','fainted','collapse','stroke','seizure','heart attack','suicid','overdose','severe pain','heavy bleeding')
    if any(x in t for x in urgent): return None,'Possible urgent concern. Ask nearby staff for immediate assistance; do not start routine guidance.'
    if any(x in t for x in ('blood test','urine test','sample collection','laboratory','lab test')):
        return ('laboratory','Confirmed referral: staff must verify the destination.') if referral else ('nurse_station','Lab referral not confirmed. Ask staff to review.')
    ortho=any(x in t for x in ('knee','joint','bone','fracture','sprain','back pain','wrist','ankle','shoulder pain','orthopedic','orthopaedic'))
    general=any(x in t for x in ('fever','cough','cold','headache','stomach','vomit','tired','fatigue','checkup','rash'))
    if ortho and not general: return 'orthopedics','Example keyword match; staff must confirm.'
    if general and not ortho: return 'general_medicine','Example keyword match; staff must confirm.'
    return 'nurse_station','Unclear or mixed concern. Ask staff to review.'

class Store:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        if not self.path.exists():
            fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600); os.close(fd)
        os.chmod(self.path,0o600)
        with sqlite3.connect(self.path) as c: c.execute('create table if not exists visits(id text primary key, payload text not null)')
    def save(self,visit):
        with sqlite3.connect(self.path) as c: c.execute('insert or replace into visits values (?,?)',(visit['id'],json.dumps(visit)))
    def history(self):
        with sqlite3.connect(self.path) as c: return [json.loads(r[0]) for r in c.execute('select payload from visits order by rowid desc limit 50')]
    def clear(self):
        with sqlite3.connect(self.path) as c: c.execute('delete from visits')

class Workflow:
    def __init__(self,store,robot): self.store=store; self.robot=robot; self.visit=None; self.lock=threading.RLock()
    def sync(self):
        if not self.visit: return
        m=self.robot.snapshot()['mission']; v=self.visit
        if v['stage'] not in ('guiding','returning'): return
        if m['status']=='succeeded': v['stage']='arrived' if v['stage']=='guiding' else 'complete'
        elif m['status'] in ('failed','canceled','uncertain'): v['stage']='interrupted'; v['note']=m['detail']
        else: return
        self.store.save(v)
    def state(self):
        with self.lock:
            self.sync(); return {'visit':self.visit.copy() if self.visit else None,'robot':self.robot.snapshot(),'goals':GOALS,'labels':LABELS}
    def act(self,action,d):
        with self.lock:
            self.sync(); v=self.visit
            if action=='register':
                if v and v['stage'] not in ('complete','staff_review','registered','measured','review'): raise ValueError('Finish or recover the current mission first.')
                if d.get('fictional') is not True: raise ValueError('Confirm fictional data only.')
                if not isinstance(d.get('name'),str) or not d['name'].strip() or len(d['name'])>80: raise ValueError('Enter a fictional name (1–80 characters).')
                age=d.get('age'); gender=d.get('gender','Not specified')
                if type(age) is not int or not 0<=age<=120 or gender not in ('Female','Male','Other','Not specified'): raise ValueError('Check age and gender.')
                self.visit={'id':uuid.uuid4().hex[:10].upper(),'name':d['name'].strip(),'age':age,'gender':gender,'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'registered','note':'Fictional demonstration only.'}; v=self.visit
            elif action=='clear_history':
                if v and v['stage'] in ('guiding','returning','arrived','interrupted'): raise ValueError('Finish the mission first.')
                self.store.clear(); self.visit=None; return
            elif not v: raise ValueError('Register a fictional patient first.')
            elif action=='measure' and v['stage']=='registered': v.update(vitals=VITALS.copy(),stage='measured')
            elif action=='recommend' and v['stage'] in ('measured','review','staff_review'):
                reason=d.get('reason','');
                if not isinstance(reason,str) or not reason.strip() or len(reason)>500: raise ValueError('Enter a reason (1–500 characters).')
                dest,note=route(reason,d.get('referral') is True); v.update(reason=reason.strip(),referral=d.get('referral') is True,destination=dest,note=note,stage='review' if dest else 'staff_review')
            elif action=='guide' and v['stage']=='review':
                if d.get('confirmed') is not True: raise ValueError('Staff must confirm destination and clear route.')
                dest=d.get('destination');
                if dest not in ('general_medicine','orthopedics','laboratory','nurse_station','waiting'): raise ValueError('Choose a valid destination.')
                if dest=='laboratory' and not v['referral']: raise ValueError('Lab referral required.')
                self.robot.start(dest,require_reception=True); v.update(destination=dest,stage='guiding',note='Staff confirmed simulation guidance.')
            elif action=='return' and v['stage'] in ('arrived','interrupted'):
                if d.get('confirmed') is not True: raise ValueError('Confirm handover/recovery and clear route.')
                self.robot.start('reception',require_reception=False); v.update(stage='returning',note='Operator confirmed return.')
            elif action=='cancel' and v['stage'] in ('guiding','returning'): self.robot.cancel()
            else: raise ValueError('Action not available in the current stage.')
            self.store.save(v)
