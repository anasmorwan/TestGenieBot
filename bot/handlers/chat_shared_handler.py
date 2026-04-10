from telebot import types
from services.usage import is_paid_user_active
from storage.quiz_repository import get_user_current_quiz
from storage.messages import get_message
from storage.session_store import user_states, get_state_safe, temp_texts
from services.poll_service import generate_poll
from bot.keyboards.actions_keyboard import send_poll_keyboard
from services.user_trap import update_last_active


def publish_interactive_link(bot, target_chat_id, quiz_code, shared_by_name, watermark=True):
    announcement_text = (
        f"🧠 هل تستطيع حل هذا التحدي؟\n\n"  
        f"🚀 ابدأ الآن خلال 30 ثانية\n"
        f"🏆 هل تتفوق على أصدقائك؟\n"
    )
    
    if watermark:
        announcement_text += f"\n\n✨ مدعوم بالذكاء الاصطناعي"

    bot_username = bot.get_me().username
    start_url = f"https://t.me/{bot_username}?start=shared_{quiz_code}"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🎯 ابدأ الاختبار الآن", url=start_url))

    try:
        bot.send_message(
            chat_id=target_chat_id,
            text=announcement_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return True # نجح النشر
    except Exception as e:
        print(f"❌ خطأ أثناء النشر في القناة {target_chat_id}: {e}")
        return False # فشل النشر



def register(bot):


    # عند استقبال القناة المختارة
    @bot.message_handler(content_types=['chat_shared'])
    def handle_chat_shared(message):
        if message.chat.type != "private":
        
            return
        user_id = message.from_user.id
        shared_by = message.from_user.first_name
        chat_id_to_publish = message.chat_shared.chat_id if message.chat_shared and message.chat_shared.chat_id else -1003806238292
        request_id = message.chat_shared.request_id  # 🔥 هذا المهم
        update_last_active(user_id)
        
        

        # تحديد النوع بناءً على الزر
        if request_id == 1:
            chat_type = "القناة"
        elif request_id == 2:
            chat_type = "المجموعة"
        else:
            chat_type = "الشات"



        try:
            
            chat_details = bot.get_chat(chat_id_to_publish)
            try:
                chat_title = chat_details.title
            except Exception as e:
                chat_title = "قناة غير معروفة"
                bot.send_message(user_id, f"حدث خطا أثناء جلب إسم القناة\n\n{str(e)}")
                

            
            state = get_state_safe(user_id)


            if state == "poll":
                waiting_text = f"تم تحديد القناة: {chat_title}\n\nيتم إنشاء استطلاع الان..."
                receive_text = get_message("POLL_TEXT")
                share_msg = get_message("SEND_POLL")
                text = temp_texts.get(user_id)


                
                waiting_msg = bot.send_message(user_id, waiting_text)
                
                try:
                    print(f"DEBUG: [User: {user_id}] Calling AI for Poll...", flush=True)
                    poll_code, poll = generate_poll(user_id, text, channel_name=chat_title)
                    print(f"DEBUG: poll type is {type(poll)}", flush=True)

                    bot.delete_message(user_id, waiting_msg.message_id)

                    
                
                    # 1. نظام استخراج البيانات المرن (Flexible Extraction)
                    q_text = "Poll"
                    q_options = []

                    if isinstance(poll, dict):
                         # إذا كان قاموساً (JSON parsed)
                         q_text = poll.get('poll') or poll.get('question') or "Poll"
                         q_options = poll.get('answers') or poll.get('options') or []
    
                    elif isinstance(poll, list) and len(poll) > 0:
                        # إذا عاد كقائمة (بعض المكتبات تعيد الاستطلاع كأول عنصر في قائمة)
                        first_item = poll[0]
                        if isinstance(first_item, dict):
                            q_text = first_item.get('poll') or first_item.get('question')
                            q_options = first_item.get('answers') or first_item.get('options')
    
                    else:
                        # إذا كان كائناً (Object/Class instance)
                        # نستخدم getattr لتجنب AttributeError
                        q_text = getattr(poll, 'poll', getattr(poll, 'question', "Poll"))
                        q_options = getattr(poll, 'answers', getattr(poll, 'options', []))

                    # 2. التحقق النهائي قبل الإرسال
                    if not q_options:
                        raise ValueError("لم يتم العثور على خيارات في الاستطلاع المولد")

                    print(f"DEBUG: Question extracted: {q_text[:20]}...", flush=True)

                    # 3. إرسال الاستطلاع
                    bot.send_poll(
                        chat_id=user_id, # تأكد من أن chat_id هو المعرف الصحيح للمستقبل
                        question=str(q_text)[:300],
                        options=[str(opt) for opt in q_options if opt][:10], # التليجرام يقبل 10 خيارات كحد أقصى
                        type="regular",
                        is_anonymous=False
                    )
                
                    action_keyboard = send_poll_keyboard(user_id, poll_code) 
                
                    
                
                    bot.send_message(user_id, share_msg, reply_markup=action_keyboard, parse_mode="HTML")
                    user_states[user_id] = None 
                    print(f"DEBUG: [User: {user_id}] generate_poll COMPLETED", flush=True)
                    return
                    
                except Exception as e:
                    bot.send_message(user_id, f"فشل إنشاء إستطلاع.\n\n {str(e)}")
                    user_states.pop(user_id, None)
                finally:
                    user_states.pop(user_id, None)
                    

                return
            elif state.get("post_poll"):
                
                

            else:
                # 1. استرجاع الكويز الذي كان المستخدم يعمل عليه
                quiz_code = get_user_current_quiz(user_id) 
    
                if not quiz_code:
                    bot.send_message(message.chat.id, "❌ حدث خطأ، لم نجد الاختبار المطلوب. حاول مرة أخرى.")
                    return

                # 2. التحقق: هل المستخدم مشترك (Paid) أم مجاني؟
                if is_paid_user_active(user_id):
                    # المستخدم برو: نعطيه خيار "كيف تريد النشر؟" لأننا نحترم وقته
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton("📊 استطلاعات مباشرة (Native)", callback_data=f"pub:native:{quiz_code}:{chat_id_to_publish}:{chat_type}"))
                    keyboard.add(types.InlineKeyboardButton("🔗 رابط تفاعلي (Interactive)", callback_data=f"pub:link:{quiz_code}:{chat_id_to_publish}:{chat_type}"))
        
                    bot.send_message(message.chat.id, "✨ أنت مستخدم Pro! كيف تريد ظهور الاختبار في قناتك؟", reply_markup=keyboard)
                else:
                    # المستخدم مجاني: ننشر فوراً بـ "الطريقة التفاعلية" (التي تفيدك أنت)
                    publish_interactive_link(bot, chat_id_to_publish, quiz_code, shared_by, watermark=True)
        
                    # رسالة نجاح في شات البوت الخاص
                    bot.send_message(message.chat.id, "✅ تم نشر الاختبار في قناتك بنجاح باستخدام الرابط التفاعلي!")
        
                    # تلميح للترقية (Soft Sell)
                     #bot.send_message(message.chat.id, text=get_message("SHARED_QUIZ_REACTIONS"))


                       
        except Exception as e:
            bot.send_message(message.chat.id, f"😴 عذراً، لا يمكنني الوصول لبيانات هذه المجموعة. تأكد أنني عضو فيها.\n\n {str(e)}")
            
        
        
