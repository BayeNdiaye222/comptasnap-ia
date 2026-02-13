import streamlit as st
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import base64
import json
import io

st.set_page_config(page_title="ComptaSnap IA", page_icon="📊")

# --- CONFIGURATION ---
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
# Utilisation du modèle Vision de Llama 3.2
model = ChatGroq(model_name="llama-3.2-11b-vision-preview", groq_api_key=GROQ_API_KEY)

st.title("📊 ComptaSnap IA")
st.write("Financez votre Master en aidant les commerçants à gérer leurs factures !")

# --- CHARGEMENT DE L'IMAGE ---
uploaded_file = st.file_uploader("Prenez une photo ou chargez une facture", type=['png', 'jpg', 'jpeg'])

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

if uploaded_file:
    st.image(uploaded_file, caption="Facture à traiter", width=300)
    
    if st.button("🚀 Extraire et Créer Excel"):
        with st.spinner("L'IA analyse les montants..."):
            image_base64 = encode_image(uploaded_file.getvalue())
            
            prompt = """
            Analyse cette image de facture. 
            Extrais les infos suivantes en JSON pur :
            {
                "fournisseur": "",
                "date": "",
                "HT": 0.0,
                "TVA": 0.0,
                "TTC": 0.0,
                "devise": ""
            }
            Réponds uniquement avec le JSON.
            """
            
            msg = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            )
            
            response = model.invoke([msg])
            
            try:
                # Nettoyage de la réponse pour ne garder que le JSON
                clean_content = response.content.replace('```json', '').replace('```', '').strip()
                data_dict = json.loads(clean_content)
                
                # Création du tableau avec Pandas
                df = pd.DataFrame([data_dict])
                st.write("### ✅ Données détectées :")
                st.table(df) # Affiche un beau tableau sur le site
                
                # Génération du fichier Excel en mémoire
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Facture')
                
                # Bouton de téléchargement
                st.download_button(
                    label="📥 Télécharger le fichier Excel",
                    data=output.getvalue(),
                    file_name="facture_extraite.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.balloons() # Petite animation pour fêter ça !

            except Exception as e:
                st.error("Erreur lors de l'extraction. Assurez-vous que l'image est lisible.")
                st.write(response.content) # Pour voir ce que l'IA a répondu en cas d'erreur