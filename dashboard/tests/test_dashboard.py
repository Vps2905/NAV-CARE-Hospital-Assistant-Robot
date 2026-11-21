import json, tempfile, threading, time, unittest, urllib.request, urllib.error, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Store, Workflow, route
from robot import DemoRobot,png_image
from server import make_server
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.r=DemoRobot(); self.s=Store(Path(self.tmp.name)/'test.sqlite'); self.w=Workflow(self.s,self.r)
    def tearDown(self): self.tmp.cleanup()
    def register(self): self.w.act('register',{'name':'Demo Patient','age':25,'fictional':True}); self.w.act('measure',{})
    def test_full_workflow(self):
        self.register(); self.w.act('recommend',{'reason':'knee pain'}); self.assertEqual(self.w.visit['destination'],'orthopedics')
        with self.assertRaises(ValueError): self.w.act('guide',{'destination':'orthopedics'})
        self.w.act('guide',{'destination':'orthopedics','confirmed':True}); self.r.end=0; self.assertEqual(self.w.state()['visit']['stage'],'arrived')
        self.w.act('return',{'confirmed':True}); self.r.end=0; self.assertEqual(self.w.state()['visit']['stage'],'complete'); self.assertEqual(len(self.s.history()),1)
    def test_urgent_no_motion(self):
        self.register(); self.w.act('recommend',{'reason':'chest pain'}); self.assertEqual(self.w.visit['stage'],'staff_review')
        with self.assertRaises(ValueError): self.w.act('guide',{'destination':'general_medicine','confirmed':True})
    def test_referral(self):
        self.register(); self.w.act('recommend',{'reason':'blood test'}); self.assertEqual(self.w.visit['destination'],'nurse_station')
        with self.assertRaises(ValueError): self.w.act('guide',{'destination':'laboratory','confirmed':True})
        self.w.act('recommend',{'reason':'blood test','referral':True}); self.assertEqual(self.w.visit['destination'],'laboratory')
    def test_cancel(self):
        self.register(); self.w.act('recommend',{'reason':'fever'}); self.w.act('guide',{'destination':'general_medicine','confirmed':True}); self.w.act('cancel',{}); self.assertEqual(self.w.state()['visit']['stage'],'interrupted')
    def test_fictional_and_reception_gate(self):
        with self.assertRaises(ValueError): self.w.act('register',{'name':'Demo','age':20})
        self.register(); self.w.act('recommend',{'reason':'fever'}); self.r.pose=[0,3,90]
        with self.assertRaises(ValueError): self.w.act('guide',{'destination':'general_medicine','confirmed':True})
    def test_png(self): self.assertTrue(png_image(2,1,'bgr8',6,b'\x00\x00\xff\xff\x00\x00').startswith(b'\x89PNG'))
    def test_http(self):
        s=make_server(self.r,self.s,0); t=threading.Thread(target=s.serve_forever,daemon=True); t.start(); base=f'http://127.0.0.1:{s.server_port}'
        try:
            self.assertIn(b'Patient assistance',urllib.request.urlopen(base+'/').read()); token=json.load(urllib.request.urlopen(base+'/api/token'))['token']; payload=json.dumps({'action':'register','data':{'name':'Demo HTTP','age':30,'fictional':True}}).encode()
            with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(urllib.request.Request(base+'/api/action',data=payload))
            req=urllib.request.Request(base+'/api/action',data=payload,headers={'X-Navcare-Token':token,'Content-Type':'application/json'}); self.assertEqual(json.load(urllib.request.urlopen(req))['visit']['stage'],'registered')
        finally: s.shutdown(); s.server_close(); t.join()
if __name__=='__main__': unittest.main()
