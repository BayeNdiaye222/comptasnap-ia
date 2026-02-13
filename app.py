import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import io
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="ComptaSnap Pro", page_icon="📊")

# Remplace l'ancienne ligne par celle-ci
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    # On utilise 'gemini-1.5-flash' (nom standard)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop()

st.title("📊 ComptaSnap Pro")
st.info("Version ultra-stable pour démonstration.")

uploaded_file = st.file_uploader("📸 Charger une facture", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=300)
    
    if st.button("🚀 Extraire les données"):
        with st.spinner("Analyse Google Vision en cours..."):
            prompt = "Extrais les infos de cette facture en JSON : fournisseur, date, HT, TVA, TTC (nombres uniquement pour les montants)."
            
            response = model.generate_content([prompt, img])
            
            try:
                # Nettoyage et lecture du JSON
                json_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(json_text)
                df = pd.DataFrame([data])
                
                st.success("✅ Terminé !")
                st.table(df)
                
                # Export Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Télécharger Excel", output.getvalue(), "facture.xlsx")
                st.balloons()
            except:
                st.error("Erreur de lecture. Réessayez avec une photo plus nette.")
                st.write(response.text)