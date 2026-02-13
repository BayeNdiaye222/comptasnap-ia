import streamlit as st
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import base64
import json
import io
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="ComptaSnap Pro", page_icon="📊", layout="wide")

# --- CONFIGURATION IA (GROQ) ---
# On définit une liste de modèles par ordre de priorité pour éviter les erreurs "Decommissioned"
MODELES_A_TESTER = [
    "llama-3.2-11b-vision-instant", 
    "llama-3.2-90b-vision-instant",
    "llama-3.2-11b-vision-preview"
]

@st.cache_resource
def load_model():
    if "GROQ_API_KEY" not in st.secrets:
        st.error("Clé API manquante dans les Secrets Streamlit.")
        st.stop()
    
    # Tentative de connexion avec le premier modèle disponible
    for nom in MODELES_A_TESTER:
        try:
            m = ChatGroq(model_name=nom, groq_api_key=st.secrets["GROQ_API_KEY"])
            return m
        except:
            continue
    return ChatGroq(model_name=MODELES_A_TESTER[0], groq_api_key=st.secrets["GROQ_API_KEY"])

model = load_model()

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
            if not uploaded_file:
                st.warning("Veuillez d'abord charger une image.")
            else:
                with st.spinner("Analyse intelligente en cours..."):
                    try:
                        # Encodage de l'image
                        image_base64 = encode_image(uploaded_file.getvalue())
                        
                        # Prompt optimisé
                        prompt = """
                        Analyse cette image de facture ou reçu. 
                        Extrais les infos suivantes au format JSON uniquement. 
                        Structure :
                        {
                            "fournisseur": "nom de l'entreprise",
                            "date": "JJ/MM/AAAA",
                            "HT": 0.0,
                            "TVA": 0.0,
                            "TTC": 0.0,
                            "devise": "XOF"
                        }
                        Ne réponds rien d'autre que le JSON brut.
                        """
                        
                        msg = HumanMessage(
                            content=[
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        )
                        
                        response = model.invoke([msg])
                        full_text = response.content

                        # --- NETTOYAGE DU JSON ---
                        match = re.search(r'\{.*\}', full_text, re.DOTALL)
                        if match:
                            json_str = match.group()
                            data_dict = json.loads(json_str)
                            
                            # Création du DataFrame
                            df = pd.DataFrame([data_dict])
                            
                            st.success("✅ Analyse terminée !")
                            st.subheader("Données extraites")
                            st.table(df)
                            
                            # Génération Excel
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False, sheet_name='Extraction')
                            
                            st.download_button(
                                label="📥 Télécharger le fichier Excel",
                                data=output.getvalue(),
                                file_name=f"Facture_{data_dict.get('fournisseur', 'Inconnu')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            st.balloons()
                        else:
                            st.error("L'IA n'a pas pu structurer les données. Vérifiez la netteté de l'image.")
                            with st.expander("Voir la réponse brute"):
                                st.write(full_text)

                    except Exception as e:
                        st.error(f"Détail de l'erreur : {str(e)}")
                        st.info("Conseil : Faites un 'Reboot' de l'app dans le menu Streamlit si l'erreur persiste.")

# --- PIED DE PAGE ---
st.sidebar.markdown("---")
st.sidebar.write("💳 **Version Pro v1.1**")
st.sidebar.caption("Développé pour l'automatisation comptable.")