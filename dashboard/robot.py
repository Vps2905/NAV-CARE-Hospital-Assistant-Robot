"""ROS2 action adapter; only the ROS worker thread touches the ROS node."""
import math, time, threading, struct, zlib
from core import GOALS

class DemoRobot:
    def __init__(self):
        self.lock=threading.RLock(); self.pose=list(GOALS['reception']); self.mission={'status':'idle','detail':'No active mission','destination':None}; self.end=0
    def snapshot(self):
        with self.lock:
            if self.mission['status']=='active' and time.monotonic()>=self.end:
                self.pose=list(GOALS[self.mission['destination']]); self.mission.update(status='succeeded',detail='Dry-run arrival; no robot was moved.')
            return {'mode':'DRY RUN','ready':True,'pose':self.pose.copy(),'mission':self.mission.copy(),'scan':False,'camera':False,'path':[],'health':'No ROS connection; fictional workflow only.'}
    def start(self,dest,require_reception):
        with self.lock:
            self.snapshot()
            if self.mission['status']=='active': raise ValueError('Mission already active.')
            if require_reception and math.dist(self.pose[:2], GOALS['reception'][:2])>0.65: raise ValueError('Robot must be at reception.')
            self.mission={'status':'active','destination':dest,'detail':'Simulating arrival; no motion commanded.'}; self.end=time.monotonic()+3
    def cancel(self):
        with self.lock:
            if self.mission['status']=='active': self.mission.update(status='canceled',detail='Dry run canceled.')
    def frame(self): return None
    def close(self): pass

def png_image(w,h,encoding,step,data):
    if not (0<w<=1920 and 0<h<=1080): return None
    channels={'rgb8':3,'bgr8':3,'rgba8':4,'bgra8':4,'mono8':1}.get(encoding)
    if channels is None or step<w*channels or len(data)<step*h: return None
    rows=[]; data=bytes(data)
    for y in range(h):
        row=data[y*step:y*step+w*channels]
        if encoding.startswith('bgr'):
            b=bytearray(row); b[0::channels],b[2::channels]=row[2::channels],row[0::channels]; row=bytes(b)
        rows.append(b'\x00'+row)
    def chunk(k,v): return struct.pack('!I',len(v))+k+v+struct.pack('!I',zlib.crc32(k+v)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,{1:0,3:2,4:6}[channels],0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows),1))+chunk(b'IEND',b'')

