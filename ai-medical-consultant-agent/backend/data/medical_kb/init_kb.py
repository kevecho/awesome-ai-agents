# ============================================================
# AI Medical Consultant - 医学知识库初始化脚本
# ============================================================
"""
初始化医学知识库 - 导入示例医学知识到RAG向量数据库

使用方法:
    cd backend
    python -m data.medical_kb.init_kb
"""
import asyncio
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.services.rag_service import rag_service
from app.models.database import KnowledgeDocument, SyncSessionLocal


# ==================== 示例医学知识数据 ====================

MEDICAL_KNOWLEDGE = [
    # === 疾病知识 ===
    {
        "title": "普通感冒",
        "category": "disease",
        "content": """
普通感冒（Common Cold）是由病毒引起的上呼吸道感染，是最常见的急性呼吸道疾病。

【病因】主要由鼻病毒、冠状病毒等引起。通过飞沫传播或接触传播。

【症状】
- 早期：咽部干燥、咽痒、打喷嚏
- 中期：鼻塞、流涕、咳嗽、声音嘶哑
- 全身症状：轻度发热（通常<38.5°C）、乏力、头痛

【病程】通常持续5-7天，具有自限性。

【治疗】
- 对症治疗：休息、多饮水
- 解热镇痛：对乙酰氨基酚（扑热息痛）或布洛芬
- 鼻塞：伪麻黄碱类滴鼻剂
- 咳嗽：右美沙芬类止咳药
- 抗生素无效（感冒是病毒性的，除非合并细菌感染）

【预防】
- 勤洗手
- 避免接触感冒患者
- 保持室内通风
- 增强免疫力：规律作息、均衡饮食、适度运动

【何时就医】
- 发热超过3天不退
- 呼吸困难、胸痛
- 症状严重或持续加重
- 婴幼儿、老年人、孕妇等特殊人群
        """.strip(),
    },
    {
        "title": "高血压",
        "category": "disease",
        "content": """
高血压（Hypertension）是指动脉血压持续升高的慢性疾病。

【诊断标准】收缩压≥140mmHg和/或舒张压≥90mmHg（诊室测量，非同日3次测量）

【分级】
- 1级（轻度）：140-159 / 90-99 mmHg
- 2级（中度）：160-179 / 100-109 mmHg
- 3级（重度）：≥180 / ≥110 mmHg

【症状】
- 多数患者早期无明显症状
- 可能出现：头晕、头痛、颈项板紧、疲劳、心悸
- 严重时：视力模糊、鼻出血、胸闷

【危险因素】
- 高盐饮食、肥胖、缺乏运动、吸烟
- 精神紧张、遗传因素、年龄增长

【并发症】
- 心脑血管疾病：脑卒中、心肌梗死、心力衰竭
- 肾脏损害：高血压肾病
- 眼部损害：高血压视网膜病变

【治疗】
1. 生活方式干预（所有患者的基础治疗）
   - 低盐饮食（每日<6g盐）
   - 控制体重（BMI<24）
   - 规律运动（每周≥150分钟）
   - 戒烟限酒
2. 药物治疗（需要医生处方）
   - ACEI/ARB类
   - CCB类（钙通道阻滞剂）
   - 利尿剂
   - β受体阻滞剂

【预防】健康饮食、定期测量血压、保持健康体重
        """.strip(),
    },
    {
        "title": "糖尿病",
        "category": "disease",
        "content": """
糖尿病（Diabetes Mellitus）是一种以高血糖为特征的代谢性疾病。

【类型】
- 1型糖尿病：胰岛素绝对缺乏，多见于青少年
- 2型糖尿病：胰岛素抵抗和/或分泌不足，占90%以上，多见于成人
- 妊娠期糖尿病：妊娠期间发生

【诊断标准】
- 空腹血糖≥7.0 mmol/L
- 或OGTT 2小时血糖≥11.1 mmol/L
- 或HbA1c≥6.5%
- 或有典型症状+随机血糖≥11.1 mmol/L

【典型症状】"三多一少"
- 多饮（口渴多喝水）
- 多食（容易饿）
- 多尿（频繁排尿）
- 体重下降

【其他症状】乏力、视力模糊、伤口愈合慢、皮肤瘙痒、手脚麻木

【并发症】
- 急性：糖尿病酮症酸中毒、高渗高血糖状态
- 慢性微血管：视网膜病变、肾病、神经病变
- 慢性大血管：心梗、脑卒中、下肢血管病变
- 糖尿病足（严重可致截肢）

【治疗】
1. 饮食控制：控制总热量，均衡营养
2. 运动疗法
3. 口服降糖药：二甲双胍（一线用药）
4. 胰岛素治疗
5. 血糖监测

【预防】健康饮食、规律运动、控制体重、定期体检
        """.strip(),
    },
    {
        "title": "急性胃肠炎",
        "category": "disease",
        "content": """
急性胃肠炎（Acute Gastroenteritis）是胃肠黏膜的急性炎症。

【病因】
- 病毒感染（最常见）：诺如病毒、轮状病毒
- 细菌感染：沙门氏菌、大肠杆菌、金黄色葡萄球菌
- 不洁饮食、食物中毒

【症状】
- 恶心、呕吐
- 腹痛、腹泻（水样便）
- 可能伴发热（通常<38.5°C）
- 脱水症状：口干、少尿、乏力

【病程】通常1-3天，具有自限性

【治疗】
- 补液最重要：口服补液盐（ORS）
- 清淡饮食：白粥、面条、香蕉、烤面包（BRAT饮食）
- 止泻：蒙脱石散
- 益生菌辅助
- 避免：奶制品、油腻食物、辛辣食物
- 抗生素：仅在明确细菌感染时由医生开具

【何时就医】
- 持续呕吐不能进食水
- 严重脱水（口干、尿少、精神差）
- 高热不退
- 便血、剧烈腹痛
- 婴幼儿、老年人
        """.strip(),
    },

    # === 药品说明 ===
    {
        "title": "布洛芬",
        "category": "drug",
        "content": """
布洛芬（Ibuprofen）是非甾体抗炎药（NSAID）。

【适应症】解热、镇痛、抗炎
- 轻中度疼痛：头痛、牙痛、关节痛、肌肉痛、痛经
- 发热：各种原因引起的发热

【用法用量】（成人）
- 解热镇痛：每次200-400mg，每6-8小时一次，每日不超过1200mg
- 餐后服用减轻胃部刺激

【禁忌症】
- 对阿司匹林或其他NSAID过敏
- 活动性消化道溃疡/出血
- 严重心/肝/肾功能不全
- 妊娠晚期

【不良反应】
- 胃肠道：恶心、胃痛、消化不良（最常见）
- 少见：头晕、皮疹、肝功能异常
- 严重：消化道出血、肾损害（尤其在老年人）

【注意事项】
- 最小有效剂量、最短疗程
- 避免与其他NSAID同时使用
- 有胃病史者慎用
- 不宜长期使用（>10天需咨询医生）
        """.strip(),
    },
    {
        "title": "对乙酰氨基酚",
        "category": "drug",
        "content": """
对乙酰氨基酚（Paracetamol/Acetaminophen，俗称扑热息痛）。

【适应症】解热、镇痛
- 头痛、牙痛、痛经、肌肉痛
- 感冒/流感引起的发热

【与布洛芬的区别】
- 对乙酰氨基酚：几乎无抗炎作用，对胃肠道刺激小
- 布洛芬：有抗炎作用，但胃肠道副作用更大

【用法用量】（成人）
- 每次500-1000mg，每4-6小时一次
- 每日不超过4000mg（4g）
- 过量可致严重肝损伤！

【禁忌症】
- 严重肝功能不全
- G6PD缺乏症（蚕豆病）

【不良反应】
- 常规剂量：较少不良反应
- 过量：肝毒性（可能致命）
- 偶有皮疹

【注意事项】
- 严格按剂量服用，避免超量
- 多种复方感冒药含此成分，避免重复用药
- 服药期间禁酒
- 持续发热>3天需就医
        """.strip(),
    },

    # === 检查指标 ===
    {
        "title": "血常规检查",
        "category": "exam",
        "content": """
血常规（Complete Blood Count, CBC）是最基础的血液检查。

【主要指标及正常值】
- 白细胞（WBC）：4.0-10.0 × 10⁹/L
  升高：感染、炎症、应激
  降低：病毒感染、药物影响、造血功能障碍

- 红细胞（RBC）：4.0-5.5 × 10¹²/L（男），3.5-5.0 × 10¹²/L（女）
  降低：贫血

- 血红蛋白（Hb）：120-160 g/L（男），110-150 g/L（女）
  降低：贫血；升高：脱水、缺氧

- 血小板（PLT）：100-300 × 10⁹/L
  降低：出血风险增加
  升高：血栓风险增加

- 中性粒细胞百分比：50%-70%
  升高：细菌感染

- 淋巴细胞百分比：20%-40%
  升高：病毒感染

【注意事项】需空腹采血（至少8小时禁食）
        """.strip(),
    },

    # === 临床指南 ===
    {
        "title": "发热处理指南",
        "category": "guideline",
        "content": """
发热（Fever）处理临床指南要点：

【定义】
- 低热：37.3-38.0°C
- 中等度热：38.1-39.0°C
- 高热：39.1-41.0°C
- 超高热：>41.0°C

【发热的分级处理】
1. <38.5°C且无明显不适
   - 多饮水、物理降温（温水擦浴）
   - 暂不用退热药

2. 38.5-39.0°C
   - 对乙酰氨基酚 或 布洛芬
   - 配合物理降温

3. >39.0°C或伴明显不适
   - 退热药物
   - 建议就医

【紧急就医指征】
- 婴幼儿（<3个月）发热
- 持续高热>3天
- 伴头痛剧烈、颈项强直
- 伴随惊厥、意识改变
- 发热伴皮疹
- 免疫缺陷患者
        """.strip(),
    },
]


async def init():
    """初始化知识库"""
    print("=" * 60)
    print("初始化医学知识库...")
    print("=" * 60)

    await rag_service.initialize()

    texts = [item["content"] for item in MEDICAL_KNOWLEDGE]
    metadatas = [
        {"title": item["title"], "category": item["category"], "source": "init_kb"}
        for item in MEDICAL_KNOWLEDGE
    ]

    # Step 1: 添加到FAISS向量索引
    count = await rag_service.add_documents(texts, metadatas)
    print(f"[OK] FAISS indexed {count} documents")

    # Step 2: 同步写入数据库表
    db_count = 0
    with SyncSessionLocal() as db:
        for item in MEDICAL_KNOWLEDGE:
            # 检查是否已存在（按title去重）
            existing = db.query(KnowledgeDocument).where(
                KnowledgeDocument.title == item["title"]
            ).first()
            if existing:
                continue
            doc = KnowledgeDocument(
                title=item["title"],
                category=item["category"],
                content=item["content"],
            )
            db.add(doc)
            db_count += 1
        db.commit()
    print(f"[OK] Database saved {db_count} documents")

    print(f"  FAISS vectors: {rag_service.index.ntotal if rag_service.index else 0}")
    print(f"  DB documents:  {db_count}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(init())
