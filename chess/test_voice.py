#!/usr/bin/env python
"""
语音功能测试脚本
测试跨平台语音输入和输出功能

用法:
    python test_voice.py [--mode voice|tts|stt|full] [--provider system|openai]
"""

import asyncio
import argparse
import sys
import os
import time

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ai.voice_system import (
    ChessVoiceSystem, VoiceSettings, VoiceProvider, 
    EmotionType, VoiceCommandRecognizer, create_voice_system
)

class VoiceTestSuite:
    """语音系统测试套件"""
    
    def __init__(self, provider: str = "system"):
        self.provider = VoiceProvider.SYSTEM if provider == "system" else VoiceProvider.OPENAI
        self.voice_system = None
        self.command_recognizer = None
        
    async def setup(self):
        """初始化测试环境"""
        print("🔧 初始化语音系统测试环境...")
        
        try:
            # 创建语音设置
            voice_settings = VoiceSettings(
                provider=self.provider,
                language="zh-CN",
                speed=1.0,
                emotion=EmotionType.FRIENDLY
            )
            
            # 创建语音系统
            self.voice_system = create_voice_system(
                voice_settings=voice_settings,
                enable_continuous_listening=False
            )
            
            # 创建指令识别器
            self.command_recognizer = VoiceCommandRecognizer()
            
            print(f"✅ 语音系统初始化成功 (提供商: {self.provider.value})")
            
            # 显示系统信息
            stats = self.voice_system.get_voice_stats()
            print(f"📊 系统信息:")
            print(f"  - 提供商: {stats['provider']}")
            print(f"  - 可用提供商: {stats['available_providers']}")
            print(f"  - 缓存目录: {stats['cache_directory']}")
            
        except Exception as e:
            print(f"❌ 语音系统初始化失败: {e}")
            raise
    
    async def test_tts(self):
        """测试文本转语音功能"""
        print("\n🔊 测试文本转语音 (TTS)...")
        
        test_messages = [
            ("欢迎使用国际象棋语音助手！", EmotionType.FRIENDLY),
            ("我正在思考最佳走法...", EmotionType.THINKING),
            ("太棒了！这是一步好棋！", EmotionType.EXCITED),
            ("让我为您分析当前局面。", EmotionType.SERIOUS),
            ("继续加油，您表现得很好！", EmotionType.ENCOURAGING)
        ]
        
        for i, (text, emotion) in enumerate(test_messages, 1):
            try:
                print(f"🎵 [{i}/{len(test_messages)}] 合成语音: '{text}' [{emotion.value}]")
                
                # 记录开始时间
                start_time = time.time()
                
                success = await self.voice_system.speak_async(
                    text, emotion, wait_for_completion=True
                )
                
                # 记录耗时
                duration = time.time() - start_time
                
                result = "✅ 成功" if success else "❌ 失败"
                print(f"   结果: {result} (耗时: {duration:.2f}s)")
                
                if success:
                    # 短暂暂停以便听清
                    await asyncio.sleep(1.0)
                else:
                    print(f"   详细错误信息已记录到日志")
                    
            except Exception as e:
                print(f"❌ 语音合成异常: {e}")
                import traceback
                traceback.print_exc()
        
        print("✅ TTS测试完成")
    
    async def test_stt(self):
        """测试语音转文本功能"""
        print("\n🎤 测试语音转文本 (STT)...")
        
        test_prompts = [
            "请说出一个象棋相关的词语",
            "请说出您想要执行的指令",
            "请随便说点什么"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🎯 [{i}/{len(test_prompts)}] {prompt}")
            
            try:
                # 语音提示
                await self.voice_system.speak_async(
                    f"{prompt}，我将在3秒内开始监听。", 
                    EmotionType.NEUTRAL, 
                    wait_for_completion=True
                )
                
                await asyncio.sleep(0.5)
                
                # 监听用户语音
                print("🎤 正在监听... (5秒内请说话)")
                result = await self.voice_system.listen_async(timeout=5.0, phrase_timeout=3.0)
                
                if result and result.text.strip():
                    text = result.text.strip()
                    confidence = result.confidence
                    
                    print(f"✅ 识别成功:")
                    print(f"   文本: {text}")
                    print(f"   置信度: {confidence:.2f}")
                    print(f"   语言: {result.language}")
                    
                    # 测试指令识别
                    if self.command_recognizer:
                        command = self.command_recognizer.recognize_command(text)
                        if command:
                            print(f"🎯 识别到指令: {command['command']}")
                        else:
                            print("💬 普通对话内容")
                    
                    # 语音回复确认
                    await self.voice_system.speak_async(
                        f"我听到您说: {text}", 
                        EmotionType.FRIENDLY,
                        wait_for_completion=True
                    )
                else:
                    print("❌ 未能识别到语音或识别超时")
                    
            except Exception as e:
                print(f"❌ 语音识别测试失败: {e}")
    
    async def test_voice_interaction(self):
        """测试完整语音交互"""
        print("\n🗣️ 测试完整语音交互...")
        
        def mock_response_handler(user_text: str) -> str:
            """模拟响应处理函数"""
            responses = {
                "你好": "你好！我是您的象棋语音助手。",
                "分析": "当前局面看起来很有趣，建议您考虑进攻策略。",
                "帮助": "我可以帮您分析局面、提供建议或回答象棋相关问题。",
                "再见": "再见！期待下次与您对弈！"
            }
            
            # 简单的关键词匹配
            user_lower = user_text.lower()
            for key, response in responses.items():
                if key in user_lower:
                    return response
            
            return f"我听到您说'{user_text}'。这很有趣！您还有其他问题吗？"
        
        try:
            print("🎙️ 开始语音交互测试...")
            
            user_text = await self.voice_system.voice_interaction(
                prompt="您好！我是象棋语音助手。请告诉我您需要什么帮助？",
                timeout=8.0,
                response_callback=mock_response_handler
            )
            
            if user_text:
                print(f"✅ 语音交互测试成功")
                print(f"   用户输入: {user_text}")
            else:
                print("❌ 语音交互测试失败或超时")
                
        except Exception as e:
            print(f"❌ 语音交互测试异常: {e}")
    
    async def test_voice_commands(self):
        """测试语音指令识别"""
        print("\n🎯 测试语音指令识别...")
        
        test_commands = [
            "开始新游戏",
            "悔棋",
            "分析当前局面", 
            "给我一些提示",
            "解释这步棋",
            "移动马到e4",
            "暂停游戏",
            "继续游戏"
        ]
        
        print("📝 测试预定义指令识别:")
        for command_text in test_commands:
            command = self.command_recognizer.recognize_command(command_text)
            if command:
                print(f"✅ '{command_text}' -> {command['command']}")
            else:
                print(f"❓ '{command_text}' -> 未识别")
    
    async def test_full_workflow(self):
        """测试完整工作流程"""
        print("\n🔄 测试完整语音工作流程...")
        
        try:
            # 1. 欢迎语音
            await self.voice_system.speak_async(
                "欢迎进行完整语音功能测试！", 
                EmotionType.FRIENDLY,
                wait_for_completion=True
            )
            
            # 2. 语音交互测试
            await self.test_voice_interaction()
            
            # 3. 指令测试
            await self.voice_system.speak_async(
                "现在请说出一个象棋指令，比如：开始游戏、分析局面等。", 
                EmotionType.NEUTRAL,
                wait_for_completion=True
            )
            
            result = await self.voice_system.listen_async(timeout=8.0)
            if result and result.text.strip():
                command = self.command_recognizer.recognize_command(result.text)
                if command:
                    response = f"我识别到您想要执行：{command['command']}"
                else:
                    response = f"我听到您说：{result.text}，但这不是一个象棋指令。"
                
                await self.voice_system.speak_async(response, EmotionType.FRIENDLY)
            
            # 4. 结束语音
            await self.voice_system.speak_async(
                "完整语音功能测试完成！感谢您的参与。", 
                EmotionType.CONGRATULATING,
                wait_for_completion=True
            )
            
            print("✅ 完整工作流程测试成功!")
            
        except Exception as e:
            print(f"❌ 完整工作流程测试失败: {e}")
    
    async def test_simple_voice(self):
        """简化语音测试（避免长时间阻塞）"""
        print("\n🎤 测试简化语音识别...")
        
        try:
            # 语音提示
            await self.voice_system.speak_async(
                "这是简化语音测试，将尝试短时间语音识别。", 
                EmotionType.NEUTRAL, 
                wait_for_completion=True
            )
            
            await asyncio.sleep(1.0)
            
            print("🎤 短时间语音识别测试 (3秒内请说话)...")
            result = await self.voice_system.listen_async(timeout=3.0, phrase_timeout=2.0)
            
            if result and result.text.strip():
                text = result.text.strip()
                confidence = result.confidence
                
                print(f"✅ 识别成功:")
                print(f"   文本: {text}")
                print(f"   置信度: {confidence:.2f}")
                
                # 简短回复
                await self.voice_system.speak_async(
                    f"收到：{text}", 
                    EmotionType.FRIENDLY,
                    wait_for_completion=True
                )
            else:
                print("⏰ 未检测到语音输入（这是正常的）")
                await self.voice_system.speak_async(
                    "未检测到语音输入，测试结束。", 
                    EmotionType.NEUTRAL,
                    wait_for_completion=True
                )
                
        except Exception as e:
            print(f"❌ 简化语音测试失败: {e}")
    
    async def test_simulated_workflow(self):
        """模拟工作流程测试（不进行实际语音识别）"""
        print("\n🔄 测试模拟语音工作流程...")
        
        try:
            # 1. 欢迎语音
            await self.voice_system.speak_async(
                "欢迎进行模拟语音功能测试！", 
                EmotionType.FRIENDLY,
                wait_for_completion=True
            )
            
            # 2. 模拟用户输入
            simulated_inputs = [
                "你好",
                "开始新游戏", 
                "分析当前局面",
                "给我一些提示",
                "再见"
            ]
            
            for i, user_input in enumerate(simulated_inputs, 1):
                print(f"🎭 [{i}/{len(simulated_inputs)}] 模拟用户输入: '{user_input}'")
                
                # 模拟语音识别结果
                await asyncio.sleep(0.5)
                
                # 测试指令识别
                if self.command_recognizer:
                    command = self.command_recognizer.recognize_command(user_input)
                    if command:
                        response = f"识别到指令：{command['command']}"
                        print(f"   🎯 指令识别: {command['command']}")
                    else:
                        response = f"收到消息：{user_input}"
                        print(f"   💬 普通对话")
                else:
                    response = f"收到：{user_input}"
                
                # 语音回复
                await self.voice_system.speak_async(response, EmotionType.FRIENDLY)
                await asyncio.sleep(1.0)
            
            # 3. 结束语音
            await self.voice_system.speak_async(
                "模拟语音功能测试完成！", 
                EmotionType.CONGRATULATING,
                wait_for_completion=True
            )
            
            print("✅ 模拟工作流程测试成功!")
            
        except Exception as e:
            print(f"❌ 模拟工作流程测试失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        print("\n🧹 清理测试资源...")
        try:
            if self.voice_system:
                self.voice_system.cleanup()
            print("✅ 清理完成")
        except Exception as e:
            print(f"⚠️ 清理时发生错误: {e}")

async def main():
    """主测试函数（改进版）"""
    import signal
    
    parser = argparse.ArgumentParser(description="语音功能测试脚本")
    parser.add_argument("--mode", choices=["voice", "tts", "stt", "full"], 
                       default="tts", help="测试模式（默认仅测试TTS）")
    parser.add_argument("--provider", choices=["system", "openai"], 
                       default="system", help="语音提供商")
    
    args = parser.parse_args()
    
    print("🎙️ 国际象棋语音功能测试")
    print("=" * 50)
    print(f"测试模式: {args.mode}")
    print(f"语音提供商: {args.provider}")
    print("=" * 50)
    
    # 创建测试套件
    test_suite = None
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        print(f"\n⏹️ 接收到停止信号 ({signum})，正在清理...")
        if test_suite:
            asyncio.create_task(test_suite.cleanup())
        sys.exit(0)
    
    # 注册信号处理器（Windows下仅支持SIGINT）
    try:
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    except Exception as e:
        print(f"警告: 信号处理器注册失败: {e}")
    
    try:
        # 创建测试套件
        test_suite = VoiceTestSuite(provider=args.provider)
        
        # 初始化（必须成功）
        await test_suite.setup()
        
        # 根据模式执行测试
        if args.mode == "tts" or args.mode == "voice" or args.mode == "full":
            print("\n🔊 开始TTS测试...")
            await test_suite.test_tts()
        
        # 仅在用户明确要求时进行STT测试（避免卡住）
        if args.mode == "stt":
            print("\n🎤 开始STT测试...")
            print("⚠️  注意：STT测试可能需要较长时间，请确保麦克风正常工作")
            await test_suite.test_stt()
        elif args.mode == "voice":
            print("\n🎤 开始简化语音测试...")
            await test_suite.test_simple_voice()
        elif args.mode == "full":
            print("\n🎯 开始指令识别测试...")
            await test_suite.test_voice_commands()
            
            # 仅进行模拟的完整测试，不实际进行语音识别
            print("\n🔄 开始模拟交互测试...")
            await test_suite.test_simulated_workflow()
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if test_suite:
            await test_suite.cleanup()
    
    print("\n🎉 语音功能测试完成!")

if __name__ == "__main__":
    # 运行测试
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 程序被中断")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")