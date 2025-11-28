from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random
import time
from deep_translator import GoogleTranslator 
import os # 👈 تم إضافة استيراد مكتبة os

# =============================================================================
# 1. الثوابت والمتغيرات الرئيسية (معلوماتك الخاصة)
# =============================================================================

# يفضل في بيئات الإنتاج (الاستضافة) استخدام متغيرات البيئة لـ TOKEN_BOT و USER_ADMIN_ID
TOKEN_BOT = "8584368140:AAE5yMyAYiefJ4SNqajzC_TzmBvkmE_whp8"
USER_ADMIN_ID = 5730502448 
WALLET_ADDRESS = "0xba844f21fafb51d3a05826756a6305c0ec07f2fa"
APP_PRICE = 5.00 

APK_DOWNLOAD_LINK = "https://play.google.com/store/apps/details?id=com.speed.gc.autoclicker.automatictap"

BINANCE_PLAY_STORE_LINK = "https://play.google.com/store/apps/details?id=com.binance.dev"

BASE_BUTTON_TEXT_AR = "💰 شراء التطبيق"

# اللغات المدعومة
SUPPORTED_LANGUAGES = {
    "العربية 🇪🇬": "ar",
    "English 🇺🇸": "en",
    "Türkçe 🇹🇷": "tr",
    "Deutsch 🇩🇪": "de",
    "Русский 🇺🇸": "ru",
    "Español 🇪🇸": "es",
    "日本語 🇯🇵": "ja",
    "한국어 🇰🇷": "ko" 
}

# قاعدة بيانات وهمية لتخزين الطلبات وحالة المستخدم
orders_db = {} 
user_states = {} 

# تهيئة كائن الترجمة الجديد (نضبط المصدر للعربية)
translator_engine = GoogleTranslator(source='auto', target='ar')

# =============================================================================
# 2. الدوال المساعدة للترجمة
# =============================================================================

def get_user_lang(user_id):
    """الحصول على رمز لغة المستخدم المحفوظ، أو افتراض العربية."""
    return user_states.get(user_id, {}).get('lang', 'ar')

def translate_text(text_ar, lang_code):
    """ترجمة النص من العربية إلى لغة الهدف باستخدام Deep-Translator."""
    try:
        if lang_code == 'ar':
            return text_ar
        
        # نضبط لغة الهدف في كل مرة
        translator_engine.target = lang_code
        translated = translator_engine.translate(text_ar)
        return translated
    except Exception as e:
        print(f"خطأ في الترجمة: {e}")
        return text_ar

