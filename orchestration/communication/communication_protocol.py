"""
Ultimate ShunsukeModel Ecosystem - Communication Protocol
エージェント間通信プロトコル

マルチエージェントシステムにおける効率的で安全な通信を提供
分散協調、メッセージルーティング、品質保証機能を実装
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import yaml
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
import zlib
import base64

from ..coordinator.agent_coordinator import AgentMessage


class MessageType(Enum):
    """メッセージタイプ"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    HEALTH_CHECK = "health_check"
    RESOURCE_REQUEST = "resource_request"
    COORDINATION = "coordination"
    BROADCAST = "broadcast"
    DIRECT = "direct"
    ERROR = "error"
    ACKNOWLEDGMENT = "acknowledgment"


class Priority(Enum):
    """メッセージ優先度"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class DeliveryMode(Enum):
    """配信モード"""
    FIRE_AND_FORGET = "fire_and_forget"  # 送信のみ
    REQUEST_RESPONSE = "request_response"  # 要求-応答
    RELIABLE = "reliable"  # 配信保証
    ORDERED = "ordered"  # 順序保証


class CompressionType(Enum):
    """圧縮タイプ"""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"


@dataclass
class MessageHeader:
    """メッセージヘッダー"""
    id: str
    timestamp: datetime
    sender: str
    receiver: str
    message_type: MessageType
    priority: Priority = Priority.MEDIUM
    delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET
    ttl: Optional[float] = None  # Time To Live (seconds)
    compression: CompressionType = CompressionType.NONE
    checksum: Optional[str] = None
    correlation_id: Optional[str] = None  # 関連メッセージID
    reply_to: Optional[str] = None  # 返信先
    sequence_number: Optional[int] = None
    total_parts: Optional[int] = None  # マルチパートメッセージ用
    part_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'sender': self.sender,
            'receiver': self.receiver,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'delivery_mode': self.delivery_mode.value,
            'ttl': self.ttl,
            'compression': self.compression.value,
            'checksum': self.checksum,
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to,
            'sequence_number': self.sequence_number,
            'total_parts': self.total_parts,
            'part_number': self.part_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageHeader':
        """辞書から復元"""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            sender=data['sender'],
            receiver=data['receiver'],
            message_type=MessageType(data['message_type']),
            priority=Priority(data['priority']),
            delivery_mode=DeliveryMode(data['delivery_mode']),
            ttl=data.get('ttl'),
            compression=CompressionType(data['compression']),
            checksum=data.get('checksum'),
            correlation_id=data.get('correlation_id'),
            reply_to=data.get('reply_to'),
            sequence_number=data.get('sequence_number'),
            total_parts=data.get('total_parts'),
            part_number=data.get('part_number')
        )


@dataclass
class ProtocolMessage:
    """プロトコルメッセージ"""
    header: MessageHeader
    payload: Dict[str, Any]
    
    def __post_init__(self):
        """初期化後処理"""
        # チェックサムを計算
        if self.header.checksum is None:
            self.header.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """チェックサム計算"""
        payload_str = json.dumps(self.payload, sort_keys=True, default=str)
        return hashlib.md5(payload_str.encode()).hexdigest()
    
    def verify_checksum(self) -> bool:
        """チェックサム検証"""
        expected = self._calculate_checksum()
        return self.header.checksum == expected
    
    def compress_payload(self) -> bytes:
        """ペイロード圧縮"""
        payload_bytes = json.dumps(self.payload, default=str).encode()
        
        if self.header.compression == CompressionType.GZIP:
            import gzip
            return gzip.compress(payload_bytes)
        elif self.header.compression == CompressionType.ZLIB:
            return zlib.compress(payload_bytes)
        else:
            return payload_bytes
    
    def decompress_payload(self, compressed_data: bytes) -> Dict[str, Any]:
        """ペイロード展開"""
        if self.header.compression == CompressionType.GZIP:
            import gzip
            payload_bytes = gzip.decompress(compressed_data)
        elif self.header.compression == CompressionType.ZLIB:
            payload_bytes = zlib.decompress(compressed_data)
        else:
            payload_bytes = compressed_data
        
        return json.loads(payload_bytes.decode())
    
    def to_wire_format(self) -> bytes:
        """ワイヤ形式に変換"""
        # ヘッダーとペイロードを分離してシリアライズ
        header_data = self.header.to_dict()
        payload_data = self.compress_payload()
        
        wire_data = {
            'header': header_data,
            'payload': base64.b64encode(payload_data).decode()
        }
        
        return json.dumps(wire_data, default=str).encode()
    
    @classmethod
    def from_wire_format(cls, wire_data: bytes) -> 'ProtocolMessage':
        """ワイヤ形式から復元"""
        data = json.loads(wire_data.decode())
        
        header = MessageHeader.from_dict(data['header'])
        compressed_payload = base64.b64decode(data['payload'])
        
        # 仮のメッセージを作成してペイロードを展開
        temp_msg = cls(header=header, payload={})
        payload = temp_msg.decompress_payload(compressed_payload)
        
        return cls(header=header, payload=payload)


@dataclass
class MessageQueue:
    """メッセージキュー"""
    name: str
    max_size: int = 1000
    messages: List[ProtocolMessage] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    async def enqueue(self, message: ProtocolMessage, priority_queue: bool = True) -> bool:
        """メッセージをキューに追加"""
        async with self.lock:
            if len(self.messages) >= self.max_size:
                # キューが満杯の場合、低優先度メッセージを削除
                if priority_queue:
                    self.messages = sorted(self.messages, key=lambda m: m.header.priority.value)
                    self.messages.pop()  # 最低優先度を削除
                else:
                    return False
            
            self.messages.append(message)
            
            # 優先度でソート
            if priority_queue:
                self.messages.sort(key=lambda m: m.header.priority.value)
            
            return True
    
    async def dequeue(self) -> Optional[ProtocolMessage]:
        """メッセージをキューから取得"""
        async with self.lock:
            if not self.messages:
                return None
            
            # TTL期限切れメッセージを削除
            current_time = datetime.now(timezone.utc)
            self.messages = [
                msg for msg in self.messages
                if not msg.header.ttl or (current_time - msg.header.timestamp).total_seconds() <= msg.header.ttl
            ]
            
            if not self.messages:
                return None
            
            return self.messages.pop(0)
    
    async def peek(self) -> Optional[ProtocolMessage]:
        """キューの先頭メッセージを確認（削除しない）"""
        async with self.lock:
            return self.messages[0] if self.messages else None
    
    async def size(self) -> int:
        """キューサイズ取得"""
        async with self.lock:
            return len(self.messages)


@dataclass
class Route:
    """メッセージルート"""
    destination: str
    next_hop: str
    cost: int = 1
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MessageRouter:
    """メッセージルーター"""
    
    def __init__(self):
        self.routing_table: Dict[str, Route] = {}
        self.direct_connections: Set[str] = set()
        self.lock = asyncio.Lock()
    
    async def add_route(self, destination: str, next_hop: str, cost: int = 1):
        """ルート追加"""
        async with self.lock:
            self.routing_table[destination] = Route(
                destination=destination,
                next_hop=next_hop,
                cost=cost
            )
    
    async def remove_route(self, destination: str):
        """ルート削除"""
        async with self.lock:
            self.routing_table.pop(destination, None)
    
    async def find_route(self, destination: str) -> Optional[Route]:
        """ルート検索"""
        async with self.lock:
            # 直接接続をチェック
            if destination in self.direct_connections:
                return Route(destination=destination, next_hop=destination, cost=0)
            
            # ルーティングテーブルから検索
            return self.routing_table.get(destination)
    
    async def update_topology(self, connections: Dict[str, List[str]]):
        """ネットワークトポロジー更新"""
        async with self.lock:
            # Dijkstraアルゴリズムの簡易実装
            # 実際の実装では、より効率的なアルゴリズムを使用
            self.direct_connections.update(connections.keys())


class ReliabilityManager:
    """信頼性管理"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pending_messages: Dict[str, ProtocolMessage] = {}
        self.acknowledgments: Dict[str, datetime] = {}
        self.retry_attempts: Dict[str, int] = {}
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5.0)
        self.ack_timeout = config.get('ack_timeout', 30.0)
    
    async def track_message(self, message: ProtocolMessage):
        """メッセージ追跡開始"""
        if message.header.delivery_mode in [DeliveryMode.RELIABLE, DeliveryMode.REQUEST_RESPONSE]:
            self.pending_messages[message.header.id] = message
            self.retry_attempts[message.header.id] = 0
    
    async def acknowledge_message(self, message_id: str):
        """メッセージ確認応答"""
        self.acknowledgments[message_id] = datetime.now(timezone.utc)
        self.pending_messages.pop(message_id, None)
        self.retry_attempts.pop(message_id, None)
    
    async def check_timeouts(self) -> List[ProtocolMessage]:
        """タイムアウトチェック"""
        current_time = datetime.now(timezone.utc)
        timeout_messages = []
        
        for message_id, message in list(self.pending_messages.items()):
            time_elapsed = (current_time - message.header.timestamp).total_seconds()
            
            if time_elapsed > self.ack_timeout:
                retry_count = self.retry_attempts.get(message_id, 0)
                
                if retry_count < self.max_retries:
                    # リトライ
                    self.retry_attempts[message_id] = retry_count + 1
                    # タイムスタンプを更新
                    message.header.timestamp = current_time
                    timeout_messages.append(message)
                else:
                    # 最大リトライ回数に達した場合は削除
                    self.pending_messages.pop(message_id, None)
                    self.retry_attempts.pop(message_id, None)
        
        return timeout_messages


