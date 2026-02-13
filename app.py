import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import io
import json
import hashlib
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Smart Завуч: Фокус-группа", layout="wide")

# --- 2. БЕЗОПАСНОСТЬ И БАЗА ДАННЫХ ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text: return hashed_text
    return False

def init_db():
    conn = sqlite3.connect('school_focus_final_v14.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    try:
        c.execute('ALTER TABLE reports ADD COLUMN user_id INTEGER')
    except:
        pass # Если колонка уже есть
    
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT, quarter INTEGER, teacher TEXT, student TEXT, subject TEXT, grade TEXT, topic TEXT, goal TEXT,
        purpose TEXT, start_t TEXT, start_s TEXT, middle_t TEXT, middle_s TEXT, end_t TEXT, end_s TEXT,
        ict_usage TEXT, methods TEXT, reflection TEXT,
        reserve_json TEXT, scores_json TEXT, comments_json TEXT,
        s1 TEXT, s2 TEXT, s3 TEXT, g1 TEXT, g2 TEXT, g3 TEXT, advice TEXT, percent REAL, lang TEXT
    )''')
    conn.commit()
    conn.close()

# --- 3. СЛОВАРЬ ИНТЕРФЕЙСА ---
LANGS = {
    'RU': {
        'title': "Smart Завуч 🇰🇿", 'header': "ЛИСТ НАБЛЮДЕНИЯ УРОКА (ФОКУС-ГРУППА)",
        'nav_new': "📊 Ввод данных (Шаблон)", 'nav_rating': "🏆 Сводный рейтинг", 'nav_map': "📈 Динамика прогресса",
        'teacher': "ФИО Учителя", 'student': "ФИО Ученика (Резерв)", 'subject': "Предмет", 'grade': "Класс",
        'date': "Дата", 'quarter': "Четверть", 'topic': "Тема урока", 'goal': "Цели урока (со слов учителя)",
        'purpose': "Цель посещения", 'res_header': "2. Назардағы оқушылар / Фокус на учащихся 'резерва'",
        'res_fio': "ФИО ученика", 'res_inter': "Взаимодействие учителя (приемы, вопросы)",
        'res_react': "Реакция и активность (ответы, действия)", 'res_idx': "Индекс (УД/ТБ)",
        'crit_header': "3. Общий анализ урока (2+, 1+, -)", 'prof_header': "🎯 Профессионализм и Методы",
        'ict_label': "Использование ИКТ (инструменты, платформы)", 'methods_label': "Методы и приемы обучения",
        'reflection': "Рефлексия (обратная связь)", 'stages_header': "⏳ Ход урока по этапам (Учитель / Ученик)",
        'conclusion_header': "4. Выводы и рекомендации", 'strengths_label': "Сильные стороны урока:",
        'growth_label': "Зоны роста:", 'final_advice': "5. Конкретные рекомендации учителю",
        'save_btn': "💾 Сохранить отчет в базу", 'excel_btn': "📥 Скачать мониторинг (Excel)",
        'word_btn': "📄 Скачать протокол (Word)", 'fact_label': "Комментарии (факты, примеры)",
        'score_label': "Балл", 'action_t': "Действие учителя", 'action_s': "Действие ученика",
        'copy_msg': "Текст справки готов:",
        'criteria_list': [
            "Четкость и достижимость целей урока", "Содержание материала (научность, доступность, ценность)",
            "Разнообразие методов и приемов (АКТ, ИКТ, группы)", "Дифференциация заданий для учащихся 'резерва'",
            "Логика и взаимосвязь этапов урока", "Критериальное оценивание (кері байланыс)",
            "Коммуникация и психологическая атмосфера", "Эффективность использования времени"
        ]
    },
    'KZ': {
        'title': "Smart Завуч 🇰🇿", 'header': "САБАҚТЫ БАҚЫЛАУ ПАРАҒЫ (РЕЗЕРВ)",
        'nav_new': "📊 Деректерді енгізу", 'nav_rating': "🏆 Жиынтық рейтинг", 'nav_map': "📈 Прогресс картасы",
        'teacher': "Мұғалімнің АЖТ", 'student': "Оқушының АЖТ (Резерв)", 'subject': "Пән", 'grade': "Сынып",
        'date': "Күні", 'quarter': "Тоқсан", 'topic': "Сабақтың тақырыбы", 'goal': "Сабақ мақсаты (мұғалім қойған)",
        'purpose': "Бақылау мақсаты", 'res_header': "2. Назардағы оқушылар ('резерв')",
        'res_fio': "Оқушының АЖТ", 'res_inter': "Мұғалімнің әрекеті (сұрақтар, әдістер)",
        'res_react': "Оқушының реакциясы мен белсенділігі", 'res_idx': "Завучтың индекстері (ОІӘ/ТБ)",
        'crit_header': "3. Сабақтың жалпы талдауы (2+, 1+, -)", 'prof_header': "🎯 Кәсіби шеберлік пен әдістер",
        'ict_label': "АКТ қолданылуы (құралдар, платформалар)", 'methods_label': "Оқыту әдіс-тәсілдері",
        'reflection': "Рефлексия (кері байланыс)", 'stages_header': "⏳ Сабақ кезеңдері (Мұғалім / Оқушы)",
        'conclusion_header': "4. Қорытынды және ұсыныстар", 'strengths_label': "Сабақтың күшті жақтары:",
        'growth_label': "Даму аймақтары:", 'final_advice': "5. Мұғалімге арналған нақты ұсыныстар",
        'save_btn': "💾 Мәліметтерді сақтау", 'excel_btn': "📥 Есепті жүктеу (Excel)",
        'word_btn': "📄 Хаттаманы жүктеу (Word)", 'fact_label': "Түсініктеме (фактілер, мысалдар)",
        'score_label': "Баға", 'action_t': "Мұғалім әрекеті", 'action_s': "Оқушы реакциясы",
        'copy_msg': "Анықтама мәтіні дайын:",
        'criteria_list': [
            "Сабақ мақсаттарының айқындылығы мен қолжетімділігі", "Материалдың мазмұны (ғылымилығы, қолжетімділігі)",
            "Әдіс-тәсілдердің әртүрлілігі (АКТ, ИКТ, топтық)", "«Резерв» оқушыларына арналған тапсырмаларды саралау",
            "Сабақ кезеңдерінің қисындылығы мен байланысы", "Критериалды бағалау (кері байланыс)",
            "Коммуникация және психологиялық ахуал", "Уақытты пайдаланудың тиімділігі"
        ]
    }
}

# --- 4. ФУНКЦИЯ WORD ---
def create_official_docx(data, lang):
    L = LANGS[lang]
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)

    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = h.add_run(L['header'])
    run.bold = True
    run.font.size = Pt(14)

    doc.add_heading('1. Общая информация', level=1)
    t1 = doc.add_table(rows=6, cols=2)
    t1.style = 'Table Grid'
    info = [(L['date'], data['date']), (L['grade'], data['grade']), (L['subject'], data['subject']), (L['teacher'], data['teacher']), (L['topic'], data['topic']), (L['goal'], data['goal'])]
    for i, (k, v) in enumerate(info):
        t1.cell(i, 0).text = k
        t1.cell(i, 1).text = str(v)

    doc.add_heading(L['res_header'], level=1)
    t2 = doc.add_table(rows=1, cols=4)
    t2.style = 'Table Grid'
    hdr = t2.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = "ФИО", L['action_t'], L['action_s'], "УД/ТБ"
    res_list = json.loads(data['reserve_json'])
    for r in res_list:
        row = t2.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text = r['fio'], r['act'], r['re'], r['idx']

    doc.add_heading(L['stages_header'], level=1)
    t3 = doc.add_table(rows=4, cols=3)
    t3.style = 'Table Grid'
    th = t3.rows[0].cells
    th[0].text, th[1].text, th[2].text = "Этап", L['action_t'], L['action_s']
    t3.cell(1,0).text = "Начало"; t3.cell(1,1).text = data['start_t']; t3.cell(1,2).text = data['start_s']
    t3.cell(2,0).text = "Середина"; t3.cell(2,1).text = data['middle_t']; t3.cell(2,2).text = data['middle_s']
    t3.cell(3,0).text = "Конец"; t3.cell(3,1).text = data['end_t']; t3.cell(3,2).text = data['end_s']

    doc.add_heading(L['conclusion_header'], level=1)
    doc.add_paragraph(f"{L['strengths_label']}\n1. {data['s1']}\n2. {data['s2']}\n3. {data['s3']}")
    doc.add_paragraph(f"{L['growth_label']}\n1. {data['g1']}\n2. {data['g2']}\n3. {data['g3']}")
    doc.add_paragraph(f"РЕКОМЕНДАЦИЯ: {data['advice']}")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 5. ЛОГИКА ПРИЛОЖЕНИЯ ---
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# ОКНО ВХОДА
if not st.session_state['logged_in']:
    st.sidebar.title("Вход в Smart Завуч")
    auth_mode = st.sidebar.selectbox("Выберите действие:", ["Вход", "Регистрация"])
    username = st.sidebar.text_input("Логин")
    password = st.sidebar.text_input("Пароль", type='password')
    
    if st.sidebar.button("Выполнить"):
        conn = sqlite3.connect('school_focus_final_v14.db')
        c = conn.cursor()
        if auth_mode == "Регистрация":
            try:
                c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
                conn.commit()
                st.sidebar.success("Аккаунт создан! Теперь войдите.")
            except:
                st.sidebar.error("Такой логин уже занят.")
        else:
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user_data = c.fetchone()
            if user_data and check_hashes(password, user_data[2]):
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user_data[0]
                st.session_state['username'] = username
                st.rerun()
            else:
                st.sidebar.error("Неверный логин или пароль.")
        conn.close()
    
    st.info("Пожалуйста, авторизуйтесь для работы с системой.")
    st.stop()

# --- SIDEBAR ПОСЛЕ ВХОДА ---
st.sidebar.title(f"👤 {st.session_state['username']}")
if st.sidebar.button("Выйти из системы"):
    st.session_state['logged_in'] = False
    st.rerun()

# БЛОК РАЗРАБОТЧИКА
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div style="text-align: center;">
        <p style="font-size: 0.85em; color: gray; margin-bottom: 5px;">Разработчик приложения:</p>
        <p style="font-weight: bold; color: #4A90E2; margin-bottom: 10px;">Адильбаева Айнура Дуйшембековна</p>
        <a href="https://instagram.com/uchitel_tdk" target="_blank" style="text-decoration: none;">
            <div style="display: inline-block; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); 
                        color: white; padding: 6px 15px; border-radius: 20px; font-weight: bold; font-size: 0.8em;">
                📸 @uchitel_tdk
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True
)
st.sidebar.divider()

lang_choice = st.sidebar.selectbox("🌍 Язык / Тіл", ['RU', 'KZ'])
L = LANGS[lang_choice]
menu = st.sidebar.radio(L['title'], [L['nav_new'], L['nav_rating'], L['nav_map']])

# --- 6. ОСНОВНЫЕ РАЗДЕЛЫ ---

if menu == L['nav_new']:
    st.header(L['header'])
    with st.form("comprehensive_form"):
        st.subheader("1. Общая информация / Жалпы ақпарат")
        c1, c2, c3 = st.columns(3)
        teacher = c1.text_input(L['teacher'])
        student = c1.text_input(L['student'])
        subject = c2.text_input(L['subject'])
        grade = c2.text_input(L['grade'])
        date = c3.date_input(L['date'], datetime.now())
        quarter = c3.selectbox(L['quarter'], [1, 2, 3, 4])
        topic = st.text_input(L['topic'])
        goal = st.text_area(L['goal'])
        purpose = st.text_input(L['purpose'], value="Анализ работы с академическим резервом")

        st.divider()
        st.subheader(L['res_header'])
        res_list = []
        for i in range(1, 4):
            cols = st.columns([2, 3, 3, 1])
            fio = cols[0].text_input(f"{L['res_fio']} {i}", key=f"fio_{i}")
            act = cols[1].text_input(L['res_inter'], key=f"act_{i}")
            re = cols[2].text_input(L['res_react'], key=f"re_{i}")
            idx = cols[3].text_input("УД/ТБ", key=f"idx_{i}")
            res_list.append({"fio": fio, "act": act, "re": re, "idx": idx})

        st.divider()
        st.subheader(L['stages_header'])
        st_tabs = st.tabs(["Начало", "Середина", "Конец", "Методы/ИКТ"])
        with st_tabs[0]:
            cl1, cl2 = st.columns(2)
            start_t = cl1.text_area(L['action_t'] + " (Start)", key="st_t")
            start_s = cl2.text_area(L['action_s'] + " (Start)", key="st_s")
        with st_tabs[1]:
            cl1, cl2 = st.columns(2)
            middle_t = cl1.text_area(L['action_t'] + " (Middle)", key="md_t")
            middle_s = cl2.text_area(L['action_s'] + " (Middle)", key="md_s")
        with st_tabs[2]:
            cl1, cl2 = st.columns(2)
            end_t = cl1.text_area(L['action_t'] + " (End)", key="ed_t")
            end_s = cl2.text_area(L['action_s'] + " (End)", key="ed_s")
        with st_tabs[3]:
            ict = st.text_area(L['ict_label'], key="ict_v")
            methods = st.text_area(L['methods_label'], key="meth_v")
            reflection = st.text_area(L['reflection'], key="refl_v")

        st.divider()
        st.subheader(L['crit_header'])
        scores_res, comms_res = {}, {}
        for i, crit in enumerate(L['criteria_list']):
            cl, cs, cf = st.columns([3, 1, 3])
            cl.write(f"**{i+1}. {crit}**")
            sc_val = cs.selectbox(L['score_label'], [2, 1, 0], format_func=lambda x: "2+" if x==2 else "1+" if x==1 else "-", key=f"sc_{i}")
            cm_val = cf.text_input(L['fact_label'], key=f"cm_{i}")
            scores_res[f"k{i}"] = sc_val
            comms_res[f"k{i}"] = cm_val

        st.divider()
        st.subheader(L['conclusion_header'])
        s1, s2, s3 = st.columns(3)
        sv1 = s1.text_input("1", key="s1_v")
        sv2 = s2.text_input("2", key="s2_v")
        sv3 = s3.text_input("3", key="s3_v")
        g1, g2, g3 = st.columns(3)
        gv1 = g1.text_input("1 ", key="g1_v")
        gv2 = g2.text_input("2 ", key="g2_v")
        gv3 = g3.text_input("3 ", key="g3_v")
        advice = st.text_area(L['final_advice'], key="adv_v")

        if st.form_submit_button(L['save_btn']):
            total = sum(scores_res.values())
            percent = (total / 16) * 100
            conn = sqlite3.connect('school_focus_final_v14.db')
            c = conn.cursor()
            c.execute('''INSERT INTO reports 
                (user_id, date, quarter, teacher, student, subject, grade, topic, goal, purpose, start_t, start_s, middle_t, middle_s, end_t, end_s, ict_usage, methods, reflection, reserve_json, scores_json, comments_json, s1, s2, s3, g1, g2, g3, advice, percent, lang) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                (st.session_state['user_id'], date.strftime("%Y-%m-%d"), quarter, teacher, student, subject, grade, topic, goal, purpose, start_t, start_s, middle_t, middle_s, end_t, end_s, ict, methods, reflection, json.dumps(res_list), json.dumps(scores_res), json.dumps(comms_res), sv1, sv2, sv3, gv1, gv2, gv3, advice, percent, lang_choice))
            conn.commit()
            conn.close()
            st.success("✅ Сохранено в ваш личный кабинет!")

