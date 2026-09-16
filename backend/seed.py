"""Seed mock data: merchants, products (vector-indexed), sessions, messages, orders.

Usage:
    python seed.py           # clear existing data and regenerate
    python seed.py --keep    # keep existing data, only append
"""
import argparse
import sys
from pathlib import Path

# Make `app` importable when running from backend/
sys.path.insert(0, str(Path(__file__).parent))

from app.storage.database import Base, SessionLocal, engine, init_db
from app.storage.models import Merchant, Product, Order, OrderItem, Session, Message
from app.rag.product_indexer import index_product
from app.core.vector_store import reset_collection


# --------------------------------------------------------------------------
# Mock data definitions
# --------------------------------------------------------------------------

MERCHANTS = [
    {
        "name": "数码旗舰店",
        "description": "主营智能音箱、耳机等数码影音产品,官方授权,正品保障",
        "products": [
            {
                "name": "智能云音箱 Pro",
                "description": "4英寸全频单元,30W大功率,支持语音助手,适合卧室听音乐和智能家居控制",
                "price": "499.00",
                "specs": "尺寸:180x90x90mm;重量:1.2kg;蓝牙5.0;WiFi双频;功率:30W",
                "stock": 50,
            },
            {
                "name": "智能云音箱 Lite",
                "description": "3英寸单元,15W功率,入门级智能音箱,支持语音助手,适合小空间使用",
                "price": "199.00",
                "specs": "尺寸:120x80x80mm;重量:0.6kg;蓝牙5.0;WiFi;功率:15W",
                "stock": 120,
            },
            {
                "name": "智能云音箱 Max",
                "description": "双5英寸低音单元,60W大功率,360°环绕音效,客厅影院级体验",
                "price": "899.00",
                "specs": "尺寸:220x150x150mm;重量:2.5kg;蓝牙5.3;WiFi6;功率:60W",
                "stock": 30,
            },
            {
                "name": "蓝牙耳机 Air",
                "description": "主动降噪,续航30小时,佩戴舒适,适合通勤和运动",
                "price": "299.00",
                "specs": "蓝牙5.3;ANC主动降噪;续航:8h+22h(充电盒);重量:4.5g/只",
                "stock": 100,
            },
            {
                "name": "蓝牙耳机 Pro",
                "description": "混合主动降噪,空间音频,LDAC高清音质,旗舰级无线耳机",
                "price": "699.00",
                "specs": "蓝牙5.3;混合ANC;空间音频;LDAC;续航:9h+27h;重量:5g/只",
                "stock": 60,
            },
            {
                "name": "蓝牙耳机 Sport",
                "description": "耳挂式运动耳机,IPX7防水,防脱落设计,跑步健身专用",
                "price": "249.00",
                "specs": "蓝牙5.2;IPX7防水;续航:10h;重量:16g;耳挂式",
                "stock": 80,
            },
            {
                "name": "便携蓝牙音箱 Mini",
                "description": "小巧便携,IPX7防水,12小时续航,户外露营首选",
                "price": "199.00",
                "specs": "尺寸:80x80x40mm;重量:280g;蓝牙5.0;IPX7防水;续航:12h",
                "stock": 200,
            },
            {
                "name": "便携蓝牙音箱 Clip",
                "description": "挂钩设计,可挂背包,IP67防尘防水,骑行徒步好伴侣",
                "price": "259.00",
                "specs": "尺寸:90x90x45mm;重量:320g;蓝牙5.3;IP67;续航:15h",
                "stock": 90,
            },
        ],
    },
    {
        "name": "家居生活馆",
        "description": "精选家居好物,让生活更有品质",
        "products": [
            {
                "name": "香薰加湿器",
                "description": "超声波雾化,七彩夜灯,静音运行,卧室办公室必备",
                "price": "159.00",
                "specs": "容量:500ml;雾量:30ml/h;噪音:<30dB;功率:12W",
                "stock": 80,
            },
            {
                "name": "香薰加湿器 Pro",
                "description": "上加水设计,UV杀菌,恒湿模式,大容量适合客厅",
                "price": "299.00",
                "specs": "容量:4L;雾量:300ml/h;UV杀菌;恒湿;噪音:<35dB",
                "stock": 45,
            },
            {
                "name": "智能台灯",
                "description": "护眼LED,无极调光调色,支持APP控制,学习办公好伴侣",
                "price": "259.00",
                "specs": "色温:2700-6500K;亮度:无极调光;功率:12W;支持米家APP",
                "stock": 60,
            },
            {
                "name": "智能台灯 Pro",
                "description": "国AA级照度,自动调光,坐姿提醒,儿童学习专用护眼灯",
                "price": "459.00",
                "specs": "照度:国AA级;自动调光;坐姿提醒;色温:3000-5000K;功率:14W",
                "stock": 40,
            },
            {
                "name": "桌面收纳盒",
                "description": "多格分区,透明抽屉,桌面文具化妆品整理神器",
                "price": "59.00",
                "specs": "尺寸:28x18x15cm;材质:PP塑料;4抽屉+4格",
                "stock": 200,
            },
            {
                "name": "北欧风收纳筐",
                "description": "棉麻材质,折叠设计,衣物杂物收纳,简约美观",
                "price": "79.00",
                "specs": "尺寸:40x30x25cm;材质:棉麻;可折叠;承重:5kg",
                "stock": 150,
            },
        ],
    },
    {
        "name": "运动户外专营店",
        "description": "专业运动装备,激发你的运动潜能",
        "products": [
            {
                "name": "无线运动耳机",
                "description": "耳挂式设计,狂甩不掉,IPX5防水,运动听歌首选",
                "price": "179.00",
                "specs": "蓝牙5.2;IPX5防水;续航:8h;重量:18g",
                "stock": 150,
            },
            {
                "name": "骨传导运动耳机",
                "description": "骨传导技术,开放双耳,安全运动,适合跑步骑行",
                "price": "399.00",
                "specs": "蓝牙5.3;骨传导;IP67防水;续航:8h;重量:28g",
                "stock": 70,
            },
            {
                "name": "智能手环",
                "description": "心率血氧监测,50米防水,14天超长续航",
                "price": "199.00",
                "specs": "屏幕:1.1英寸AMOLED;防水:5ATM;续航:14天;传感器:心率/血氧",
                "stock": 120,
            },
            {
                "name": "智能手表 GPS",
                "description": "独立GPS,100+运动模式,血氧心率监测,7天续航",
                "price": "799.00",
                "specs": "屏幕:1.43英寸AMOLED;GPS独立;防水:5ATM;续航:7天",
                "stock": 50,
            },
            {
                "name": "瑜伽垫",
                "description": "TPE环保材质,双面防滑,加厚8mm,初学者友好",
                "price": "89.00",
                "specs": "材质:TPE;尺寸:183x68cm;厚度:8mm;重量:1.2kg",
                "stock": 300,
            },
            {
                "name": "瑜伽垫 Pro",
                "description": "天然橡胶材质,6mm加厚,超强防滑,专业瑜伽爱好者首选",
                "price": "199.00",
                "specs": "材质:天然橡胶;尺寸:183x68cm;厚度:6mm;重量:2.5kg",
                "stock": 80,
            },
            {
                "name": "跑步腰包",
                "description": "贴身不晃动,防水面料,多口袋设计,夜跑反光条",
                "price": "69.00",
                "specs": "材质:防水尼龙;口袋:3个;容量:1.5L;可放6.5寸手机",
                "stock": 200,
            },
        ],
    },
    {
        "name": "厨房好物店",
        "description": "精选厨房小家电和厨具,让烹饪更简单",
        "products": [
            {
                "name": "智能电饭煲",
                "description": "IH电磁加热,4L大容量,24小时预约,多功能菜单",
                "price": "399.00",
                "specs": "容量:4L;IH加热;内胆:不粘涂层;功率:1200W;预约:24h",
                "stock": 60,
            },
            {
                "name": "空气炸锅",
                "description": "5L大容量,无油烹饪,可视化窗口,一键操作",
                "price": "299.00",
                "specs": "容量:5L;功率:1500W;可视窗口;温控:80-200°C",
                "stock": 100,
            },
            {
                "name": "便携式榨汁杯",
                "description": "USB充电,随身携带,鲜榨果汁,6叶刀片",
                "price": "129.00",
                "specs": "容量:400ml;电池:1500mAh;刀片:6叶;充电:USB-C",
                "stock": 180,
            },
            {
                "name": "保温杯",
                "description": "316不锈钢内胆,24小时保温,500ml大容量",
                "price": "99.00",
                "specs": "容量:500ml;材质:316不锈钢;保温:24h;重量:320g",
                "stock": 250,
            },
            {
                "name": "不粘锅炒锅",
                "description": "麦饭石不粘涂层,轻量设计,电磁炉明火通用",
                "price": "169.00",
                "specs": "直径:32cm;涂层:麦饭石;适用:电磁炉/明火;重量:1.1kg",
                "stock": 90,
            },
        ],
    },
    {
        "name": "办公学习专营店",
        "description": "办公学习用品,提升效率的好帮手",
        "products": [
            {
                "name": "机械键盘",
                "description": "红轴机械键盘,87键紧凑布局,RGB背光,办公游戏两用",
                "price": "329.00",
                "specs": "轴体:红轴;键数:87;背光:RGB;连接:USB-C",
                "stock": 70,
            },
            {
                "name": "无线鼠标",
                "description": "静音按键,2.4G无线,人体工学设计,续航12个月",
                "price": "99.00",
                "specs": "连接:2.4G;DPI:1600;按键:静音;续航:12个月",
                "stock": 150,
            },
            {
                "name": "显示器支架",
                "description": "气压升降,360°旋转,承重9kg,桌面免打孔",
                "price": "199.00",
                "specs": "承重:9kg;适配:17-32寸;升降:40cm;旋转:360°",
                "stock": 60,
            },
            {
                "name": "A4打印纸",
                "description": "70g高白度,500张/包,不卡纸,双面打印清晰",
                "price": "29.00",
                "specs": "规格:A4;克重:70g;数量:500张/包;白度:96%",
                "stock": 500,
            },
            {
                "name": "中性笔套装",
                "description": "0.5mm黑色,12支装,顺滑书写,办公学生通用",
                "price": "19.00",
                "specs": "笔尖:0.5mm;颜色:黑色;数量:12支;类型:拔帽式",
                "stock": 400,
            },
        ],
    },
]


