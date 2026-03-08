import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(
    page_title="Frequência - Ezequiel Miranda", 
    page_icon="📝", 
    layout="centered"
)

# Estilo para melhorar a visualização
st.markdown("""
    <style>
    .stRadio [data-testid="stMarkdownContainer"] p { font-size: 0.8rem; }
    .stSelectbox label { display: none; }
    .stCode { background-color: #f1f5f9; border-left: 5px solid #2563eb; }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração de Segurança (Secrets)
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
    else:
        st.error("⚠️ Chave 'GEMINI_API_KEY' não encontrada nos Secrets do Streamlit.")
        st.stop()
except Exception as e:
    st.error(f"Erro de configuração: {e}")
    st.stop()

# 3. Inicialização do Estado da Sessão
if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

# 4. Função de Processamento com IA (Versão Blindada)
def process_image(uploaded_file):
    # Lista de nomes de modelos para tentar em sequência caso dê 404
    model_names = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "models/gemini-1.5-flash"]
    
    success = False
    response_text = ""
    
    img = PIL.Image.open(uploaded_file)
    
    for m_name in model_names:
        try:
            model = genai.GenerativeModel(m_name)
            prompt = """
            Analise a tabela de produtividade. 
            Extraia os nomes (coluna 'Nome') e o status (coluna 'PRODUTIVO ?').
            Retorne APENAS um JSON puro no formato:
            [{"nome": "NOME COMPLETO", "categoria": "SIM ou PULMÃO"}]
            Não escreva explicações, apenas o JSON.
            """
            response = model.generate_content([prompt, img])
            response_text = response.text
            success = True
            break # Se funcionou, sai do loop
        except Exception:
            continue # Tenta o próximo nome de modelo
            
    if not success:
        st.error("Não foi possível conectar aos modelos da IA (Erro 404 persistente). Verifique sua API Key.")
        return False

    try:
        # Extração limpa do JSON
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        if start == -1 or end == 0:
            st.error("A IA não retornou um formato de lista válido.")
            return False
            
        data = json.loads(response_text[start:end])
        
        for item in data:
            nome = item.get("nome", "").strip().upper()
            if len(nome) < 3: continue
            
            if nome not in st.session_state.attendance:
                cat = item.get("categoria", "SIM").strip().upper()
                st.session_state.attendance[nome] = {
                    "categoria": cat,
                    "status": "Presente", 
                    "justification": ""
                }
        return True
    except Exception as e:
        st.error(f"Erro ao ler os dados da IA: {e}")
        return False

# 5. Interface Principal
st.title("📝 Controle de Frequência")
st.caption("Responsável: Ezequiel Miranda | Marituba-PA")

# Upload
with st.expander("📷 Carregar Foto da Lista", expanded=not st.session_state.attendance):
    uploaded_file = st.file_uploader("Suba a imagem da lista de produtividade", type=["png", "jpg", "jpeg"])
    if uploaded_file and st.button("Processar Lista Agora"):
        with st.spinner("Lendo nomes com Inteligência Artificial..."):
            if process_image(uploaded_file):
                st.success("Lista carregada!")
                st.rerun()

# 6. Lista de Chamada
if st.session_state.attendance:
    st.write("---")
    nomes_ordenados = sorted(st.session_state.attendance.keys())
    
    for name in nomes_ordenados:
        dados = st.session_state.attendance[name]
        col_n, col_s, col_j = st.columns([2, 1, 1.5])
        
        with col_n:
            is_p = "PULM" in dados["categoria"]
            st.markdown(f"**{name}** {'🫁' if is_p else ''}")
            
        with col_s:
            status = st.radio(f"S_{name}", ["Presente", "ABS"], key=f"s_{name}", 
                              label_visibility="collapsed", horizontal=True)
            st.session_state.attendance[name]["status"] = status
            
        with col_j:
            if status == "ABS":
                just = st.selectbox(f"J_{name}", ["Injustificado", "Atestado", "Declaração", "Suspensão"],
                                    key=f"j_{name}", label_visibility="collapsed")
                st.session_state.attendance[name]["justification"] = just
            else:
                st.write("-")

    # 7. Relatório Final
    st.write("---")
    if st.button("📋 Gerar Relatório para WhatsApp"):
        hoje = datetime.now().strftime("%d/%m")
        na, pulm = [], []
        
        for n in nomes_ordenados:
            d = st.session_state.attendance[n]
            if d["status"] == "ABS":
                txt = f"- {n} {'❌ ' if 'PULM' in d['categoria'] else ''}( {d['justification']})"
                if "PULM" in d["categoria"]: pulm.append(txt)
                else: na.append(txt)
        
        res = f"ABS ({hoje})\n\nN/A\n" + ("\n".join(na) if na else "Nenhum")
        res += f"\n\nPulmões 🫁\n" + ("\n".join(pulm) if pulm else "Nenhum")
        res += f"\n\nABS real: {len(na)}"
        
        st.code(res, language="text")
        st.info("Copie o texto acima e envie no grupo.")

if st.sidebar.button("🗑️ Limpar Lista"):
    st.session_state.attendance = {}
    st.rerun()