# =============================================================================
# 3. الدوال الرئيسية للبوت
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يبدأ العملية: يسأل عن اللغة أو يرحب باللغة المحفوظة."""
    user_id = update.effective_user.id
    
    if user_id in user_states and user_states[user_id].get('lang'):
        # إذا كانت اللغة موجودة، ابدأ المحادثة مباشرة
        user_lang_code = user_states[user_id]['lang']
        
        welcome_text_ar = "مرحباً بك مجدداً! يمكنك الآن الضغط على زر الشراء أو استخدام الأمر /buy."
        welcome_text = translate_text(welcome_text_ar, user_lang_code)
        
        button_text_ar = BASE_BUTTON_TEXT_AR 
        button_text = translate_text(button_text_ar, user_lang_code)
        
        reply_keyboard = ReplyKeyboardMarkup([[KeyboardButton(button_text)]], resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_keyboard)
        return
    
    # إذا لم يتم تحديد اللغة، اطرح السؤال
    lang_buttons_list = [KeyboardButton(lang) for lang in SUPPORTED_LANGUAGES.keys()]
    
    # تقسيم الأزرار إلى صفوف 
    lang_keyboard = ReplyKeyboardMarkup([lang_buttons_list[0:3], lang_buttons_list[3:6], lang_buttons_list[6:]], resize_keyboard=True, one_time_keyboard=True)
    
    question = "👋 Welcome! يرجى اختيار اللغة المفضلة لديك للمتابعة:"
    await update.message.reply_text(question, reply_markup=lang_keyboard)
    
    user_states[user_id] = {'status': 'awaiting_lang', 'lang': None}

async def handle_lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج اختيار اللغة ويحفظها."""
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # 1. التحقق من حالة انتظار اللغة
    if user_id in user_states and user_states[user_id]['status'] == 'awaiting_lang':
        
        if user_text in SUPPORTED_LANGUAGES:
            lang_code = SUPPORTED_LANGUAGES[user_text]
            
            user_states[user_id]['lang'] = lang_code
            user_states[user_id]['status'] = 'ready'
            
            confirmation_ar = f"تم اختيار {user_text}! لنبدأ الآن."
            confirmation_text = translate_text(confirmation_ar, lang_code)
            
            await update.message.reply_text(confirmation_text)
            
            # استدعاء دالة /start مرة أخرى الآن وقد تم تحديد اللغة
            await start(update, context) 
            
        else:
            error_ar = "عذراً، يرجى اختيار واحدة من اللغات المتاحة من لوحة المفاتيح."
            error_text = translate_text(error_ar, get_user_lang(user_id))
            await update.message.reply_text(error_text)
    
    # إذا لم تكن الرسالة اختيار لغة، فسيتم تجاهلها أو معالجتها بواسطة معالج آخر
    else:
        # إذا كانت الرسالة ليست أمراً ولا اختيار لغة، يمكن هنا توجيه المستخدم لـ /start
        user_lang_code = get_user_lang(user_id)
        if user_text not in SUPPORTED_LANGUAGES.keys():
             help_msg_ar = "عذراً، لا أفهم هذا الأمر. يرجى الضغط على زر الشراء أو استخدام الأمر /start."
             help_msg = translate_text(help_msg_ar, user_lang_code)
             await update.message.reply_text(help_msg)