class ROSRobot:
    def __init__(self):
        self.lock=threading.RLock(); self.ready=False; self.pose=None; self.path=[]; self.scan_time=0; self.clock_time=0; self.map_seen=False; self.camera_time=0; self.camera=None; self.health='Waiting for ROS'; self.closed=False; self.cancel_requested=False; self.pending=None; self.mission={'status':'idle','destination':None,'detail':'No active mission'}; self.thread=threading.Thread(target=self.run,daemon=True); self.thread.start()
    def snapshot(self):
        with self.lock:
            return {'mode':'GAZEBO LIVE','ready':self.ready,'pose':self.pose,'mission':self.mission.copy(),'scan':time.monotonic()-self.scan_time<2,'camera':time.monotonic()-self.camera_time<4,'path':self.path,'health':self.health}
    def frame(self):
        with self.lock: return self.camera if time.monotonic()-self.camera_time<4 else None
    def start(self,dest,require_reception):
        with self.lock:
            if not self.ready: raise ValueError('ROS not ready: '+self.health)
            if self.mission['status'] in ('queued','active','canceling','uncertain'): raise ValueError('Previous mission is active or unresolved.')
            if require_reception and (not self.pose or math.dist(self.pose[:2],GOALS['reception'][:2])>0.65): raise ValueError('Robot must be at reception before starting intake guidance.')
            self.pending=dest; self.cancel_requested=False; self.mission={'status':'queued','destination':dest,'detail':'Submitting supervised Nav2 goal…'}
    def cancel(self):
        with self.lock:
            if self.mission['status'] in ('queued','active','canceling'): self.cancel_requested=True; self.mission.update(status='canceling',detail='Cancellation requested; wait for Nav2 acknowledgement.')
    def close(self):
        self.cancel(); self.closed=True; self.thread.join(12)
    def run(self):
        node=None; rclpy=None
        try:
            import rclpy
            from rclpy.action import ActionClient
            from rclpy.qos import QoSProfile, DurabilityPolicy, qos_profile_sensor_data, ReliabilityPolicy
            from rclpy.time import Time
            from rclpy.parameter import Parameter
            from nav2_msgs.action import NavigateToPose
            from action_msgs.msg import GoalStatus
            from lifecycle_msgs.srv import GetState
            from sensor_msgs.msg import Image, LaserScan
            from nav_msgs.msg import OccupancyGrid, Path
            from rosgraph_msgs.msg import Clock
            from tf2_ros import Buffer, TransformListener
            rclpy.init(); node=rclpy.create_node('navcare_dashboard',parameter_overrides=[Parameter('use_sim_time',value=True)])
            self.node=node; tf=Buffer(); listener=TransformListener(tf,node); client=ActionClient(node,NavigateToPose,'/navigate_to_pose')
            lifecycle={n:node.create_client(GetState,'/'+n+'/get_state') for n in ('amcl','map_server','controller_server','planner_server','bt_navigator','collision_monitor','velocity_smoother')}; states={}; checks={}; next_check=0
            def scan(m): self.scan_time=time.monotonic()
            def clock(m): self.clock_time=time.monotonic()
            def map_cb(m): self.map_seen=m.info.width>0 and m.info.height>0
            def cam(m):
                if time.monotonic()-self.camera_time<0.5: return
                p=png_image(m.width,m.height,m.encoding,m.step,m.data)
                if p:
                    with self.lock: self.camera=p; self.camera_time=time.monotonic()
            def plan(m):
                if m.header.frame_id=='map':
                    with self.lock: self.path=[[p.pose.position.x,p.pose.position.y] for p in m.poses[::max(1,len(m.poses)//400)]]
            subs=[node.create_subscription(LaserScan,'/scan',scan,qos_profile_sensor_data),node.create_subscription(Clock,'/clock',clock,qos_profile_sensor_data),node.create_subscription(OccupancyGrid,'/map',map_cb,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)),node.create_subscription(Image,'/navcare/camera/image',cam,qos_profile_sensor_data),node.create_subscription(Path,'/plan',plan,qos_profile_sensor_data)]
            send=handle=result=cancel_future=None; deadline=cancel_deadline=0; shutdown_at=None
            while rclpy.ok():
                rclpy.spin_once(node,timeout_sec=0.05); now=time.monotonic()
                if now>=next_check:
                    next_check=now+1
                    for n,c in lifecycle.items():
                        f=checks.get(n)
                        if f and f.done():
                            try: states[n]=(f.result().current_state.id,now)
                            except Exception: states.pop(n,None)
                            checks.pop(n,None)
                        if not c.service_is_ready(): states.pop(n,None)
                        elif n not in checks: checks[n]=c.call_async(GetState.Request())
                pose=None
                try:
                    t=tf.lookup_transform('map','base_link',Time()); q=t.transform.rotation; p=t.transform.translation
                    age=(node.get_clock().now().nanoseconds-(t.header.stamp.sec*10**9+t.header.stamp.nanosec))/1e9
                    if -2<age<2: pose=[p.x,p.y,math.degrees(math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))]
                except Exception: pass
                problems=[]
                if now-self.clock_time>2: problems.append('simulation clock')
                if now-self.scan_time>2: problems.append('LiDAR')
                if not self.map_seen: problems.append('reference map')
                if pose is None: problems.append('fresh map → base_link TF')
                if not client.server_is_ready(): problems.append('Nav2 action')
                if any(states.get(n,(0,0))[0]!=3 or now-states.get(n,(0,0))[1]>4 for n in lifecycle): problems.append('active navigation/safety servers')
                with self.lock:
                    self.pose=pose; self.ready=not problems; self.health='Ready for supervised simulation' if not problems else 'Waiting for '+', '.join(problems)
                    if self.closed and shutdown_at is None: shutdown_at=now+9
                    if self.pending is not None:
                        dest=self.pending; self.pending=None
                        if self.cancel_requested or self.closed: self.mission.update(status='canceled',detail='Canceled before submission.')
                        elif not self.ready: self.mission.update(status='failed',detail=self.health)
                        else:
                            x,y,yaw=GOALS[dest]; goal=NavigateToPose.Goal(); goal.pose.header.frame_id='map'; goal.pose.header.stamp=node.get_clock().now().to_msg(); goal.pose.pose.position.x=float(x); goal.pose.pose.position.y=float(y); goal.pose.pose.position.z=0.0; goal.pose.pose.orientation.z=math.sin(math.radians(yaw)/2); goal.pose.pose.orientation.w=math.cos(math.radians(yaw)/2)
                            self.path=[]; cancel_deadline=0; send=client.send_goal_async(goal); deadline=now+240; handle=result=cancel_future=None
                    if send is not None and send.done():
                        handle=send.result(); send=None
                        if not handle or not handle.accepted: self.mission.update(status='failed',detail='Nav2 rejected goal.'); handle=None
                        else:
                            result=handle.get_result_async()
                            if not self.cancel_requested: self.mission.update(status='active',detail='Nav2 accepted goal; supervise in Gazebo.')
                    if (send is not None or result is not None) and (now>=deadline or not self.ready or self.closed): self.cancel_requested=True
                    if self.cancel_requested and (send is not None or result is not None):
                        if self.mission['status'] not in ('canceling','uncertain'): self.mission.update(status='canceling',detail='Stopping mission; awaiting confirmed result.')
                        if not cancel_deadline: cancel_deadline=now+10
                        if handle and cancel_future is None: cancel_future=handle.cancel_goal_async()
                        if now>cancel_deadline: self.mission.update(status='uncertain',detail='Cancellation not confirmed. Stop Nav2 and verify robot is stationary before restarting dashboard.')
                    if result is not None and result.done():
                        response=result.result(); status=response.status; detail=response.result
                        label='succeeded' if status==GoalStatus.STATUS_SUCCEEDED else 'canceled' if status==GoalStatus.STATUS_CANCELED else 'failed'
                        self.mission.update(status=label,detail='Nav2 reported arrival.' if label=='succeeded' else f'Nav2 status {status}; error {getattr(detail,"error_code",0)}: {getattr(detail,"error_msg","")}'); result=handle=cancel_future=None; cancel_deadline=0; self.cancel_requested=False
                    if shutdown_at and ((send is None and result is None) or now>shutdown_at): break
        except Exception as e:
            with self.lock:
                self.health=f'ROS adapter error: {e}'; self.ready=False
                if self.mission['status'] in ('queued','active','canceling'): self.mission.update(status='uncertain',detail='ROS adapter stopped. Verify robot is stationary; stop Nav2 before restart.')
        finally:
            if node: node.destroy_node()
            if rclpy and rclpy.ok(): rclpy.shutdown()
