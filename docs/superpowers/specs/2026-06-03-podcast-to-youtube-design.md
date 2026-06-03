# Podcast → YouTube — Design Spec

## Objectif

App web locale (Mac) qui combine une mini vidéo en boucle avec une piste audio podcast pour générer une vidéo prête à poster sur YouTube.

## Cas d'utilisation

Marina produit des épisodes de podcast. Elle possède :
- Une mini vidéo de 2 min créée sur Canva (~20 Mo, MP4)
- Une piste audio du podcast (WAV, ~240 Mo, durée 20 min à 1h)

L'outil boucle la mini vidéo pendant toute la durée de l'audio et produit un fichier MP4 final.

## Stack technique

- **Backend** : Python 3 + Flask
- **Frontend** : HTML/CSS/JS (une seule page)
- **Traitement vidéo** : FFmpeg (installé via Homebrew)
- **Hébergement** : Local uniquement (localhost:5000)

## Architecture

### Serveur (app.py)

- Serveur Flask avec 4 routes :
  - `GET /` — sert la page HTML
  - `POST /generate` — reçoit les fichiers, lance FFmpeg, retourne l'ID du job
  - `GET /status/<job_id>` — retourne la progression du traitement
  - `GET /download/<job_id>` — sert le fichier généré
- Les fichiers uploadés sont stockés temporairement dans `uploads/`
- Les fichiers générés vont dans `output/`
- Les fichiers temporaires dans `uploads/` sont supprimés après génération

### Commande FFmpeg

```
ffmpeg -stream_loop -1 -i <video> -i <audio> -shortest -c:v libx264 -c:a aac -b:a 192k <output>.mp4
```

- `-stream_loop -1` : boucle la vidéo indéfiniment
- `-shortest` : arrête quand la piste la plus courte (l'audio) se termine
- `-c:v libx264` : codec vidéo compatible YouTube
- `-c:a aac -b:a 192k` : audio AAC qualité standard

### Frontend (index.html)

Page unique avec :
1. Titre "Podcast → YouTube"
2. Bouton de sélection pour la mini vidéo (MP4)
3. Bouton de sélection pour la piste audio (WAV/MP3)
4. Bouton "Générer la vidéo"
5. Barre de progression pendant le traitement
6. Bouton "Télécharger" une fois terminé

Style sobre, fond clair, centré, fonctionnel.

### Gestion d'erreurs

- Vérification que les fichiers sont bien uploadés avant de lancer
- Vérification du format (vidéo : MP4 ; audio : WAV ou MP3)
- Message d'erreur clair en rouge si FFmpeg échoue

## Structure du projet

```
~/Projects/podcast-to-youtube/
├── app.py
├── templates/
│   └── index.html
├── static/
│   └── style.css
├── uploads/           (créé automatiquement)
├── output/            (créé automatiquement)
└── requirements.txt
```

## Utilisation

```bash
cd ~/Projects/podcast-to-youtube
python app.py
```

Le navigateur s'ouvre automatiquement sur http://localhost:5000.

## Prérequis (installation unique)

- Python 3 (déjà présent sur Mac)
- FFmpeg : `brew install ffmpeg`
- Flask : `pip install flask`

## Hors scope

- Pas d'hébergement en ligne
- Pas de titre/texte superposé
- Pas de fondu début/fin
- Pas de traitement par lots