SAMPLE_CHATS = [
    {
        "title": "音箱咨询",
        "messages": [
            {"role": "user", "content": "想买个卧室听音乐的音箱,有什么推荐吗?"},
            {
                "role": "assistant",
                "content": "为您推荐以下适合卧室使用的音箱:\n\n1. **智能云音箱 Pro**(¥499):4英寸全频单元,30W大功率,支持语音助手,非常适合卧室听音乐。\n2. **便携蓝牙音箱 Mini**(¥199):小巧便携,IPX7防水,12小时续航。\n\n请问您的预算大概是多少?对音质有什么特别要求吗?",
            },
            {"role": "user", "content": "预算500以内,音质好一点的"},
            {
                "role": "assistant",
                "content": "那我推荐您选择 **智能云音箱 Pro**(¥499),它的4英寸全频单元和30W功率在同价位中音质表现出色,支持语音助手也很方便。\n\n您可以直接点击下方商品卡片下单购买~",
            },
        ],
    },
    {
        "title": "运动耳机推荐",
        "messages": [
            {"role": "user", "content": "跑步用的耳机有什么推荐?"},
            {
                "role": "assistant",
                "content": "为您推荐适合跑步的运动耳机:\n\n1. **无线运动耳机**(¥179):耳挂式设计,狂甩不掉,IPX5防水,非常适合跑步时佩戴。\n2. **蓝牙耳机 Air**(¥299):主动降噪,续航30小时,音质更佳。\n\n请问您更看重防水性能还是降噪效果呢?",
            },
        ],
    },
]


