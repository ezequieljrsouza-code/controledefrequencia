import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Frequência - Ezequiel Miranda", page_icon="📝")

# Estilo CSS
st.markdown("<style>.stCode { background-color: #f1f5f9; border-left: 5px solid #2563eb; }</style>", unsafe_allow_html=True)

# Configuração da API
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ Configure 'GEMINI_API_KEY' nos Secrets do Streamlit.")
    st.stop()

if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

def process_image(uploaded_file):
    try:
        # Tenta o modelo mais estável de 2026
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = PIL.Image.open(uploaded_file)
        
        prompt = """
        Analise a tabela e extraia os dados.
        Retorne APENAS um JSON: [{"nome": "NOME", "categoria": "SIM ou PULMÃO"}]
        """
        
        response = model.generate_content([prompt, img])
        
        # Limpeza do JSON
        txt = response.text
        start, end = txt.find('['), txt.rfind(']') + 1
        data = json.loads(txt[start:end])
        
        for item in data:
            nome = item.get("nome", "").strip().upper()
            if len(nome) > 2 and nome not in st.session_state.attendance:
                st.session_state.attendance[nome] = {
                    "categoria": item.get("categoria", "SIM").strip().upper(),
                    "status": "Presente", 
                    "justification": ""
                }
        return True
    except Exception as e:
        # Se der 404, vamos listar os modelos que sua chave suporta para diagnosticar
        st.error(f"Erro de Conexão: {e}")
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            st.info(f"Modelos disponíveis para sua chave: {available_models}")
        except:
            st.warning("Não foi possível listar os modelos. Verifique se sua API Key é válida no Google AI Studio.")
        return False

st.title("📝 Controle de Frequência")
st.caption("Responsável: Ezequiel Miranda | Marituba-PA")

# Upload
with st.expander("📷 Carregar Foto", expanded=not st.session_state.attendance):
    uploaded_file = st.file_uploader("Suba a imagem da lista", type=["png", "jpg", "jpeg"])
    if uploaded_file and st.button("Processar Lista"):
        with st.spinner("Processando..."):
            if process_image(uploaded_file):
                st.success("Carregado!")
                st.rerun()

# Chamada
if st.session_state.attendance:
    st.write("---")
    nomes = sorted(st.session_state.attendance.keys())
    for n in nomes:
        d = st.session_state.attendance[n]
        c1, c2, c3 = st.columns([2, 1, 1.5])
        with c1:
            st.markdown(f"**{n}** {'🫁' if 'PULM' in d['categoria'] else ''}")
        with c2:
            st.session_state.attendance[n]["status"] = st.radio(f"S_{n}", ["Presente", "ABS"], key=f"s_{n}", label_visibility="collapsed", horizontal=True)
        with c3:
            if st.session_state.attendance[n]["status"] == "ABS":
                st.session_state.attendance[n]["justification"] = st.selectbox(f"J_{n}", ["Injustificado", "Atestado", "Declaração", "Suspensão"], key=f"j_{n}", label_visibility="collapsed")
            else: st.write("-")

    if st.button("📋 Gerar Relatório"):
        hoje = datetime.now().strftime("%d/%m")
        na, pulm = [], []
        for n in nomes:
            d = st.session_state.attendance[n]
            if d["status"] == "ABS":
                txt = f"- {n} {'❌ ' if 'PULM' in d['categoria'] else ''}( {d['justification']})"
                if "PULM" in d["categoria"]: pulm.append(txt)
                else: na.append(txt)
        
        rel = f"ABS ({hoje})\n\nN/A\n" + ("\n".join(na) if na else "Nenhum")
        rel += f"\n\nPulmões 🫁\n" + ("\n".join(pulm) if pulm else "Nenhum")
        rel += f"\n\nABS real: {len(na)}"
        st.code(rel, language="text")

if st.sidebar.button("🗑️ Limpar"):
    st.session_state.attendance = {}
    st.rerun()
