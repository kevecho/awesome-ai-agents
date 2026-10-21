"""Agent 工具描述。"""


TOOL_DESCRIPTIONS_TEXT = """
## 可用工具

### search_knowledge（知识库检索）
搜索知识库，获取商品信息、平台政策和常见问题解答。
输入: 搜索查询字符串
输出: 相关知识库文档
适用场景: 用户询问商品详情、退换货政策、配送信息或一般性问题

### query_order（订单查询）
查询用户的订单详情，包括状态、物流和收货信息。
输入: 订单号（可选，不提供则列出所有订单）
输出: 订单详情或订单列表
适用场景: 用户询问订单状态、配送进度或想查看自己的订单

### query_product（商品搜索）
搜索商品目录。
输入: 商品关键词或分类
输出: 匹配的商品列表，含价格和库存信息
适用场景: 用户想找商品、查询价格或浏览品类

### refund（退款退货）
处理退款、退货和订单取消。
输入: 操作类型（取消/退货/退款/查询）和订单号
输出: 处理确认和后续步骤说明
适用场景: 用户想要取消订单、退货或查询退款信息

### transfer_human（转人工）
将用户转接给人工客服。
输入: 转接原因
输出: 队列位置和预计等待时间
适用场景: 用户明确要求人工服务、问题过于复杂或需要升级处理

### create_ticket（创建工单）
创建工单用于跟踪和后续处理。
输入: 工单类型、标题和描述
输出: 工单编号和确认信息
适用场景: 问题需要跟踪但不需要立即人工介入
"""


TOOL_JSON_SCHEMAS = [
    {
        "name": "search_knowledge",
        "description": "搜索知识库，获取商品信息、平台政策和常见问题解答",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"},
                "category": {"type": "string", "description": "可选的知识分类筛选"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "query_order",
        "description": "查询用户订单详情和状态",
        "parameters": {
            "type": "object",
            "properties": {
                "order_no": {"type": "string", "description": "订单号（可选）"},
            },
            "required": [],
        },
    },
    {
        "name": "query_product",
        "description": "搜索商品目录",
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "商品搜索关键词"},
                "category": {"type": "string", "description": "可选的商品分类"},
            },
            "required": ["keywords"],
        },
    },
    {
        "name": "refund",
        "description": "处理退款、退货和取消订单",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["cancel", "return", "refund", "query"],
                    "description": "操作类型",
                },
                "order_no": {"type": "string", "description": "订单号"},
                "reason": {"type": "string", "description": "操作原因"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "transfer_human",
        "description": "将用户转接给人工客服",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "enum": ["user_requested", "complaint", "technical_issue", "other"],
                    "description": "转接原因",
                },
            },
            "required": ["reason"],
        },
    },
    {
        "name": "create_ticket",
        "description": "创建工单用于跟踪处理",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["complaint", "refund", "consult", "suggestion"],
                    "description": "工单类型",
                },
                "title": {"type": "string", "description": "工单标题"},
                "content": {"type": "string", "description": "详细描述"},
            },
            "required": ["type", "content"],
        },
    },
]
