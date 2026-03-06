import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Controle de Frequência - Ezequiel Miranda", page_icon="📝", layout="centered")

# Estilo CSS para melhorar a aparência
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
    }
    .report-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        font-family: monospace;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização da API Gemini usando Secrets do Streamlit
API_KEY = st.secrets["AIzaSyABFt80KlM50OPrqvGSKAR4D_3s3d8e5C4"]
genai.configure(api_key=API_KEY)

# Inicialização do estado da sessão
if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

def process_image(uploaded_file):
    """Processa a imagem usando Gemini para extrair nomes e categorias."""
    try:
        # Usando o modelo flash que é rápido e ótimo para extração de texto estruturado
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = PIL.Image.open(uploaded_file)
        
        prompt = """
        Analise a tabela na imagem. Extraia os nomes da primeira coluna e o status da segunda coluna (PRODUTIVO ?).
        Retorne EXATAMENTE UM ARRAY JSON com objetos contendo as chaves "nome" e "categoria".
        Exemplo:
        [
            {"nome": "JOAO DA SILVA", "categoria": "SIM"},
            {"nome": "MARIA SOUZA", "categoria": "PULMÃO"}
        ]
        Não inclua os cabeçalhos. Não adicione nenhum outro texto ou marcação markdown além do JSON.
        """
        
        response = model.generate_content([prompt, img])
        text = response.text.strip()
        
        # Limpando possíveis formatações markdown do Gemini
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        
        # Inicializa presença para os nomes lidos
        for item in data:
            nome = item["nome"].strip().upper()
            categoria = item["categoria"].strip().upper()
            
            # Filtro de segurança para pular cabeçalhos acidentais
            if "NOME" in nome or len(nome) < 3:
                continue
                
            if nome not in st.session_state.attendance:
                st.session_state.attendance[nome] = {
                    "categoria": categoria,
                    "status": "Presente", 
                    "justification": ""
                }
        return True
    except Exception as e:
        st.error(f"Erro ao processar imagem. Certifique-se de que a imagem está legível. Detalhe técnico: {e}")
        return False

# Interface do Usuário
st.title("📝 Controle de Frequência")
st.subheader("Responsável: Ezequiel Miranda (Marituba/PA)")

# Upload de Arquivo
with st.expander("📷 Carregar Lista de Nomes (Imagem)", expanded=not st.session_state.attendance):
    uploaded_file = st.file_uploader("Suba a foto da lista de produtividade", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        if st.button("Processar Imagem"):
            with st.spinner("Extraindo nomes e categorias com IA..."):
                if process_image(uploaded_file):
                    st.success("Dados extraídos com sucesso!")
                    st.rerun()

# Botão para limpar lista
if st.session_state.attendance:
    if st.sidebar.button("🗑️ Limpar Toda a Lista"):
        st.session_state.attendance = {}
        st.rerun()

# Lista de Chamada
if st.session_state.attendance:
    st.write("---")
    st.info(f"Total de pessoas na lista: {len(st.session_state.attendance)}")
    
    nomes_ordenados = sorted(list(st.session_state.attendance.keys()))
    
    for name in nomes_ordenados:
        data = st.session_state.attendance[name]
        col1, col2, col3 = st.columns([2, 1, 1.5])
        
        with col1:
            # Mostra um emoji de pulmão do lado do nome se for da categoria
            is_pulmao = "PULM" in data["categoria"]
            tag = " 🫁" if is_pulmao else ""
            st.markdown(f"**{name}**{tag}")
            
        with col2:
            current_status = data["status"]
            status_idx = 0 if current_status == "Presente" else 1
            
            status = st.radio(
                f"Status para {name}",
                ["Presente", "ABS"],
                index=status_idx,
                key=f"status_{name}",
                label_visibility="collapsed",
                horizontal=True
            )
            st.session_state.attendance[name]["status"] = status
            
        with col3:
            if status == "ABS":
                # Nova lista de opções incluindo Suspensão
                opcoes_just = ["Injustificado", "Atestado", "Declaração", "Suspensão"]
                
                # Tenta manter o valor anterior se ele existir nas opções
                curr_just = data.get("justification", "Injustificado")
                just_idx = opcoes_just.index(curr_just) if curr_just in opcoes_just else 0
                
                just = st.selectbox(
                    f"Justificativa para {name}",
                    opcoes_just,
                    index=just_idx,
                    key=f"just_{name}",
                    label_visibility="collapsed"
                )
                st.session_state.attendance[name]["justification"] = just
            else:
                st.session_state.attendance[name]["justification"] = ""
                st.write("-")

    # Geração do Relatório Formato WhatsApp
    st.write("---")
    st.subheader("📋 Relatório Final")
    
    # Processando os dados para o texto
    hoje = datetime.now().strftime("%d/%m")
    abs_na = []
    abs_pulmao = []
    
    for name in nomes_ordenados:
        dados = st.session_state.attendance[name]
        if dados["status"] == "ABS":
            just = dados["justification"]
            if "PULM" in dados["categoria"]:
                abs_pulmao.append(f"- {name} ❌ ( {just})")
            else:
                abs_na.append(f"- {name} ( {just})")
                
    abs_real_count = len(abs_na)
    
    # Construindo a string do relatório
    relatorio = f"ABS ({hoje})\n\n"
    relatorio += "N/A\n"
    if abs_na:
        relatorio += "\n".join(abs_na) + "\n"
    else:
        relatorio += "Nenhum\n"
        
    relatorio += "\nPulmões 🫁\n"
    if abs_pulmao:
        relatorio += "\n".join(abs_pulmao) + "\n"
    else:
        relatorio += "Nenhum\n"
        
    relatorio += f"\nABS real: {abs_real_count}"

    # Exibe o relatório para o usuário copiar
    st.code(relatorio, language="text")
    st.caption("☝️ Clique no ícone de 'copiar' no canto superior direito do quadro acima para colar no WhatsApp.")

else:
    st.warning("Aguardando carregamento de nomes via imagem.")
