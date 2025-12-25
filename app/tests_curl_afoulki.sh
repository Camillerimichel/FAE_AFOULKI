#!/bin/bash

BASE="http://72.61.94.45:9000"

echo "=== TEST FILLEULES ==="

# GET all
curl "$BASE/filleules/"

# GET one
curl "$BASE/filleules/1"

# CREATE
curl -X POST "$BASE/filleules/" \
  -H "Content-Type: application/json" \
  -d '{
        "nom": "Amina",
        "prenom": "El",
        "village": "Tiznit",
        "email": "amina@example.com"
      }'

# UPDATE
curl -X PUT "$BASE/filleules/1" \
  -H "Content-Type: application/json" \
  -d '{
        "nom": "Amina",
        "prenom": "El",
        "village": "Agadir",
        "email": "amina.updated@example.com"
      }'

# DELETE
curl -X DELETE "$BASE/filleules/1"



echo "=== TEST PARRAINS ==="

# GET all
curl "$BASE/parrains/"

# CREATE
curl -X POST "$BASE/parrains/" \
  -H "Content-Type: application/json" \
  -d '{
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean.dupont@example.com"
      }'

# GET one
curl "$BASE/parrains/1"

# UPDATE
curl -X PUT "$BASE/parrains/1" \
  -H "Content-Type: application/json" \
  -d '{
        "nom": "Dupont",
        "prenom": "Jean-Michel",
        "email": "jeanm@example.com"
      }'

# DELETE
curl -X DELETE "$BASE/parrains/1"



echo "=== TEST PARRAINAGES ==="

curl "$BASE/parrainages/"

curl -X POST "$BASE/parrainages/" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "id_parrain": 1,
        "statut": "actif"
      }'

curl "$BASE/parrainages/1"

curl -X PUT "$BASE/parrainages/1" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "id_parrain": 1,
        "statut": "termine"
      }'

curl -X DELETE "$BASE/parrainages/1"



echo "=== TEST ETABLISSEMENTS ==="

curl "$BASE/etablissements/"

curl -X POST "$BASE/etablissements/" \
  -H "Content-Type: application/json" \
  -d '{
        "nom": "Lycee Ibn Sina",
        "ville": "Tiznit"
      }'

curl "$BASE/etablissements/1"

curl -X PUT "$BASE/etablissements/1" \
  -H "Content-Type: application/json" \
  -d '{
        "nom": "Lycee Ibn Rochd",
        "ville": "Agadir"
      }'

curl -X DELETE "$BASE/etablissements/1"



echo "=== TEST SCOLARITE ==="

curl "$BASE/scolarite/"

curl -X POST "$BASE/scolarite/" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "id_etablissement": 1,
        "annee_scolaire": "2023-2024",
        "niveau": "Terminale"
      }'

curl "$BASE/scolarite/1"

curl -X PUT "$BASE/scolarite/1" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "id_etablissement": 1,
        "annee_scolaire": "2024-2025",
        "niveau": "Bac+1"
      }'

curl -X DELETE "$BASE/scolarite/1"



echo "=== TEST CORRESPONDANTS ==="

curl "$BASE/correspondants/"

curl -X POST "$BASE/correspondants/" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "nom": "Fatima",
        "prenom": "El Khadiri",
        "telephone": "0601234567"
      }'

curl "$BASE/correspondants/1"

curl -X PUT "$BASE/correspondants/1" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "nom": "Fatima",
        "prenom": "El K.",
        "telephone": "0709876543"
      }'

curl -X DELETE "$BASE/correspondants/1"



echo "=== TEST TYPES DOCUMENTS ==="

curl "$BASE/typesdocuments/"

curl -X POST "$BASE/typesdocuments/" \
  -H "Content-Type: application/json" \
  -d '{
        "libelle": "Bulletin",
        "description": "Bulletin scolaire"
      }'

curl "$BASE/typesdocuments/1"

curl -X PUT "$BASE/typesdocuments/1" \
  -H "Content-Type: application/json" \
  -d '{
        "libelle": "Diplome",
        "description": "Diplome final"
      }'

curl -X DELETE "$BASE/typesdocuments/1"



echo "=== TEST DOCUMENTS ==="

curl "$BASE/documents/"

curl -X POST "$BASE/documents/" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "id_type": 1,
        "titre": "Bulletin 2023"
      }'

curl "$BASE/documents/1"

curl -X PUT "$BASE/documents/1" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "id_type": 1,
        "titre": "Bulletin 2023 - mis à jour"
      }'

curl -X DELETE "$BASE/documents/1"



echo "=== TEST SUIVI SOCIAL ==="

curl "$BASE/suivisocial/"

curl -X POST "$BASE/suivisocial/" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "commentaire": "Visite effectuée",
        "besoins": "Fournitures"
      }'

curl "$BASE/suivisocial/1"

curl -X PUT "$BASE/suivisocial/1" \
  -H "Content-Type: application/json" \
  -d '{
        "id_filleule": 1,
        "commentaire": "Mise à jour du suivi",
        "besoins": "Aucun"
      }'

curl -X DELETE "$BASE/suivisocial/1"
