-- 用户表
CREATE TABLE `users` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `email` VARCHAR(100) UNIQUE COMMENT '邮箱',
    `phone` VARCHAR(20) UNIQUE COMMENT '手机号',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `user_type` ENUM('customer', 'agent', 'admin') DEFAULT 'customer' COMMENT '用户类型',
    `avatar_url` VARCHAR(500) COMMENT '头像URL',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_username` (`username`),
    INDEX `idx_phone` (`phone`),
    INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 会话表
CREATE TABLE `sessions` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '会话ID',
    `session_id` VARCHAR(64) NOT NULL UNIQUE COMMENT '会话唯一标识',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `agent_id` BIGINT COMMENT '分配的Agent ID',
    `status` ENUM('active', 'waiting', 'transferred', 'closed') DEFAULT 'active' COMMENT '会话状态',
    `channel` VARCHAR(20) DEFAULT 'web' COMMENT '来源渠道',
    `started_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    `ended_at` DATETIME COMMENT '结束时间',
    `last_message_at` DATETIME COMMENT '最后消息时间',
    `message_count` INT DEFAULT 0 COMMENT '消息数量',
    `satisfaction_score` TINYINT COMMENT '满意度评分',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_session_id` (`session_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';

-- 消息表
CREATE TABLE `messages` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    `session_id` BIGINT NOT NULL COMMENT '会话ID',
    `sender_type` ENUM('user', 'bot', 'agent') NOT NULL COMMENT '发送者类型',
    `sender_id` BIGINT COMMENT '发送者ID',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `content_type` ENUM('text', 'image', 'voice', 'file', 'quick_reply') DEFAULT 'text' COMMENT '内容类型',
    `intent_id` BIGINT COMMENT '识别的意图ID',
    `intent_confidence` DECIMAL(5,4) COMMENT '意图置信度',
    `sentiment` ENUM('positive', 'neutral', 'negative') COMMENT '情感倾向',
    `sentiment_score` DECIMAL(3,2) COMMENT '情感得分',
    `is_human_transfer` BOOLEAN DEFAULT FALSE COMMENT '是否转人工',
    `is_generated` BOOLEAN DEFAULT FALSE COMMENT '是否AI生成',
    `metadata` JSON COMMENT '元数据',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`intent_id`) REFERENCES `intents`(`id`) ON DELETE SET NULL,
    INDEX `idx_session_id` (`session_id`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_sender_type` (`sender_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- 意图表
CREATE TABLE `intents` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '意图ID',
    `intent_name` VARCHAR(100) NOT NULL COMMENT '意图名称',
    `intent_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '意图编码',
    `description` VARCHAR(255) COMMENT '意图描述',
    `handler_type` ENUM('rag', 'tool', 'transfer', 'fallback') NOT NULL COMMENT '处理类型',
    `handler_config` JSON COMMENT '处理配置',
    `sample_utterances` TEXT COMMENT '示例语料',
    `priority` INT DEFAULT 0 COMMENT '优先级',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_intent_code` (`intent_code`),
    INDEX `idx_handler_type` (`handler_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='意图表';

-- 知识库表
CREATE TABLE `knowledge` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '知识ID',
    `category` VARCHAR(50) NOT NULL COMMENT '知识分类',
    `question` TEXT NOT NULL COMMENT '问题',
    `answer` TEXT NOT NULL COMMENT '答案',
    `keywords` VARCHAR(500) COMMENT '关键词',
    `vector_id` VARCHAR(100) COMMENT '向量数据库ID',
    `embedding_model` VARCHAR(50) DEFAULT 'text-embedding-ada-002' COMMENT '向量化模型',
    `hit_count` INT DEFAULT 0 COMMENT '命中次数',
    `satisfaction_rate` DECIMAL(5,2) COMMENT '满意度',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_category` (`category`),
    INDEX `idx_keywords` (`keywords`(255)),
    FULLTEXT `ft_question` (`question`, `keywords`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库表';

-- 订单表
CREATE TABLE `orders` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
    `order_no` VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `status` ENUM('pending', 'paid', 'shipped', 'delivered', 'completed', 'cancelled', 'refunded') DEFAULT 'pending' COMMENT '订单状态',
    `total_amount` DECIMAL(10,2) NOT NULL COMMENT '订单总金额',
    `pay_amount` DECIMAL(10,2) COMMENT '实付金额',
    `shipping_address` JSON COMMENT '收货地址',
    `receiver_name` VARCHAR(50) COMMENT '收货人',
    `receiver_phone` VARCHAR(20) COMMENT '联系电话',
    `tracking_no` VARCHAR(50) COMMENT '物流单号',
    `remark` TEXT COMMENT '订单备注',
    `paid_at` DATETIME COMMENT '支付时间',
    `shipped_at` DATETIME COMMENT '发货时间',
    `delivered_at` DATETIME COMMENT '收货时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_order_no` (`order_no`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- 商品表
CREATE TABLE `products` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '商品ID',
    `sku` VARCHAR(50) NOT NULL UNIQUE COMMENT '商品SKU',
    `name` VARCHAR(200) NOT NULL COMMENT '商品名称',
    `category` VARCHAR(50) NOT NULL COMMENT '商品分类',
    `brand` VARCHAR(50) COMMENT '品牌',
    `price` DECIMAL(10,2) NOT NULL COMMENT '售价',
    `original_price` DECIMAL(10,2) COMMENT '原价',
    `stock` INT DEFAULT 0 COMMENT '库存',
    `sales_count` INT DEFAULT 0 COMMENT '销量',
    `description` TEXT COMMENT '商品描述',
    `specifications` JSON COMMENT '规格参数',
    `images` JSON COMMENT '图片列表',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否上架',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_sku` (`sku`),
    INDEX `idx_category` (`category`),
    INDEX `idx_name` (`name`),
    FULLTEXT `ft_name_desc` (`name`, `description`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品表';

-- 工单表
CREATE TABLE `tickets` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '工单ID',
    `ticket_no` VARCHAR(32) NOT NULL UNIQUE COMMENT '工单号',
    `session_id` BIGINT COMMENT '关联会话ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `type` ENUM('complaint', 'refund', 'consult', 'suggestion', 'other') NOT NULL COMMENT '工单类型',
    `title` VARCHAR(200) NOT NULL COMMENT '工单标题',
    `content` TEXT NOT NULL COMMENT '工单内容',
    `status` ENUM('pending', 'processing', 'resolved', 'closed') DEFAULT 'pending' COMMENT '处理状态',
    `priority` ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' COMMENT '优先级',
    `assigned_to` BIGINT COMMENT '处理人',
    `resolution` TEXT COMMENT '处理结果',
    `resolved_at` DATETIME COMMENT '解决时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_ticket_no` (`ticket_no`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单表';