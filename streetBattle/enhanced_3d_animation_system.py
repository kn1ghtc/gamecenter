"""
增强型3D动画状态机系统
Enhanced 3D Animation State Machine System

解决3D角色动画状态管理、过渡和同步问题
Solves 3D character animation state management, transitions, and synchronization issues
"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from direct.actor.Actor import Actor
from panda3d.core import Vec3
import time


class AnimationState(Enum):
    """3D角色动画状态枚举"""
    IDLE = "idle"
    WALK = "walk"
    RUN = "run"
    JUMP = "jump"
    ATTACK_LIGHT = "light_attack"
    ATTACK_HEAVY = "heavy_attack"
    HURT = "hurt"
    KNOCKDOWN = "knockdown"
    VICTORY = "victory"
    DEFEAT = "defeat"
    BLOCK = "block"
    SPECIAL_MOVE = "special_move"


class AnimationTransition:
    """动画过渡配置"""
    def __init__(self, from_state: AnimationState, to_state: AnimationState, 
                 condition: Callable = None, priority: int = 1, 
                 transition_time: float = 0.1, interruptible: bool = True):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition or (lambda: True)
        self.priority = priority
        self.transition_time = transition_time
        self.interruptible = interruptible


class Enhanced3DAnimationStateMachine:
    """增强型3D动画状态机"""
    
    def __init__(self, actor: Actor, character_name: str = "Unknown"):
        self.actor = actor
        self.character_name = character_name
        self.current_state = AnimationState.IDLE
        self.previous_state = AnimationState.IDLE
        self.state_start_time = time.time()
        self.animation_queue = []
        self.state_timers = {}
        self.transitions = {}
        self.animation_speeds = {}
        self.loop_states = set()
        self.animation_callbacks = {}
        
        # 安全性和错误处理
        self.is_valid = self._validate_actor()
        self.error_count = 0
        self.max_errors = 10
        
        # 初始化状态机
        self._setup_default_animations()
        self._setup_default_transitions()
        self._setup_default_timers()
        
        print(f"✅ 3D动画状态机初始化完成: {character_name}")
    
    def _validate_actor(self) -> bool:
        """验证Actor对象的有效性"""
        try:
            if not self.actor:
                print(f"❌ Actor对象为空: {self.character_name}")
                return False
            
            if hasattr(self.actor, 'isEmpty') and self.actor.isEmpty():
                print(f"❌ Actor对象已删除: {self.character_name}")
                return False
            
            # 检查可用动画
            if hasattr(self.actor, 'getAnimNames'):
                anim_names = self.actor.getAnimNames()
                if anim_names:
                    print(f"📽️ 发现{len(anim_names)}个动画: {list(anim_names)}")
                else:
                    print(f"⚠️  {self.character_name}: 没有发现可用动画")
            
            return True
            
        except Exception as e:
            print(f"❌ Actor验证失败: {e}")
            return False
    
    def _setup_default_animations(self):
        """设置默认动画映射和配置"""
        # 标准动画速度
        self.animation_speeds = {
            AnimationState.IDLE: 1.0,
            AnimationState.WALK: 1.2,
            AnimationState.RUN: 1.5,
            AnimationState.JUMP: 1.0,
            AnimationState.ATTACK_LIGHT: 1.3,
            AnimationState.ATTACK_HEAVY: 1.0,
            AnimationState.HURT: 1.0,
            AnimationState.KNOCKDOWN: 0.8,
            AnimationState.VICTORY: 1.0,
            AnimationState.DEFEAT: 0.7,
            AnimationState.BLOCK: 1.0,
            AnimationState.SPECIAL_MOVE: 1.2
        }
        
        # 循环播放的状态
        self.loop_states = {
            AnimationState.IDLE,
            AnimationState.WALK,
            AnimationState.RUN,
            AnimationState.BLOCK
        }
    
    def _setup_default_transitions(self):
        """设置默认状态转换规则"""
        transitions = [
            # 从空闲状态的转换
            AnimationTransition(AnimationState.IDLE, AnimationState.WALK, priority=1),
            AnimationTransition(AnimationState.IDLE, AnimationState.JUMP, priority=2),
            AnimationTransition(AnimationState.IDLE, AnimationState.ATTACK_LIGHT, priority=3),
            AnimationTransition(AnimationState.IDLE, AnimationState.ATTACK_HEAVY, priority=3),
            
            # 从行走状态的转换
            AnimationTransition(AnimationState.WALK, AnimationState.IDLE, priority=1),
            AnimationTransition(AnimationState.WALK, AnimationState.RUN, priority=2),
            AnimationTransition(AnimationState.WALK, AnimationState.JUMP, priority=3),
            AnimationTransition(AnimationState.WALK, AnimationState.ATTACK_LIGHT, priority=4),
            
            # 攻击状态转换（允许返回IDLE，解决"状态转换被拒绝"问题）
            AnimationTransition(AnimationState.ATTACK_LIGHT, AnimationState.IDLE, priority=1, interruptible=True),
            AnimationTransition(AnimationState.ATTACK_HEAVY, AnimationState.IDLE, priority=1, interruptible=True),
            AnimationTransition(AnimationState.ATTACK_LIGHT, AnimationState.ATTACK_HEAVY, priority=2, interruptible=True),
            AnimationTransition(AnimationState.ATTACK_HEAVY, AnimationState.ATTACK_LIGHT, priority=2, interruptible=True),
            
            # 受伤状态转换
            AnimationTransition(AnimationState.HURT, AnimationState.IDLE, priority=1, interruptible=False),
            AnimationTransition(AnimationState.KNOCKDOWN, AnimationState.IDLE, priority=1, interruptible=False),
            
            # 跳跃状态转换
            AnimationTransition(AnimationState.JUMP, AnimationState.IDLE, priority=1),
            AnimationTransition(AnimationState.JUMP, AnimationState.ATTACK_LIGHT, priority=2),
        ]
        
        # 建立转换索引
        for transition in transitions:
            key = (transition.from_state, transition.to_state)
            self.transitions[key] = transition
    
    def _setup_default_timers(self):
        """设置默认状态持续时间"""
        self.state_timers = {
            AnimationState.ATTACK_LIGHT: 0.4,
            AnimationState.ATTACK_HEAVY: 0.6,
            AnimationState.HURT: 0.5,
            AnimationState.KNOCKDOWN: 1.2,
            AnimationState.JUMP: 0.8,
            AnimationState.SPECIAL_MOVE: 1.0,
            AnimationState.VICTORY: 2.0,
            AnimationState.DEFEAT: 2.5
        }
    
    def update(self, dt: float):
        """更新状态机"""
        if not self.is_valid:
            return
        
        try:
            current_time = time.time()
            state_duration = current_time - self.state_start_time
            
            # 检查是否需要自动状态转换（基于时间）
            if self.current_state in self.state_timers:
                max_duration = self.state_timers[self.current_state]
                if state_duration >= max_duration:
                    self._auto_transition_to_idle()
            
            # 处理动画队列
            self._process_animation_queue()
            
        except Exception as e:
            self._handle_error(f"状态机更新失败: {e}")
    
    def request_state_change(self, new_state: AnimationState, force: bool = False) -> bool:
        """请求状态改变"""
        if not self.is_valid:
            return False
        
        try:
            # 检查是否为相同状态
            if new_state == self.current_state and not force:
                return True
            
            # 检查转换是否允许
            if not force and not self._can_transition(self.current_state, new_state):
                print(f"⚠️  状态转换被拒绝: {self.current_state.value} -> {new_state.value}")
                return False
            
            # 执行状态转换
            return self._execute_state_change(new_state)
            
        except Exception as e:
            self._handle_error(f"状态改变请求失败: {e}")
            return False
    
    def _can_transition(self, from_state: AnimationState, to_state: AnimationState) -> bool:
        """检查状态转换是否允许 - 更灵活的转换逻辑"""
        transition_key = (from_state, to_state)
        
        # 允许优先级高的状态转换（如受伤、倒地）
        if to_state in [AnimationState.HURT, AnimationState.KNOCKDOWN, AnimationState.IDLE]:
            return True
        
        # 如果没有显式定义的转换规则，允许返回idle状态
        if transition_key not in self.transitions:
            if to_state == AnimationState.IDLE:
                return True
            # 对于没有定义转换规则的，使用时间判断
            if from_state in self.state_timers:
                current_time = time.time()
                state_duration = current_time - self.state_start_time
                min_duration = self.state_timers.get(from_state, 0)
                # 如果当前状态已经持续足够长时间，允许转换
                return state_duration >= min_duration * 0.5  # 50%最小时间后即可转换
            return False
        
        transition = self.transitions[transition_key]
        
        # 对于可打断的转换，直接允许
        if transition.interruptible:
            return transition.condition()
        
        # 对于不可打断的转换，检查最小持续时间
        current_time = time.time()
        state_duration = current_time - self.state_start_time
        min_duration = self.state_timers.get(from_state, 0)
        if state_duration < min_duration * 0.3:  # 必须至少完成30%的最小时间
            return False
        
        # 检查转换条件
        return transition.condition()
    
    def _execute_state_change(self, new_state: AnimationState) -> bool:
        """执行状态改变"""
        try:
            # 记录状态历史
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_start_time = time.time()
            
            # 播放对应动画
            success = self._play_animation_for_state(new_state)
            
            # 执行状态改变回调
            if new_state in self.animation_callbacks:
                try:
                    self.animation_callbacks[new_state]()
                except Exception as e:
                    print(f"⚠️  状态回调执行失败: {e}")
            
            if success:
                print(f"🎬 {self.character_name} 状态改变: {self.previous_state.value} -> {new_state.value}")
            
            return success
            
        except Exception as e:
            self._handle_error(f"状态改变执行失败: {e}")
            return False
    
    def _play_animation_for_state(self, state: AnimationState) -> bool:
        """为指定状态播放动画"""
        try:
            if not hasattr(self.actor, 'getAnimNames'):
                print(f"⚠️  Actor不支持动画播放")
                return False
            
            available_anims = list(self.actor.getAnimNames())
            if not available_anims:
                print(f"⚠️  没有可用动画")
                return False
            
            # 尝试寻找匹配的动画名称
            anim_name = self._find_animation_for_state(state, available_anims)
            
            if anim_name:
                # 设置播放参数
                loop = state in self.loop_states
                speed = self.animation_speeds.get(state, 1.0)
                
                # 停止当前动画并播放新动画
                self.actor.stop()
                self.actor.play(anim_name, loop=loop)
                self.actor.setPlayRate(speed, anim_name)
                
                print(f"🎭 播放动画: {anim_name} (循环:{loop}, 速度:{speed})")
                return True
            else:
                # 如果没有找到特定动画，播放第一个可用动画
                fallback_anim = available_anims[0]
                self.actor.stop()
                self.actor.play(fallback_anim, loop=True)
                print(f"🎭 播放备用动画: {fallback_anim}")
                return True
                
        except Exception as e:
            self._handle_error(f"动画播放失败: {e}")
            return False
    
    def _find_animation_for_state(self, state: AnimationState, available_anims: List[str]) -> Optional[str]:
        """为状态寻找最匹配的动画"""
        state_name = state.value.lower()
        
        # 精确匹配
        for anim in available_anims:
            if anim.lower() == state_name:
                return anim
        
        # 部分匹配
        for anim in available_anims:
            if state_name in anim.lower() or anim.lower() in state_name:
                return anim
        
        # 状态别名匹配
        aliases = {
            'idle': ['stand', 'rest', 'neutral'],
            'walk': ['move', 'step'],
            'run': ['sprint', 'dash'],
            'attack': ['hit', 'punch', 'strike'],
            'hurt': ['damage', 'pain', 'hit'],
            'jump': ['leap', 'hop']
        }
        
        for alias in aliases.get(state_name, []):
            for anim in available_anims:
                if alias in anim.lower():
                    return anim
        
        return None
    
    def _auto_transition_to_idle(self):
        """自动转换到空闲状态"""
        if self.current_state != AnimationState.IDLE:
            self.request_state_change(AnimationState.IDLE, force=True)
    
    def _process_animation_queue(self):
        """处理动画队列"""
        if self.animation_queue:
            next_anim = self.animation_queue.pop(0)
            self.request_state_change(next_anim)
    
    def queue_animation(self, state: AnimationState):
        """将动画加入队列"""
        self.animation_queue.append(state)
    
    def register_callback(self, state: AnimationState, callback: Callable):
        """注册状态改变回调"""
        self.animation_callbacks[state] = callback
    
    def get_current_state(self) -> AnimationState:
        """获取当前状态"""
        return self.current_state
    
    def get_state_duration(self) -> float:
        """获取当前状态持续时间"""
        return time.time() - self.state_start_time
    
    def is_state_finished(self) -> bool:
        """检查当前状态是否完成"""
        if self.current_state in self.state_timers:
            return self.get_state_duration() >= self.state_timers[self.current_state]
        return False
    
    def _handle_error(self, error_msg: str):
        """处理错误"""
        self.error_count += 1
        print(f"❌ {self.character_name} 动画状态机错误: {error_msg}")
        
        if self.error_count >= self.max_errors:
            print(f"❌ {self.character_name} 动画状态机错误过多，禁用中...")
            self.is_valid = False
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.actor and hasattr(self.actor, 'stop'):
                self.actor.stop()
            self.animation_callbacks.clear()
            self.animation_queue.clear()
            print(f"✅ 3D动画状态机清理完成: {self.character_name}")
        except Exception as e:
            print(f"⚠️  动画状态机清理警告: {e}")


class Animation3DManager:
    """3D动画管理器 - 管理多个角色的动画状态机"""
    
    def __init__(self):
        self.state_machines = {}
        self.last_update = time.time()
    
    def register_character(self, character_id: str, actor: Actor, character_name: str = None):
        """注册角色和其动画状态机"""
        try:
            name = character_name or character_id
            state_machine = Enhanced3DAnimationStateMachine(actor, name)
            self.state_machines[character_id] = state_machine
            print(f"✅ 注册3D角色动画: {character_id}")
            return state_machine
        except Exception as e:
            print(f"❌ 注册3D角色动画失败: {e}")
            return None
    
    def update_all(self, dt: float):
        """更新所有动画状态机"""
        current_time = time.time()
        actual_dt = current_time - self.last_update
        self.last_update = current_time
        
        for character_id, state_machine in self.state_machines.items():
            try:
                state_machine.update(actual_dt)
            except Exception as e:
                print(f"❌ 更新{character_id}动画状态机失败: {e}")
    
    def get_state_machine(self, character_id: str) -> Optional[Enhanced3DAnimationStateMachine]:
        """获取指定角色的状态机"""
        return self.state_machines.get(character_id)
    
    def cleanup(self):
        """清理所有状态机"""
        for state_machine in self.state_machines.values():
            state_machine.cleanup()
        self.state_machines.clear()
        print("✅ 3D动画管理器清理完成")