def clear_all(db):
    """Delete all data from all tables (in dependency order) and reset the vector store."""
    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.query(Message).delete()
    db.query(Session).delete()
    db.query(Product).delete()
    db.query(Merchant).delete()
    db.commit()
    # Clear stale vectors from previous seeds so re-seeding doesn't create duplicates
    reset_collection()


def seed(keep_existing: bool = False):
    init_db()
    db = SessionLocal()
    try:
        if not keep_existing:
            print("[1/4] 清空现有数据...")
            clear_all(db)

        # ---- Merchants + Products ----
        print("[2/4] 创建商户和商品(含向量索引)...")
        created_products = []
        for m_data in MERCHANTS:
            merchant = Merchant(name=m_data["name"], description=m_data["description"])
            db.add(merchant)
            db.commit()
            db.refresh(merchant)
            for p_data in m_data["products"]:
                product = Product(merchant_id=merchant.id, **p_data)
                db.add(product)
                db.commit()
                db.refresh(product)
                # Index into vector store
                try:
                    index_product(product, merchant_name=merchant.name)
                    product.status = "indexed"
                except Exception as e:
                    print(f"  ⚠ 商品 [{product.name}] 索引失败: {e}")
                    product.status = "failed"
                db.commit()
                created_products.append(product)
                print(f"  + 商品: {product.name} (¥{product.price})")

        # ---- Sessions + Messages ----
        print("[3/4] 创建示例会话和消息...")
        sessions = []
        for chat in SAMPLE_CHATS:
            session = Session(title=chat["title"])
            db.add(session)
            db.commit()
            db.refresh(session)
            sessions.append(session)
            for msg in chat["messages"]:
                m = Message(
                    session_id=session.id,
                    role=msg["role"],
                    content=msg["content"],
                    sources_json=[],
                    product_cards_json=[],
                )
                db.add(m)
            db.commit()
            print(f"  + 会话: {session.title} ({len(chat['messages'])}条消息)")

        # ---- Orders ----
        print("[4/4] 创建示例订单...")
        if created_products and sessions:
            # Order 1: paid
            p1 = created_products[0]
            s1 = sessions[0]
            o1 = Order(
                session_id=s1.id,
                merchant_id=p1.merchant_id,
                status="paid",
                total_amount=p1.price,
                remark="尽快发货",
            )
            db.add(o1)
            db.commit()
            db.refresh(o1)
            db.add(OrderItem(
                order_id=o1.id,
                product_id=p1.id,
                product_name=p1.name,
                price=p1.price,
                quantity=1,
                image_url=p1.image_url,
            ))
            print(f"  + 订单(已支付): {p1.name} x1 = ¥{p1.price}")

            # Order 2: pending
            p2 = created_products[1]
            o2 = Order(
                session_id=s1.id,
                merchant_id=p2.merchant_id,
                status="pending",
                total_amount=p2.price,
                remark="",
            )
            db.add(o2)
            db.commit()
            db.refresh(o2)
            db.add(OrderItem(
                order_id=o2.id,
                product_id=p2.id,
                product_name=p2.name,
                price=p2.price,
                quantity=1,
                image_url=p2.image_url,
            ))
            print(f"  + 订单(待支付): {p2.name} x1 = ¥{p2.price}")

            # Order 3: cancelled
            p3 = created_products[3] if len(created_products) > 3 else created_products[2]
            o3 = Order(
                session_id=sessions[1].id,
                merchant_id=p3.merchant_id,
                status="cancelled",
                total_amount=p3.price,
                remark="不想要了",
            )
            db.add(o3)
            db.commit()
            db.refresh(o3)
            db.add(OrderItem(
                order_id=o3.id,
                product_id=p3.id,
                product_name=p3.name,
                price=p3.price,
                quantity=1,
                image_url=p3.image_url,
            ))
            print(f"  + 订单(已取消): {p3.name} x1 = ¥{p3.price}")
            db.commit()

        # ---- Summary ----
        n_merchants = db.query(Merchant).count()
        n_products = db.query(Product).count()
        n_sessions = db.query(Session).count()
        n_messages = db.query(Message).count()
        n_orders = db.query(Order).count()
        print(f"\n✅ 完成! 商户:{n_merchants} 商品:{n_products} 会话:{n_sessions} 消息:{n_messages} 订单:{n_orders}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed mock data into the database")
    parser.add_argument("--keep", action="store_true", help="keep existing data, only append")
    args = parser.parse_args()
    seed(keep_existing=args.keep)
