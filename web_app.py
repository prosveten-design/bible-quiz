import streamlit as st
import json
import random
import os
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# Конфигурация на уеб страницата
st.set_page_config(page_title="Библейска Викторина", page_icon="📖", layout="centered")

# --- ФУНКЦИЯ ЗА РЕГИСТРИРАНЕ НА ШРИФТ (КИРИЛИЦА) ---
def register_fonts():
    # Търсим файла arial.ttf в текущата папка
    font_path = "arial.ttf"
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('ArialCustom', font_path))
            return 'ArialCustom'
        except Exception as e:
            st.error(f"Грешка при регистрация на шрифт: {e}")
            return 'Helvetica'
    else:
        # Ако файлът липсва, показваме предупреждение в Streamlit
        st.warning("Внимание: Файлът 'arial.ttf' не е намерен. Кирилицата в PDF може да не излиза коректно.")
        return 'Helvetica'

# Глобална променлива за името на шрифта
FONT_NAME = register_fonts()

# --- ФУНКЦИИ ЗА ДАННИ ---
def load_questions():
    if os.path.exists('questions.json'):
        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            st.error(f"Грешка при четене на JSON: {e}")
            return None
    return None

def generate_pdf_bytes(name, score, max_score, history):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    
    # Заглавие
    c.setFont(FONT_NAME, 16)
    c.drawString(50, 800, "ОФИЦИАЛЕН ОТЧЕТ ОТ БИБЛЕЙСКИ ТЕСТ")
    
    # Информация
    c.setFont(FONT_NAME, 12)
    c.drawString(50, 770, f"Ученик: {name}")
    c.drawString(50, 750, f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    # Резултат с цвят
    if score / max_score >= 0.5:
        c.setFillColor(colors.darkgreen)
    else:
        c.setFillColor(colors.red)
    c.drawString(50, 730, f"Краен резултат: {score} от {max_score} точки")
    
    c.setFillColor(colors.black)
    c.line(50, 720, 550, 720)

    # Въпроси и отговори
    y = 690
    c.setFont(FONT_NAME, 10)
    
    for i, h in enumerate(history):
        if y < 100:
            c.showPage()
            y = 800
            c.setFont(FONT_NAME, 10)
        
        status = "Верен" if h['is_right'] else "Грешен"
        # Скъсяваме въпроса, ако е твърде дълъг за PDF-а
        clean_q = h['q'][:80] + "..." if len(h['q']) > 80 else h['q']
        
        c.drawString(50, y, f"{i+1}. {clean_q}")
        y -= 15
        c.setFont(FONT_NAME, 9)
        c.drawString(70, y, f"Статус: {status}")
        y -= 25
        c.setFont(FONT_NAME, 10)

    c.save()
    return buffer.getvalue()

# --- ОСНОВЕН ИНТЕРФЕЙС ---
def main():
    questions_db = load_questions()

    if not questions_db:
        st.error("Системата не може да зареди въпросите. Проверете дали 'questions.json' съществува.")
        return

    # Инициализация на сесията
    if 'step' not in st.session_state:
        st.session_state.step = "intro"
        st.session_state.score = 0
        st.session_state.history = []
        st.session_state.current_q_idx = 0
        st.session_state.selected_qs = []
        st.session_state.user_name = ""

    # ЕКРАН 1: ВХОД
    if st.session_state.step == "intro":
        st.header("📖 Библейска Викторина Онлайн")
        st.write("Добре дошли! Моля, попълнете данните си, за да започнете теста.")
        
        name_input = st.text_input("Вашето име и фамилия:")
        level = st.selectbox("Изберете ниво:", sorted(list(questions_db.keys())))
        
        if st.button("Започни изпита"):
            if name_input.strip():
                st.session_state.user_name = name_input
                all_qs = questions_db[level]
                # Избираме 5 случайни въпроса от нивото
                st.session_state.selected_qs = random.sample(all_qs, min(len(all_qs), 5))
                st.session_state.step = "quiz"
                st.rerun()
            else:
                st.warning("Моля, въведете име!")

    # ЕКРАН 2: ТЕСТ
    elif st.session_state.step == "quiz":
        q_idx = st.session_state.current_q_idx
        q_data = st.session_state.selected_qs[q_idx]

        st.write(f"**Ученик:** {st.session_state.user_name}")
        st.write(f"**Въпрос {q_idx + 1} от {len(st.session_state.selected_qs)}**")
        st.progress((q_idx) / len(st.session_state.selected_qs))
        
        st.subheader(q_data[0])
        choice = st.radio("Изберете един отговор:", q_data[1], key=f"choice_{q_idx}")

        if st.button("Следващ въпрос ➡️"):
            is_right = (q_data[1].index(choice) == q_data[2])
            if is_right:
                st.session_state.score += 10
            
            st.session_state.history.append({
                "q": q_data[0],
                "is_right": is_right
            })

            if q_idx + 1 < len(st.session_state.selected_qs):
                st.session_state.current_q_idx += 1
                st.rerun()
            else:
                st.session_state.step = "finish"
                st.rerun()

    # ЕКРАН 3: ФИНАЛ
    elif st.session_state.step == "finish":
        st.balloons()
        st.header("🏁 Резултати")
        
        max_p = len(st.session_state.selected_qs) * 10
        st.success(f"Вие завършихте теста успешно, {st.session_state.user_name}!")
        st.metric("Общ брой точки", f"{st.session_state.score} / {max_p}")

        # Генериране на PDF сертификат
        pdf_data = generate_pdf_bytes(
            st.session_state.user_name, 
            st.session_state.score, 
            max_p, 
            st.session_state.history
        )

        st.download_button(
            label="📥 Изтегли PDF Резултат",
            data=pdf_data,
            file_name=f"Rezultat_{st.session_state.user_name}.pdf",
            mime="application/pdf"
        )

        if st.button("Започни нов тест"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()