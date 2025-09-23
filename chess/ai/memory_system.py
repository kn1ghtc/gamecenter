"""
Chess AI Agent 记忆系统 (Memory System)
基于ChromaDB和LanceDB的RAG向量记忆系统

核心功能：
- 持久化向量存储（游戏记录、对话历史、策略学习）
- 语义相似度搜索和智能检索
- 重要度评分和记忆管理
- 多类型记忆分类存储
- Langchain集成支持
"""

import json
import os
import time
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict

# Langchain和向量数据库
try:
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    import chromadb
    from chromadb.config import Settings
    VECTOR_DB_AVAILABLE = True
    print("✅ ChromaDB和Langchain可用（新API）")
except ImportError as e:
    print(f"⚠️ 新版本依赖不可用，尝试备用导入: {e}")
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        import chromadb
        from chromadb.config import Settings
        VECTOR_DB_AVAILABLE = True
        print("✅ 使用备用Langchain导入")
    except ImportError as e2:
        print(f"❌ 向量数据库完全不可用: {e2}")
        VECTOR_DB_AVAILABLE = False

# 备用嵌入模型
SENTENCE_TRANSFORMERS_AVAILABLE = False  # 禁用sentence_transformers避免soundfile问题

@dataclass
class ChessMemory:
    """象棋记忆数据类"""
    id: str
    content: str
    memory_type: str  # 'game', 'conversation', 'strategy', 'learning', 'tactic'
    importance: float  # 0.0-1.0
    timestamp: datetime
    context: Dict[str, Any]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    embedding_id: Optional[str] = None  # 向量数据库中的ID
    
    def to_document(self) -> Document:
        """转换为Langchain Document"""
        metadata = {
            'id': self.id,
            'memory_type': self.memory_type,
            'importance': self.importance,
            'timestamp': self.timestamp.isoformat(),
            'access_count': self.access_count,
            'context': json.dumps(self.context) if self.context else '{}'
        }
        return Document(page_content=self.content, metadata=metadata)

