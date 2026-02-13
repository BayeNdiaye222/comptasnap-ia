import streamlit as st
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import base64
import json
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="ComptaSnap Pro", page_icon="📊", layout="wide")

# --- CONFIGURATION IA (GROQ) ---
# Assure-toi que GROQ_API_KEY est bien dans tes Secrets Streamlit
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
model = ChatGroq(model_name="llama-3.2-11b-vision-preview", groq_api_key=GROQ_API_KEY)

# --- INTERFACE PROFESSIONNELLE ---
st.title("📊 ComptaSnap Pro")
st.markdown("### L'intelligence artificielle au service de votre comptabilité")
st.info("Simplifiez la saisie de vos dépenses : Prenez une photo, nous créons votre Excel.")

# --- FONCTION POUR ENCODER L'IMAGE ---
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# --- ZONE DE CHARGEMENT ---
st.divider()
uploaded_file = st.file_uploader("📸 Prenez une photo ou chargez une facture (JPG, PNG)", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.image(uploaded_file, caption="Facture originale", use_container_width=True)
    
    with col2:
        if st.button("🚀 Extraire les données vers Excel"):
            with st.spinner("Analyse intelligente en cours..."):
                try:
                    # Encodage de l'image pour l'IA Vision
                    image_base64 = encode_image(uploaded_file.getvalue())
                    
                    # Le Prompt pour forcer l'extraction structurée
                    prompt = """
                    Analyse cette image de facture. 
                    Extrais UNIQUEMENT les infos suivantes au format JSON pur :
                    {
                        "fournisseur": "nom de l'entreprise",
                        "date": "JJ/MM/AAAA",
                        "HT": 0.0,
                        "TVA": 0.0,
                        "TTC": 0.0,
                        "devise": "XOF/EUR/USD"
                    }
                    Ne réponds rien d'autre que le JSON.
                    """
                    
                    msg = HumanMessage(
                        content=[
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    )
                    
                    response = model.invoke([msg])
                    
                    # Nettoyage et lecture du JSON reçu
                    clean_content = response.content.replace('```json', '').replace('```', '').strip()
                    data_dict = json.loads(clean_content)
                    
                    # Création du tableau de données (DataFrame)
                    df = pd.DataFrame([data_dict])
                    
                    st.success("✅ Analyse terminée !")
                    st.table(df) # Affichage du résultat à l'écran
                    
                    # Préparation du fichier Excel en mémoire
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='ComptaSnap_Extract')
                    
                    # Bouton de téléchargement
                    st.download_button(
                        label="📥 Télécharger le fichier Excel",
                        data=output.getvalue(),
                        file_name=f"Facture_{data_dict['fournisseur']}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.balloons()

                except Exception as e:
                    st.error("Désolé, l'IA n'a pas pu lire correctement cette image. Réessayez avec une photo plus nette.")
                    # Optionnel pour debug : st.write(e)

# --- PIED DE PAGE ---
st.sidebar.markdown("---")
st.sidebar.write("💳 **Version Pro**")
st.sidebar.caption("Développé pour simplifier la vie des entrepreneurs.")