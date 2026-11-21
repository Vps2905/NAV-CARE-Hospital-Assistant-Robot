#!/usr/bin/env python3
"""Local-only dashboard. Run with sourced ROS 2 for live mode."""
import argparse, json, secrets, sys, os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from core import Store, Workflow
from robot import DemoRobot, ROSRobot
BASE=Path(__file__).resolve().parent

def make_server(robot,store,port=8080):
    workflow=Workflow(store,robot); token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def send(self,code,data,kind='application/json'):
            if not isinstance(data,bytes): data=json.dumps(data).encode()
            self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY'); self.end_headers(); self.wfile.write(data)
        def valid_host(self): return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
        def do_GET(self):
            if not self.valid_host(): return self.send(403,{'error':'Local requests only'})
            if self.path=='/api/state': return self.send(200,workflow.state())
            if self.path=='/api/history': return self.send(200,store.history())
            if self.path=='/api/token': return self.send(200,{'token':token})
            if self.path.split('?')[0]=='/api/camera':
                frame=robot.frame(); return self.send(200,frame,'image/png') if frame else self.send(404,{'error':'No fresh image'})
            files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8'),'/hospital.png':('hospital.png','image/png')}
            if self.path in files:
                name,kind=files[self.path]; return self.send(200,(BASE/'static'/name).read_bytes(),kind)
            return self.send(404,{'error':'Not found'})
        def do_POST(self):
            if not self.valid_host() or self.headers.get('X-Navcare-Token')!=token or self.headers.get('Origin') not in (None,f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'): return self.send(403,{'error':'Local session required'})
            try:
                if self.path!='/api/action': return self.send(404,{'error':'Not found'})
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=10000: raise ValueError('Invalid request size')
                data=json.loads(self.rfile.read(length)); workflow.act(data['action'],data.get('data',{})); self.send(200,workflow.state())
            except (ValueError,KeyError,TypeError,AttributeError) as e: self.send(400,{'error':str(e)})
            except Exception as e: self.send(500,{'error':'Request failed: '+str(e)})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--demo',action='store_true'); p.add_argument('--live',action='store_true'); p.add_argument('--port',type=int,default=8080); a=p.parse_args()
    if a.live==a.demo: p.error('choose exactly one of --demo or --live')
    if a.live:
        if input('GAZEBO ONLY. No real robot, no other goal clients or teleop. Type SIMULATION to enable: ').strip()!='SIMULATION': return
        try: import rclpy, nav2_msgs, tf2_ros
        except ImportError as e: sys.exit('Source ROS 2 Lyrical first: '+str(e))
    robot=DemoRobot() if a.demo else ROSRobot(); store=Store(BASE/'data'/('demo.sqlite' if a.demo else 'simulation.sqlite'))
    try:
        server=make_server(robot,store,a.port); print(f'NAV CARE | {"DRY RUN" if a.demo else "GAZEBO LIVE"} | http://127.0.0.1:{server.server_port}',flush=True); server.serve_forever()
    except KeyboardInterrupt: print('\nClosing. Requesting mission cancellation if needed. Verify robot is stationary before continuing.')
    finally: robot.close()
if __name__=='__main__': main()