class ChessMemorySystem:
    """Chess AI Agent 记忆系统"""
    
    def __init__(self,
                 memory_dir: str = None,
                 embedding_model: str = "openai",  # 'openai' 或 'huggingface'
                 collection_name: str = "chess_memories",
                 max_memories: int = 10000,
                 fast_start: bool = False,
                 strict_vector: bool = True):
        """
        初始化记忆系统
        
        Args:
            memory_dir: 记忆数据存储目录（默认为项目下的chess_memory_companion）
            embedding_model: 嵌入模型类型
            collection_name: ChromaDB集合名称
            max_memories: 最大记忆数量
        """
        # 如果没有指定路径，使用项目目录下的默认路径
        if memory_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            chess_dir = os.path.dirname(current_dir)  # 到chess目录
            memory_dir = os.path.join(chess_dir, "chess_memory_companion")
        
        self.memory_dir = memory_dir
        self.collection_name = collection_name
        self.max_memories = max_memories
        self.embedding_model_name = embedding_model
        self.fast_start = fast_start
        self.strict_vector = strict_vector
        
        # 创建存储目录
        os.makedirs(memory_dir, exist_ok=True)
        
        # 初始化向量数据库和嵌入模型
        self.vector_store = None
        self.embeddings = None
        self.chroma_client = None
        
        # 记忆索引（用于快速查找）
        self.memory_index: Dict[str, ChessMemory] = {}
        self.metadata_file = os.path.join(memory_dir, "memory_metadata.json")
        
        # 配置参数
        self.cleanup_threshold = 0.8
        self.importance_decay_rate = 0.95
        
        # 统计信息
        self.stats = {
            'memories_stored': 0,
            'memories_retrieved': 0,
            'searches_performed': 0,
            'vector_searches': 0,
            'cache_hits': 0
        }
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
        
        # 日志设置
        self.logger = logging.getLogger(f"ChessMemorySystem_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # 初始化系统（快速启动时仅加载元数据，延迟向量库）
        self._initialize_system()

        self.logger.info(f"Chess记忆系统初始化完成")
        # 运行期保护：避免外部证书错误反复刷屏
        self._suppress_ssl_errors = False
    
    def _initialize_system(self):
        """初始化记忆系统"""
        try:
            if not VECTOR_DB_AVAILABLE or self.fast_start:
                self.logger.info("快速启动：仅加载元数据，延迟初始化向量库")
                self._load_metadata()
                return
            
            # 初始化嵌入模型
            self._initialize_embeddings()
            
            # 初始化ChromaDB
            self._initialize_chroma()
            
            # 加载现有记忆
            self._load_memories()
            
        except Exception as e:
            self.logger.error(f"记忆系统初始化失败: {e}")
            self.vector_store = None
    
    def _initialize_embeddings(self):
        """初始化嵌入模型"""
        try:
            if self.embedding_model_name == "openai":
                # 使用OpenAI嵌入，参考langchain_rag的配置
                api_key = os.getenv("OPENAI_API_KEY")
                
                if not api_key:
                    self.logger.warning("OpenAI API密钥未设置，切换到轻量级嵌入")
                    self.embedding_model_name = "huggingface"
                else:
                    # 使用正确的OpenAI嵌入配置，参考langchain_rag
                    self.embeddings = OpenAIEmbeddings(
                        api_key=api_key,
                        model="text-embedding-ada-002"  # 使用稳定的ada-002模型
                    )
                    self.logger.info(f"使用OpenAI嵌入模型: text-embedding-ada-002")
                    return
            
            if self.embedding_model_name == "huggingface":
                # 使用轻量级嵌入模型，避免torch依赖
                try:
                    from langchain_community.embeddings import FakeEmbeddings
                    self.embeddings = FakeEmbeddings(size=384)
                    self.logger.info("使用轻量级嵌入模型（测试模式）")
                    return
                except ImportError:
                    # 如果FakeEmbeddings不可用，使用HuggingFace
                    model_name = "sentence-transformers/all-MiniLM-L6-v2"
                    
                    # 尝试创建不依赖soundfile的嵌入模型
                    self.embeddings = HuggingFaceEmbeddings(
                        model_name=model_name,
                        model_kwargs={
                            'device': 'cpu',
                            'trust_remote_code': False
                        },
                        encode_kwargs={'batch_size': 1}  # 小批次避免内存问题
                    )
                    self.logger.info(f"使用HuggingFace嵌入模型: {model_name}")
                    return
                
        except Exception as e:
            self.logger.error(f"嵌入模型初始化失败: {e}")
            # 不设置为None，而是尝试使用基础HuggingFace模型
            try:
                from langchain_community.embeddings import FakeEmbeddings
                self.embeddings = FakeEmbeddings(size=384)
                self.logger.info("使用备用轻量级嵌入模型")
            except Exception as e2:
                self.logger.error(f"备用嵌入模型也失败: {e2}")
                self.embeddings = None
    
    def _initialize_chroma(self):
        """初始化ChromaDB"""
        try:
            # ChromaDB持久化配置
            chroma_db_path = os.path.join(self.memory_dir, "chromadb")
            
            # 创建ChromaDB客户端
            self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
            
            # 初始化向量存储，即使无嵌入模型也尝试初始化
            try:
                self.vector_store = Chroma(
                    client=self.chroma_client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=chroma_db_path
                )
                self.logger.info(f"ChromaDB向量存储初始化成功: {chroma_db_path}")
            except Exception as e:
                self.logger.warning(f"向量存储初始化失败，尝试无嵌入模式: {e}")
                # 如果嵌入函数有问题，尝试不使用嵌入函数
                if "embedding" in str(e).lower():
                    self.vector_store = None
                    self.logger.info("使用基础ChromaDB模式（无向量搜索）")
                else:
                    raise e
            
        except Exception as e:
            self.logger.error(f"ChromaDB完全初始化失败: {e}")
            self.vector_store = None
            self.chroma_client = None

    def _ensure_vector_store(self):
        """按需初始化向量存储（用于fast_start模式）"""
        if self.vector_store is None and not getattr(self, '_suppress_ssl_errors', False):
            try:
                if not VECTOR_DB_AVAILABLE:
                    return
                # 初始化嵌入与Chroma
                self._initialize_embeddings()
                self._initialize_chroma()
            except Exception as e:
                self.logger.warning(f"延迟初始化向量库失败: {e}")
    
    def store_memory(self, 
                    content: str, 
                    memory_type: str = 'general',
                    importance: float = 0.5,
                    context: Optional[Dict[str, Any]] = None) -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要度 (0.0-1.0)
            context: 上下文信息
            
        Returns:
            记忆ID
        """
        try:
            # 生成唯一ID
            memory_id = str(uuid.uuid4())[:16]
            
            # 创建记忆对象
            memory = ChessMemory(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                importance=importance,
                timestamp=datetime.now(),
                context=context or {}
            )
            
            # 存储到向量数据库（按需初始化）
            if not getattr(self, '_suppress_ssl_errors', False):
                self._ensure_vector_store()
            if self.vector_store and not getattr(self, '_suppress_ssl_errors', False):
                try:
                    documents = [memory.to_document()]
                    embedding_ids = self.vector_store.add_documents(documents)
                    if embedding_ids:
                        memory.embedding_id = embedding_ids[0]
                        self.stats['vector_searches'] += 1
                except Exception as e:
                    msg = str(e)
                    self.logger.warning(f"向量存储失败: {e}")
                    # 针对 tiktoken 证书问题，降级一次，后续不再尝试
                    if 'tiktoken' in msg or 'CERTIFICATE_VERIFY_FAILED' in msg or 'openaipublic.blob.core.windows.net' in msg:
                        self._suppress_ssl_errors = True
                        self.logger.warning("检测到外部证书/tiktoken问题：已暂时关闭向量写入，改用本地索引，避免刷屏。")
            
            # 存储到内存索引
            self.memory_index[memory_id] = memory
            self.stats['memories_stored'] += 1
            
            # 检查清理
            if len(self.memory_index) > self.max_memories * self.cleanup_threshold:
                self._cleanup_memories()
            
            # 保存元数据
            self._save_metadata()
            
            self.logger.debug(f"存储记忆: {memory_id} - {content[:50]}...")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"存储记忆失败: {e}")
            return ""
    
    def search_memories(self, 
                       query: str, 
                       memory_type: Optional[str] = None,
                       limit: int = 5,
                       min_importance: float = 0.1,
                       similarity_threshold: float = 0.7) -> List[ChessMemory]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            memory_type: 记忆类型过滤
            limit: 返回结果数量
            min_importance: 最小重要度
            similarity_threshold: 相似度阈值
            
        Returns:
            匹配的记忆列表
        """
        try:
            self.stats['searches_performed'] += 1
            
            if self.fast_start and not getattr(self, '_suppress_ssl_errors', False) and self.vector_store is None:
                # 首次搜索时尝试延迟初始化
                self._ensure_vector_store()
            if not self.vector_store:
                if self.strict_vector:
                    return []
                return self._fallback_search(query, memory_type, limit, min_importance)
            # 如果已检测到外部证书问题，直接使用回退搜索，避免重复错误
            if getattr(self, '_suppress_ssl_errors', False):
                if self.strict_vector:
                    return []
                return self._fallback_search(query, memory_type, limit, min_importance)
            
            # 构建过滤条件（Chroma新API使用filter语法；避免多个操作符直接并列）
            filter_dict = None
            conditions = []
            if memory_type:
                conditions.append({"memory_type": memory_type})
            if min_importance > 0:
                conditions.append({"importance": {"$gte": min_importance}})
            if len(conditions) == 1:
                filter_dict = conditions[0]
            elif len(conditions) > 1:
                filter_dict = {"$and": conditions}
            
            # 向量相似度搜索
            docs = []
            try:
                docs = self.vector_store.similarity_search(
                    query=query,
                    k=max(limit * 2, 4),  # 获取更多结果用于过滤
                    filter=filter_dict
                )
            except Exception as e:
                msg = str(e)
                self.logger.error(f"记忆搜索失败: {e}")
                if 'tiktoken' in msg or 'CERTIFICATE_VERIFY_FAILED' in msg or 'openaipublic.blob.core.windows.net' in msg:
                    self._suppress_ssl_errors = True
                    if self.strict_vector:
                        return []
                    return self._fallback_search(query, memory_type, limit, min_importance)
            
            # 转换为记忆对象并更新访问统计
            results = []
            for doc in docs[:limit]:
                memory_id = doc.metadata.get('id')
                if memory_id in self.memory_index:
                    memory = self.memory_index[memory_id]
                    memory.access_count += 1
                    memory.last_accessed = datetime.now()
                    results.append(memory)
                    self.stats['memories_retrieved'] += 1
            
            self.logger.debug(f"向量搜索: '{query}' 找到 {len(results)} 条结果")
            return results
            
        except Exception as e:
            self.logger.error(f"记忆搜索失败: {e}")
            if self.strict_vector:
                return []
            return self._fallback_search(query, memory_type, limit, min_importance)
    
    def _fallback_search(self, query: str, memory_type: Optional[str], 
                        limit: int, min_importance: float) -> List[ChessMemory]:
        """备用搜索（关键词匹配）"""
        try:
            query_lower = query.lower()
            candidates = []
            
            for memory in self.memory_index.values():
                if memory_type and memory.memory_type != memory_type:
                    continue
                if memory.importance < min_importance:
                    continue
                
                # 简单的关键词匹配
                content_lower = memory.content.lower()
                if query_lower in content_lower:
                    score = memory.importance
                    candidates.append((score, memory))
            
            # 排序并返回
            candidates.sort(key=lambda x: x[0], reverse=True)
            results = [memory for _, memory in candidates[:limit]]
            
            # 更新访问统计
            for memory in results:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                self.stats['memories_retrieved'] += 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"备用搜索失败: {e}")
            return []
    
    def get_memory_by_id(self, memory_id: str) -> Optional[ChessMemory]:
        """根据ID获取记忆"""
        memory = self.memory_index.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self.stats['memories_retrieved'] += 1
        return memory
    
    def get_memories_by_type(self, memory_type: str, limit: int = 10) -> List[ChessMemory]:
        """根据类型获取记忆"""
        memories = [
            memory for memory in self.memory_index.values()
            if memory.memory_type == memory_type
        ]
        
        # 按重要度和时间排序
        memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        return memories[:limit]
    
    def update_memory_importance(self, memory_id: str, new_importance: float) -> bool:
        """更新记忆重要度"""
        if memory_id not in self.memory_index:
            return False
        
        memory = self.memory_index[memory_id]
        memory.importance = max(0.0, min(1.0, new_importance))
        
        # 同步到向量数据库
        if self.vector_store and memory.embedding_id:
            try:
                # 重新添加文档（ChromaDB会更新现有文档）
                self.vector_store.add_documents([memory.to_document()])
            except Exception as e:
                self.logger.warning(f"向量数据库同步失败: {e}")
        
        self._save_metadata()
        return True
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id not in self.memory_index:
            return False
        
        memory = self.memory_index[memory_id]
        
        # 从向量数据库删除
        if self.vector_store and memory.embedding_id:
            try:
                self.vector_store.delete([memory.embedding_id])
            except Exception as e:
                self.logger.warning(f"向量数据库删除失败: {e}")
        
        # 从索引删除
        del self.memory_index[memory_id]
        self._save_metadata()
        return True
    
    def _cleanup_memories(self):
        """清理低重要度的旧记忆"""
        if len(self.memory_index) <= self.max_memories * 0.5:
            return
        
        # 计算清理分数
        memories_list = list(self.memory_index.values())
        
        def cleanup_score(memory):
            age_factor = (datetime.now() - memory.timestamp).days * 0.01
            access_factor = min(1.0, memory.access_count / 10.0)
            return memory.importance * access_factor * max(0.1, 1.0 - age_factor)
        
        memories_list.sort(key=cleanup_score, reverse=True)
        
        # 保留70%的记忆
        keep_count = int(len(memories_list) * 0.7)
        memories_to_keep = memories_list[:keep_count]
        memories_to_delete = memories_list[keep_count:]
        
        # 删除记忆
        for memory in memories_to_delete:
            self.delete_memory(memory.id)
        
        self.logger.info(f"记忆清理完成，删除 {len(memories_to_delete)} 条记忆")
    
    def _save_metadata(self):
        """保存记忆元数据"""
        try:
            metadata = {
                'memories': {
                    memory_id: {
                        'id': memory.id,
                        'content': memory.content,
                        'memory_type': memory.memory_type,
                        'importance': memory.importance,
                        'timestamp': memory.timestamp.isoformat(),
                        'context': memory.context,
                        'access_count': memory.access_count,
                        'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None,
                        'embedding_id': memory.embedding_id
                    }
                    for memory_id, memory in self.memory_index.items()
                },
                'stats': self.stats,
                'version': '2.0'
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存元数据失败: {e}")
    
    def _load_memories(self):
        """加载记忆"""
        try:
            self._load_metadata()
            
            # 如果有向量存储，验证一致性
            if self.vector_store and not self.fast_start:
                try:
                    # 获取向量存储中的文档数量
                    collection = self.chroma_client.get_collection(self.collection_name)
                    vector_count = collection.count()
                    memory_count = len(self.memory_index)
                    
                    if vector_count != memory_count:
                        self.logger.warning(f"数据不一致: 向量存储有{vector_count}条，内存有{memory_count}条")
                        # 可以选择重建索引或修复数据
                    
                except Exception as e:
                    self.logger.warning(f"数据验证失败: {e}")
            
        except Exception as e:
            self.logger.error(f"加载记忆失败: {e}")
    
    def _load_metadata(self):
        """加载记忆元数据"""
        try:
            if not os.path.exists(self.metadata_file):
                return
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载记忆
            for memory_id, memory_data in data.get('memories', {}).items():
                memory = ChessMemory(
                    id=memory_data['id'],
                    content=memory_data['content'],
                    memory_type=memory_data['memory_type'],
                    importance=memory_data['importance'],
                    timestamp=datetime.fromisoformat(memory_data['timestamp']),
                    context=memory_data['context'],
                    access_count=memory_data.get('access_count', 0),
                    embedding_id=memory_data.get('embedding_id')
                )
                
                if memory_data.get('last_accessed'):
                    memory.last_accessed = datetime.fromisoformat(memory_data['last_accessed'])
                
                self.memory_index[memory_id] = memory
            
            # 加载统计信息
            self.stats.update(data.get('stats', {}))
            
        except Exception as e:
            self.logger.error(f"加载元数据失败: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        memory_types = defaultdict(int)
        importance_distribution = defaultdict(int)
        
        for memory in self.memory_index.values():
            memory_types[memory.memory_type] += 1
            importance_range = round(memory.importance, 1)
            importance_distribution[importance_range] += 1
        
        return {
            **self.stats,
            'total_memories': len(self.memory_index),
            'memory_types': dict(memory_types),
            'importance_distribution': dict(importance_distribution),
            'vector_store_available': self.vector_store is not None,
            'embedding_model': self.embedding_model_name,
            'storage_path': self.memory_dir,
            'strict_vector': self.strict_vector
        }
    
    def export_memories(self, export_file: str, format: str = 'json') -> bool:
        """导出记忆"""
        try:
            if format == 'json':
                export_data = {
                    'exported_at': datetime.now().isoformat(),
                    'total_memories': len(self.memory_index),
                    'memories': [
                        {
                            'content': memory.content,
                            'type': memory.memory_type,
                            'importance': memory.importance,
                            'timestamp': memory.timestamp.isoformat(),
                            'access_count': memory.access_count,
                            'context': memory.context
                        }
                        for memory in self.memory_index.values()
                    ]
                }
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"记忆导出完成: {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"记忆导出失败: {e}")
            return False

# 工厂函数
def create_chess_memory_system(
    memory_dir: str = None,
    embedding_model: str = "openai",
    fast_start: bool = False,
    strict_vector: bool = True
) -> ChessMemorySystem:
    """创建Chess记忆系统"""
    return ChessMemorySystem(
        memory_dir=memory_dir,
        embedding_model=embedding_model,
        fast_start=fast_start,
        strict_vector=strict_vector
    )

# 测试和演示
if __name__ == "__main__":
    print("🧪 测试Chess记忆系统...")
    
    # 创建记忆系统
    memory_system = create_chess_memory_system(
        memory_dir="test_memory",
        embedding_model="huggingface"  # 测试时使用免费模型
    )
    
    print("✅ 记忆系统创建成功")
    
    # 存储测试记忆
    memories = [
        ("在开局阶段，控制中心很重要，特别是e4和d4格子", "strategy", 0.8),
        ("玩家刚才使用了西西里防御，这是一个很有攻击性的开局", "game", 0.7),
        ("骑士叉王是一个常见的战术，可以同时攻击王和其他棋子", "tactic", 0.9),
        ("玩家问了关于残局技巧的问题，特别是王兵对王的残局", "conversation", 0.6)
    ]
    
    memory_ids = []
    for content, mem_type, importance in memories:
        memory_id = memory_system.store_memory(
            content, mem_type, importance,
            context={'source': 'test', 'session': 'demo'}
        )
        memory_ids.append(memory_id)
        print(f"✅ 存储记忆: {memory_id[:8]}... - {content[:30]}...")
    
    # 搜索测试
    print("\n🔍 搜索测试:")
    search_queries = [
        "开局策略和中心控制",
        "战术和叉王",
        "残局技巧",
        "西西里防御"
    ]
    
    for query in search_queries:
        results = memory_system.search_memories(query, limit=2)
        print(f"  查询: '{query}'")
        for result in results:
            print(f"    📝 {result.content[:50]}... (重要度: {result.importance})")
    
    # 按类型搜索
    print("\n📂 按类型搜索:")
    for mem_type in ['strategy', 'tactic', 'game']:
        results = memory_system.get_memories_by_type(mem_type, limit=2)
        print(f"  类型: {mem_type}")
        for result in results:
            print(f"    📋 {result.content[:40]}...")
    
    # 统计信息
    stats = memory_system.get_memory_stats()
    print(f"\n📊 统计信息:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}: {dict(value)}")
        else:
            print(f"  {key}: {value}")
    
    print("\n🎉 记忆系统测试完成!")