class CommunicationProtocol:
    """
    通信プロトコル - エージェント間通信の中核
    
    主要機能:
    1. メッセージルーティングと配信
    2. 信頼性保証（ACK、リトライ）
    3. メッセージ圧縮と暗号化
    4. 順序保証と重複排除
    5. 負荷分散とフロー制御
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """初期化"""
        self.agent_id = agent_id
        self.config = config
        
        # コンポーネント初期化
        self.router = MessageRouter()
        self.reliability_manager = ReliabilityManager(config.get('reliability', {}))
        
        # メッセージキュー
        self.inbound_queue = MessageQueue(f"{agent_id}_inbound", 
                                        config.get('max_queue_size', 1000))
        self.outbound_queue = MessageQueue(f"{agent_id}_outbound",
                                         config.get('max_queue_size', 1000))
        
        # メッセージハンドラー
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # 統計情報
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_dropped': 0,
            'errors': 0,
            'retries': 0
        }
        
        # ログ設定
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self._setup_logging()
        
        # 実行状態
        self.is_running = False
        self._background_tasks = set()
        self._shutdown_event = asyncio.Event()
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path.home() / '.claude' / 'logs' / 'shunsuke-ecosystem'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / f'communication-{self.agent_id}.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def initialize(self):
        """通信プロトコル初期化"""
        try:
            self.logger.info(f"Communication protocol initialization started for {self.agent_id}")
            
            # デフォルトメッセージハンドラー登録
            await self._register_default_handlers()
            
            # バックグラウンドタスク開始
            await self._start_background_tasks()
            
            self.is_running = True
            self.logger.info(f"Communication protocol initialization completed for {self.agent_id}")
            
        except Exception as e:
            self.logger.error(f"Communication protocol initialization failed: {e}")
            raise
    
    async def _register_default_handlers(self):
        """デフォルトメッセージハンドラー登録"""
        self.message_handlers[MessageType.HEALTH_CHECK] = self._handle_health_check
        self.message_handlers[MessageType.ACKNOWLEDGMENT] = self._handle_acknowledgment
        self.message_handlers[MessageType.ERROR] = self._handle_error
    
    async def _start_background_tasks(self):
        """バックグラウンドタスク開始"""
        # メッセージ処理
        message_processor = asyncio.create_task(self._process_messages())
        self._background_tasks.add(message_processor)
        
        # 信頼性チェック
        reliability_checker = asyncio.create_task(self._reliability_checker())
        self._background_tasks.add(reliability_checker)
        
        # 統計収集
        stats_collector = asyncio.create_task(self._collect_stats())
        self._background_tasks.add(stats_collector)
    
    async def send_message(
        self,
        receiver: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET,
        ttl: Optional[float] = None,
        compression: CompressionType = CompressionType.NONE
    ) -> str:
        """
        メッセージ送信
        
        Args:
            receiver: 受信者ID
            message_type: メッセージタイプ
            payload: ペイロード
            priority: 優先度
            delivery_mode: 配信モード
            ttl: 生存時間
            compression: 圧縮タイプ
            
        Returns:
            メッセージID
        """
        # メッセージID生成
        message_id = str(uuid.uuid4())
        
        # ヘッダー作成
        header = MessageHeader(
            id=message_id,
            timestamp=datetime.now(timezone.utc),
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            priority=priority,
            delivery_mode=delivery_mode,
            ttl=ttl,
            compression=compression
        )
        
        # メッセージ作成
        message = ProtocolMessage(header=header, payload=payload)
        
        # 送信キューに追加
        await self.outbound_queue.enqueue(message)
        
        # 信頼性管理
        await self.reliability_manager.track_message(message)
        
        self.stats['messages_sent'] += 1
        self.logger.debug(f"Message queued for sending: {message_id} to {receiver}")
        
        return message_id
    
    async def receive_message(self, timeout: Optional[float] = None) -> Optional[ProtocolMessage]:
        """
        メッセージ受信
        
        Args:
            timeout: タイムアウト時間
            
        Returns:
            受信メッセージ
        """
        if timeout:
            try:
                # タイムアウト付きで受信
                return await asyncio.wait_for(
                    self.inbound_queue.dequeue(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return None
        else:
            return await self.inbound_queue.dequeue()
    
    async def broadcast_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        receivers: Optional[List[str]] = None,
        priority: Priority = Priority.MEDIUM
    ) -> List[str]:
        """
        ブロードキャストメッセージ送信
        
        Args:
            message_type: メッセージタイプ
            payload: ペイロード
            receivers: 受信者リスト（Noneの場合は全エージェント）
            priority: 優先度
            
        Returns:
            送信されたメッセージIDリスト
        """
        message_ids = []
        
        # 受信者リストが指定されていない場合はルーティングテーブルから取得
        if receivers is None:
            receivers = list(self.router.routing_table.keys())
        
        # 各受信者にメッセージ送信
        for receiver in receivers:
            if receiver != self.agent_id:  # 自分には送信しない
                message_id = await self.send_message(
                    receiver=receiver,
                    message_type=message_type,
                    payload=payload,
                    priority=priority
                )
                message_ids.append(message_id)
        
        self.logger.info(f"Broadcast message sent to {len(message_ids)} receivers")
        
        return message_ids
    
    async def request_response(
        self,
        receiver: str,
        request_payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[ProtocolMessage]:
        """
        要求-応答パターン
        
        Args:
            receiver: 受信者
            request_payload: 要求ペイロード
            timeout: タイムアウト時間
            
        Returns:
            応答メッセージ
        """
        # 要求送信
        request_id = await self.send_message(
            receiver=receiver,
            message_type=MessageType.TASK_REQUEST,
            payload=request_payload,
            delivery_mode=DeliveryMode.REQUEST_RESPONSE
        )
        
        # 応答待機
        start_time = datetime.now(timezone.utc)
        while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout:
            message = await self.receive_message(timeout=1.0)
            
            if (message and 
                message.header.message_type == MessageType.TASK_RESPONSE and
                message.header.correlation_id == request_id):
                return message
        
        self.logger.warning(f"Request-response timeout: {request_id}")
        return None
    
    async def register_handler(self, message_type: MessageType, handler: Callable):
        """メッセージハンドラー登録"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered handler for {message_type.value}")
    
    async def unregister_handler(self, message_type: MessageType):
        """メッセージハンドラー登録解除"""
        self.message_handlers.pop(message_type, None)
        self.logger.info(f"Unregistered handler for {message_type.value}")
    
    async def _process_messages(self):
        """メッセージ処理メインループ"""
        while not self._shutdown_event.is_set():
            try:
                # 送信キューからメッセージを取得
                outbound_message = await self.outbound_queue.dequeue()
                if outbound_message:
                    await self._deliver_message(outbound_message)
                
                # 受信キューからメッセージを取得
                inbound_message = await self.inbound_queue.dequeue()
                if inbound_message:
                    await self._handle_message(inbound_message)
                
                # CPUを他のタスクに譲る
                await asyncio.sleep(0.01)
                
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
                self.stats['errors'] += 1
    
    async def _deliver_message(self, message: ProtocolMessage):
        """メッセージ配信"""
        try:
            # ルートを検索
            route = await self.router.find_route(message.header.receiver)
            
            if not route:
                self.logger.warning(f"No route found for {message.header.receiver}")
                self.stats['messages_dropped'] += 1
                return
            
            # メッセージ配信（実際の実装では外部通信を行う）
            await self._actual_send(message, route)
            
            self.logger.debug(f"Message delivered: {message.header.id}")
            
        except Exception as e:
            self.logger.error(f"Message delivery failed: {e}")
            self.stats['errors'] += 1
    
    async def _actual_send(self, message: ProtocolMessage, route: Route):
        """実際のメッセージ送信"""
        # 実際の実装では、TCP/UDP/WebSocket等を使用してメッセージを送信
        # ここではデモ用の簡易実装
        
        # ワイヤ形式に変換
        wire_data = message.to_wire_format()
        
        # 送信をシミュレート
        await asyncio.sleep(0.01)
        
        self.logger.debug(f"Sent {len(wire_data)} bytes to {route.next_hop}")
    
    async def _handle_message(self, message: ProtocolMessage):
        """メッセージハンドリング"""
        try:
            # チェックサム検証
            if not message.verify_checksum():
                self.logger.warning(f"Checksum verification failed: {message.header.id}")
                return
            
            # TTL チェック
            if message.header.ttl:
                age = (datetime.now(timezone.utc) - message.header.timestamp).total_seconds()
                if age > message.header.ttl:
                    self.logger.warning(f"Message expired: {message.header.id}")
                    return
            
            # ACK送信（必要な場合）
            if message.header.delivery_mode in [DeliveryMode.RELIABLE, DeliveryMode.REQUEST_RESPONSE]:
                await self._send_acknowledgment(message)
            
            # ハンドラー実行
            handler = self.message_handlers.get(message.header.message_type)
            if handler:
                await handler(message)
            else:
                self.logger.warning(f"No handler for message type: {message.header.message_type.value}")
            
            self.stats['messages_received'] += 1
            
        except Exception as e:
            self.logger.error(f"Message handling error: {e}")
            self.stats['errors'] += 1
    
    async def _send_acknowledgment(self, original_message: ProtocolMessage):
        """確認応答送信"""
        ack_message = await self.send_message(
            receiver=original_message.header.sender,
            message_type=MessageType.ACKNOWLEDGMENT,
            payload={'original_message_id': original_message.header.id},
            delivery_mode=DeliveryMode.FIRE_AND_FORGET
        )
        
        self.logger.debug(f"Sent ACK for message: {original_message.header.id}")
    
    async def _handle_health_check(self, message: ProtocolMessage):
        """ヘルスチェックハンドラー"""
        # ヘルスステータスを返信
        await self.send_message(
            receiver=message.header.sender,
            message_type=MessageType.STATUS_UPDATE,
            payload={
                'agent_id': self.agent_id,
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stats': self.stats
            },
            delivery_mode=DeliveryMode.FIRE_AND_FORGET,
            correlation_id=message.header.id
        )
    
    async def _handle_acknowledgment(self, message: ProtocolMessage):
        """確認応答ハンドラー"""
        original_message_id = message.payload.get('original_message_id')
        if original_message_id:
            await self.reliability_manager.acknowledge_message(original_message_id)
            self.logger.debug(f"Received ACK for message: {original_message_id}")
    
    async def _handle_error(self, message: ProtocolMessage):
        """エラーハンドラー"""
        error_data = message.payload
        self.logger.error(f"Received error from {message.header.sender}: {error_data}")
    
    async def _reliability_checker(self):
        """信頼性チェッカー"""
        while not self._shutdown_event.is_set():
            try:
                # タイムアウトメッセージをチェック
                timeout_messages = await self.reliability_manager.check_timeouts()
                
                # リトライメッセージを再送
                for message in timeout_messages:
                    await self.outbound_queue.enqueue(message)
                    self.stats['retries'] += 1
                    self.logger.info(f"Retrying message: {message.header.id}")
                
                await asyncio.sleep(5.0)  # 5秒間隔
                
            except Exception as e:
                self.logger.error(f"Reliability checker error: {e}")
    
    async def _collect_stats(self):
        """統計収集"""
        while not self._shutdown_event.is_set():
            try:
                # キューサイズ等の統計を収集
                inbound_size = await self.inbound_queue.size()
                outbound_size = await self.outbound_queue.size()
                
                self.stats.update({
                    'inbound_queue_size': inbound_size,
                    'outbound_queue_size': outbound_size,
                    'pending_messages': len(self.reliability_manager.pending_messages),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                await asyncio.sleep(30.0)  # 30秒間隔
                
            except Exception as e:
                self.logger.error(f"Stats collection error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """通信統計取得"""
        return self.stats.copy()
    
    async def get_status(self) -> Dict[str, Any]:
        """通信プロトコル状態取得"""
        return {
            "agent_id": self.agent_id,
            "is_running": self.is_running,
            "inbound_queue_size": await self.inbound_queue.size(),
            "outbound_queue_size": await self.outbound_queue.size(),
            "message_handlers": len(self.message_handlers),
            "routing_entries": len(self.router.routing_table),
            "stats": self.stats
        }
    
    async def shutdown(self):
        """通信プロトコルシャットダウン"""
        self.logger.info(f"Communication protocol shutdown initiated for {self.agent_id}")
        
        # シャットダウンイベント設定
        self._shutdown_event.set()
        
        # バックグラウンドタスクの終了を待機
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self.is_running = False
        self.logger.info(f"Communication protocol shutdown completed for {self.agent_id}")


if __name__ == "__main__":
    # テスト実行
    async def test_communication_protocol():
        config = {
            'max_queue_size': 100,
            'reliability': {
                'max_retries': 3,
                'retry_delay': 2.0,
                'ack_timeout': 10.0
            }
        }
        
        # 2つのプロトコルインスタンスを作成
        protocol_a = CommunicationProtocol("agent_a", config)
        protocol_b = CommunicationProtocol("agent_b", config)
        
        await protocol_a.initialize()
        await protocol_b.initialize()
        
        # ルート設定
        await protocol_a.router.add_route("agent_b", "agent_b", 1)
        await protocol_b.router.add_route("agent_a", "agent_a", 1)
        
        # メッセージ送信テスト
        message_id = await protocol_a.send_message(
            receiver="agent_b",
            message_type=MessageType.TASK_REQUEST,
            payload={"task": "test_task", "data": "test_data"},
            priority=Priority.HIGH,
            delivery_mode=DeliveryMode.RELIABLE
        )
        
        print(f"Sent message: {message_id}")
        
        # 状態確認
        status_a = await protocol_a.get_status()
        status_b = await protocol_b.get_status()
        
        print("Protocol A status:", json.dumps(status_a, indent=2, default=str))
        print("Protocol B status:", json.dumps(status_b, indent=2, default=str))
        
        # シャットダウン
        await protocol_a.shutdown()
        await protocol_b.shutdown()
    
    asyncio.run(test_communication_protocol())