elif menu == L['nav_rating']:
    st.header(L['nav_rating'])
    conn = sqlite3.connect('school_focus_final_v14.db')
    df = pd.read_sql_query("SELECT * FROM reports WHERE user_id = ?", conn, params=(st.session_state['user_id'],))
    conn.close()
    if not df.empty:
        st.dataframe(df[['date', 'teacher', 'subject', 'grade', 'percent']])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(L['excel_btn'], output.getvalue(), "Focus_Report.xlsx")
    else:
        st.info("Ваша база данных пока пуста.")

elif menu == L['nav_map']:
    st.header(L['nav_map'])
    conn = sqlite3.connect('school_focus_final_v14.db')
    df = pd.read_sql_query("SELECT * FROM reports WHERE user_id = ?", conn, params=(st.session_state['user_id'],))
    conn.close()
    if not df.empty:
        t_name = st.selectbox(L['teacher'], df['teacher'].unique())
        t_df = df[df['teacher'] == t_name].sort_values('date')
        st.plotly_chart(px.line(t_df, x='date', y='percent', markers=True, title=f"Динамика: {t_name}"))
        for _, r in t_df.iterrows():
            with st.expander(f"{r['date']} - {r['topic']} ({r['percent']}%)"):
                word_data = create_official_docx(r, lang_choice)
                st.download_button(L['word_btn'], word_data, f"Protokol_{r['teacher']}_{r['date']}.docx", key=f"btn_{r['id']}")
