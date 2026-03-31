import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
from database import db
from models import Reservation, Cours, Salle, Creneau, Professeur, Groupe, Etudiant
from datetime import datetime, date

def get_base64_image(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return img_base64

def get_dataframe_sql(query):
    # Use pandas read_sql to execute a pure query and return a dataframe
    return pd.read_sql(query, db.engine)

def get_base_dataframes():
    """Retrieve necessary dataframes from DB"""
    df_res = pd.read_sql("SELECT * FROM reservation", db.engine)
    df_cours = pd.read_sql("SELECT * FROM cours", db.engine)
    df_salle = pd.read_sql("SELECT * FROM salle", db.engine)
    df_creneau = pd.read_sql("SELECT * FROM creneau", db.engine)
    df_prof = pd.read_sql("SELECT * FROM professeur", db.engine)
    df_groupe = pd.read_sql("SELECT * FROM groupe", db.engine)
    df_etu = pd.read_sql("SELECT * FROM etudiant", db.engine)
    
    # Merge for a comprehensive view
    if not df_res.empty:
        df_full = df_res.merge(df_cours, on='id_cours', how='left', suffixes=('', '_cours'))
        df_full = df_full.merge(df_salle, on='id_salle', how='left', suffixes=('', '_salle'))
        df_full = df_full.merge(df_creneau, on='id_creneau', how='left', suffixes=('', '_creneau'))
        
        # Convert time objects to compute duration
        if 'heure_debut' in df_full.columns and 'heure_fin' in df_full.columns:
            def calc_duration(row):
                if pd.notnull(row['heure_debut']) and pd.notnull(row['heure_fin']):
                    hd = pd.to_datetime(row['heure_debut'], format='%H:%M:%S', errors='coerce')
                    hf = pd.to_datetime(row['heure_fin'], format='%H:%M:%S', errors='coerce')
                    if not pd.isnull(hd) and not pd.isnull(hf):
                        return (hf - hd).total_seconds() / 3600.0
                return 0
            df_full['duree'] = df_full.apply(calc_duration, axis=1)
        else:
            df_full['duree'] = 0
            
    else:
        df_full = pd.DataFrame()
        
    return {
        'res': df_res, 'cours': df_cours, 'salle': df_salle, 
        'creneau': df_creneau, 'prof': df_prof, 'groupe': df_groupe, 
        'etu': df_etu, 'full': df_full
    }

def compute_admin_kpis():
    dfs = get_base_dataframes()
    df = dfs['full']
    
    if df.empty:
        return {'error': 'Pas de données de réservation'}

    df_conf = df[df['statut'] == 'confirmee']
    
    # 1. Taux d'occupation par salle
    heures_par_salle = df_conf.groupby('numero_salle')['duree'].sum()
    heures_ouvrables = 60 # Arbitrary 60h/week
    taux_occ_salle = (heures_par_salle / heures_ouvrables * 100).round(1).to_dict()
    
    # 2. Nombre moyen d'heures par enseignant
    if not dfs['prof'].empty:
        heures_par_prof = df_conf.groupby('id_professeur')['duree'].sum()
        moy_heures_prof = round(heures_par_prof.sum() / len(dfs['prof']), 1)
    else:
        moy_heures_prof = 0
        
    # 3. Nombre moyen d'heures par étudiant et Taux d'absence (Simulation)
    if not dfs['etu'].empty and not dfs['groupe'].empty:
        # Heures par groupe
        heures_par_groupe = df_conf.groupby('id_groupe')['duree'].sum()
        moy_heures_etu = round(heures_par_groupe.mean(), 1) if not heures_par_groupe.empty else 0
    else:
        moy_heures_etu = 0
        
    # Taux d'absence simulé basé sur une distribution normale (mean=5%, std=2%)
    taux_absence = max(0, round(np.random.normal(5, 2), 1))
    
    # 4. Taux de conflits en termes de disponibilité de salle
    # Un conflit est une réservation pour la même salle au même créneau
    conflits = df[df.duplicated(subset=['id_salle', 'id_creneau', 'jour'], keep=False)]
    taux_conflits = round(len(conflits) / len(df) * 100, 1) if not df.empty else 0
    
    # 5. Taux de modification de l'emploi du temps
    modifie_ou_annule = df[(df['statut'] != 'confirmee') | (df['modifie_le'].notnull())]
    taux_modifs = round(len(modifie_ou_annule) / len(df) * 100, 1) if not df.empty else 0
    
    # 6. Périodes de surcharge (Heures_Pleines, Heures_Creuses)
    df_conf['heure'] = pd.to_datetime(df_conf['heure_debut'], format='%H:%M:%S', errors='coerce').dt.hour
    repartition_heures = df_conf.groupby('heure').size()
    heures_pleines = repartition_heures[repartition_heures > repartition_heures.mean()].index.tolist()
    
    # Visualisations avec Matplotlib & Seaborn
    sns.set_theme(style="whitegrid")
    
    # A. Heatmap: Jours vs Heures
    heatmap_base64 = None
    try:
        if not df_conf.empty and 'jour' in df_conf.columns and 'heure' in df_conf.columns:
            # Cast 'jour' to datetime if needed to get day name, but it's a date string usually from sqlite
            df_conf['jour_dt'] = pd.to_datetime(df_conf['jour'])
            df_conf['jour_nom'] = df_conf['jour_dt'].dt.day_name(locale='fr_FR.utf8') if hasattr(df_conf['jour_dt'].dt, 'day_name') else df_conf['jour_dt'].dt.dayofweek
            
            # Create pivot
            pivot_h = pd.crosstab(df_conf['jour_nom'], df_conf['heure'])
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            sns.heatmap(pivot_h, cmap="YlGnBu", annot=True, fmt="d", ax=ax1, cbar_kws={'label': 'Nombre de réservations'})
            ax1.set_title("Heatmap d'Occupation (Jours vs Heures)")
            heatmap_base64 = get_base64_image(fig1)
    except Exception as e:
        print(f"Erreur Heatmap: {e}")
        
    # B. Matrice de corrélation
    corr_base64 = None
    try:
        from scipy.stats import spearmanr
        # We need numerical columns to correlate. Let's create a numerical summary per room.
        room_stats = df_conf.groupby('numero_salle').agg({'duree': 'sum', 'capacite': 'first', 'id_cours': 'count'}).rename(columns={'id_cours': 'nb_reservations'})
        if len(room_stats) > 1:
            fig2, ax2 = plt.subplots(figsize=(6, 5))
            sns.heatmap(room_stats.corr(), annot=True, cmap="coolwarm", center=0, ax=ax2)
            ax2.set_title("Matrice de Corrélation des Salles")
            corr_base64 = get_base64_image(fig2)
    except Exception as e:
        print(f"Erreur Corrélation: {e}")
        
    # C. Donut Chart Type Salles
    donut_base64 = None
    try:
        type_salles = df_conf['type_salle'].value_counts()
        if not type_salles.empty:
            fig3, ax3 = plt.subplots(figsize=(6, 6))
            ax3.pie(type_salles.values, labels=type_salles.index, autopct='%1.1f%%', startangle=90, pctdistance=0.85, colors=sns.color_palette('pastel')[0:len(type_salles)])
            # Draw circle
            centre_circle = plt.Circle((0,0),0.70,fc='white')
            fig3.gca().add_artist(centre_circle)
            ax3.axis('equal')  
            ax3.set_title('Répartition par Type de Salle')
            donut_base64 = get_base64_image(fig3)
    except Exception as e:
        print(f"Erreur Donut: {e}")

    return {
        'taux_occ_salle': taux_occ_salle,
        'moy_heures_prof': moy_heures_prof,
        'moy_heures_etu': moy_heures_etu,
        'taux_absence': taux_absence,
        'taux_conflits': taux_conflits,
        'taux_modifs': taux_modifs,
        'heures_pleines': [f"{int(h)}h" for h in heures_pleines if pd.notnull(h)],
        'heatmap_b64': heatmap_base64,
        'corr_b64': corr_base64,
        'donut_b64': donut_base64
    }

def compute_prof_kpis(id_professeur):
    dfs = get_base_dataframes()
    df = dfs['full']
    
    if df.empty:
        return {}
        
    df_prof_all = df[df['id_professeur'] == id_professeur]
    df_prof_conf = df_prof_all[df_prof_all['statut'] == 'confirmee']
    
    if df_prof_conf.empty:
        return {'total_heures': 0, 'nb_cours': 0, 'taux_modifs': 0, 'salles_freq': []}
        
    total_heures = df_prof_conf['duree'].sum()
    nb_cours = df_prof_conf['id_cours'].nunique()
    
    modifie_ou_annule = df_prof_all[(df_prof_all['statut'] != 'confirmee') | (df_prof_all['modifie_le'].notnull())]
    taux_modifs = round(len(modifie_ou_annule) / len(df_prof_all) * 100, 1) if not df_prof_all.empty else 0
    
    salles_freq = df_prof_conf['numero_salle'].value_counts().head(3).to_dict()
    
    return {
        'total_heures': total_heures,
        'nb_cours': nb_cours,
        'taux_modifs': taux_modifs,
        'salles_freq': salles_freq
    }
    