async def buy_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ينشئ فاتورة الدفع ويرسل تنبيهاً للمشرف بلغة المستخدم."""
    
    user_id = update.effective_user.id
    user_lang_code = get_user_lang(user_id)
    
    # 1. إنشاء رقم مرجعي فريد
    order_id = f"ORD-{random.randint(10000, 99999)}"
    orders_db[order_id] = {'user_id': user_id, 'status': 'PENDING', 'username': update.effective_user.username}
    
    # 2. إنشاء زر مضمن (Inline Button) وترجمة نصه
    inline_button_text_ar = "🔗 افتح رابط المحفظة (للتسهيل)"
    inline_button_text = translate_text(inline_button_text_ar, user_lang_code)
    
    inline_button = InlineKeyboardButton(
        text=inline_button_text, 
        url=BINANCE_PLAY_STORE_LINK 
    )
    inline_keyboard = InlineKeyboardMarkup([[inline_button]])
    
    # 3. صياغة وترجمة تعليمات الدفع
    payment_message_ar = (
        f"💰 **فاتورة شراء التطبيق**\n\n"
        f"المبلغ المطلوب: **{APP_PRICE} USDT**\n"
        f"العنوان للدفع (USDT-TRC20): `{WALLET_ADDRESS}`\n"
        f"الرقم المرجعي لطلبك: **{order_id}**\n\n"
        f"❗️ **بعد إرسال المبلغ، نرجو الانتظار قليلاً ريثما يتم التحقق من عملية الدفع و تسليم التطبيق.**"
    )
    translated_payment_message = translate_text(payment_message_ar, user_lang_code)
    
    await (update.callback_query or update.message).reply_text(
        translated_payment_message,
        parse_mode='Markdown',
        reply_markup=inline_keyboard
    )
    
    # 4. إرسال تنبيه للمشرف (بلغة المشرف - العربية)
    admin_alert = (
        f"🚨 **تنبيه: طلب شراء جديد**\n"
        f"اللغة: {user_lang_code}\n"
        f"الرقم المرجعي: **{order_id}**\n"
        f"من المستخدم: @{update.effective_user.username or 'غير معروف'}\n"
        f"المطلوب: {APP_PRICE} USDT.\n"
        f"للتسليم، أرسل الأمر التالي: `/deliver {order_id}`"
    )
    await context.bot.send_message(chat_id=USER_ADMIN_ID, text=admin_alert)


async def deliver_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يستخدمه المشرف يدوياً لتأكيد التسليم للمستخدم وإرسال رابط التنزيل المحدث."""
    
    if update.effective_user.id != USER_ADMIN_ID:
        return await update.message.reply_text("هذا الأمر خاص بالمشرفين فقط.")

    try:
        order_id = context.args[0]
    except (IndexError, TypeError):
        return await update.message.reply_text("يرجى إدخال الرقم المرجعي بعد الأمر. مثال: /deliver ORD-12345")

    if order_id not in orders_db:
        return await update.message.reply_text(f"الرقم المرجعي {order_id} غير موجود.")
    
    if orders_db[order_id]['status'] == 'DELIVERED':
        return await update.message.reply_text(f"تم تسليم الطلب {order_id} مسبقاً.")

    # تنفيذ التسليم
    target_user_id = orders_db[order_id]['user_id']
    user_lang_code = get_user_lang(target_user_id) 
    orders_db[order_id]['status'] = 'DELIVERED'
    
    # صياغة وترجمة رسالة التسليم
    delivery_confirmation_ar = (
        f"✅ **تم تأكيد الدفع!** شكراً لك.\n\n"
        f"إليك رابط تنزيل التطبيق:\n"
        f"[رابط تنزيل التطبيق الخاص بك]({APK_DOWNLOAD_LINK})"
    )
    delivery_confirmation = translate_text(delivery_confirmation_ar, user_lang_code)
    
    # إرسال التسليم إلى المشتري
    await context.bot.send_message(chat_id=target_user_id, text=delivery_confirmation, parse_mode='Markdown')
    
    # تأكيد التسليم للمشرف
    await update.message.reply_text(f"تم بنجاح تسليم التطبيق للطلب {order_id}.")

# =============================================================================
# 4. نقطة الدخول وبدء التشغيل (باستخدام Webhook)
# =============================================================================

# 👈 تحديد المتغيرات المطلوبة للويب هوك (سيتم سحبها من بيئة الاستضافة)
PORT = int(os.environ.get('PORT', 8080)) # المنفذ الذي ستستمع عليه الخدمة (عادة 80 أو 8080)
# رابط الويب هوك الذي ستزودك به منصة الاستضافة (يجب عليك تغييره إلى رابط تطبيقك)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://your-app-name.onrender.com/') 

if __name__ == '__main__':
    # بناء التطبيق
    application = Application.builder().token(TOKEN_BOT).build()
    
    # حساب جميع نصوص زر الشراء المترجمة
    ALL_BUY_BUTTON_TEXTS = set()
    for lang_code in SUPPORTED_LANGUAGES.values():
        translated_text = translate_text(BASE_BUTTON_TEXT_AR, lang_code)
        if translated_text:
            ALL_BUY_BUTTON_TEXTS.add(translated_text)
    
    # ربط المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy_app))
    application.add_handler(CommandHandler("deliver", deliver_app)) 
    application.add_handler(MessageHandler(filters.Text(list(ALL_BUY_BUTTON_TEXTS)), buy_app)) 
    application.add_handler(MessageHandler(filters.Text(), handle_lang_choice))
    
    # 🚨 بدء تشغيل البوت باستخدام Webhooks 🚨
    print(f"البوت يعمل بنظام Webhook على المنفذ {PORT}...")
    
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        # المسار السري الذي سيستمع إليه البوت (يمكن تركه فارغاً أو تعيينه)
        url_path="", 
        webhook_url=WEBHOOK_URL # الرابط العام الكامل لتطبيقك
    )
