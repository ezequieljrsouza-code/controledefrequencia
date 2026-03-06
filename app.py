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
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração de Segurança (Secrets)
try:
    # Busca a chave configurada no dashboard do Streamlit Cloud
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ Erro: A chave 'GEMINI_API_KEY' não foi configurada nos Secrets do Streamlit.")
    st.info("Acesse Settings -> Secrets no painel do Streamlit e adicione: GEMINI_API_KEY = 'sua_chave'")
    st.stop()

# 3. Inicialização do Estado da Sessão
if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

# 4. Função de Processamento com IA
def process_image(uploaded_file):
    try:
        # Usando o caminho completo do modelo para evitar erro 404
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        img = PIL.Image.open(uploaded_file)
        
        prompt = """
        Analise a tabela na imagem. 
        Extraia os nomes da primeira coluna e o status da segunda coluna (PRODUTIVO ?).
        Retorne APENAS um JSON no seguinte formato:
        [
            {"nome": "NOME DA PESSOA", "categoria": "SIM ou PULMÃO"}
        ]
        Ignore o cabeçalho 'Nome' e 'Produtivo'. Se na segunda coluna estiver 'PULMÃO', marque como 'PULMÃO'.
        """
        
        response = model.generate_content([prompt, img])
        
        # Limpeza do texto para extrair apenas o JSON
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        for item in data:
            nome = item["nome"].strip().upper()
            if len(nome) < 3: continue # Pula ruídos ou textos curtos demais
            
            # Adiciona apenas se o nome ainda não estiver na lista
            if nome not in st.session_state.attendance:
                st.session_state.attendance[nome] = {
                    "categoria": item["categoria"].strip().upper(),
                    "status": "Presente", 
                    "justification": ""
                }
        return True
    except Exception as e:
        st.error(f"Erro ao processar imagem: {e}")
        return False

# 5. Interface Principal
st.title("📝 Controle de Frequência")
st.caption("Responsável: Ezequiel Miranda | Marituba-PA")

# Upload de Arquivo
with st.expander("📷 Carregar Lista de Produtividade", expanded=not st.session_state.attendance):
    uploaded_file = st.file_uploader("Selecione a imagem da lista", type=["png", "jpg", "jpeg"])
    if uploaded_file and st.button("Extrair Nomes da Imagem"):
        with st.spinner("A IA está lendo os nomes..."):
            if process_image(uploaded_file):
                st.success("Nomes carregados com sucesso!")
                st.rerun()

# 6. Lista de Chamada Interativa
if st.session_state.attendance:
    st.write("---")
    st.subheader("Lista de Presença")
    
    # Ordena nomes para facilitar a busca
    nomes_ordenados = sorted(st.session_state.attendance.keys())
    
    for name in nomes_ordenados:
        dados = st.session_state.attendance[name]
        col_nome, col_status, col_just = st.columns([2, 1, 1.5])
        
        with col_nome:
            # Identifica visualmente se é pulmão
            is_pulmao = "PULM" in dados["categoria"]
            st.markdown(f"**{name}** {'🫁' if is_pulmao else ''}")
            
        with col_status:
            status = st.radio(
                f"Status_{name}", ["Presente", "ABS"], 
                key=f"st_{name}", label_visibility="collapsed", horizontal=True
            )
            st.session_state.attendance[name]["status"] = status
            
        with col_just:
            if status == "ABS":
                justificativa = st.selectbox(
                    f"Just_{name}", ["Injustificado", "Atestado", "Declaração", "Suspensão"],
                    key=f"js_{name}", label_visibility="collapsed"
                )
                st.session_state.attendance[name]["justification"] = justificativa
            else:
                st.session_state.attendance[name]["justification"] = ""
                st.write("-")

    # 7. Gerador de Relatório Formatado
    st.write("---")
    if st.button("📋 Gerar Relatório para WhatsApp"):
        hoje = datetime.now().strftime("%d/%m")
        lista_na = []
        lista_pulmao = []
        
        for n in nomes_ordenados:
            d = st.session_state.attendance[n]
            if d["status"] == "ABS":
                # Formatação conforme o modelo solicitado
                if "PULM" in d["categoria"]:
                    lista_pulmao.append(f"- {n} ❌ ( {d['justification']})")
                else:
                    lista_na.append(f"- {n} ( {d['justification']})")
        
        # Montagem do Texto Final
        relatorio = f"ABS ({hoje})\n\n"
        relatorio += "N/A\n"
        relatorio += "\n".join(lista_na) if lista_na else "Nenhum"
        
        relatorio += "\n\nPulmões 🫁\n"
        relatorio += "\n".join(lista_pulmao) if lista_pulmao else "Nenhum"
        
        relatorio += f"\n\nABS real: {len(lista_na)}"
        
        st.subheader("Relatório Pronto:")
        st.code(relatorio, language="text")
        st.info("Copie o texto acima e cole no WhatsApp.")

# Barra lateral para controle
if st.sidebar.button("🗑️ Limpar Lista Atual"):
    st.session_state.attendance = {}
    st.rerun()

st.sidebar.write("---")
st.sidebar.info("Dica: Use imagens com boa iluminação para a IA não errar os nomes.")
