Depuis un batch, XPR ou PRO :

curl -X POST http://127.0.0.1:8000/api-einvoicing/v1/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "doxallia",
    "batch_id": "2026030207",
    "batch_type": "XPR",
    "files": [
      {
        "path": "/Users/lafabriquedecode/Development/api-einvoicing/PDF/seb.pdf"
      },
      {
        "path": "/Users/lafabriquedecode/Development/api-einvoicing/PDF/seb2.pdf"
      }
    ]
  }'

Depuis intranet, en mode unitaire (une ou plusieurs factures)
curl -X POST http://127.0.0.1:8000/api-einvoicing/v1/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "doxallia",
    "files": [
      {
        "path": "/Users/lafabriquedecode/Development/api-einvoicing/PDF/seb.pdf"
      }
    ]
  }'

-- conf WS

$global_conf{'e-invoicing'} = {
	'url' => 'https://e-invoicing.api.as30781.net',
	'client_id' => 'ws.service',
	'client_secret' => 'mettrelememe',
};

--------------------------------------------------------------------------------
-- TEST de l'API mock de Doxallia
--------------------------------------------------------------------------------

curl -X POST http://sebastien.ferrandez.free.fr/freepro/doxallia.php \
  -F "flowInfo[trackingId]=123" \
  -F "flowInfo[name]=seb.pdf"

curl -X POST http://sebastien.ferrandez.free.fr/freepro/doxallia.php \
  -F "flowInfo[trackingId]=123" \
  -F "flowInfo[name]=seb.pdf" \
  -F "flowInfo[processingRule]=B2B" \
  -F "flowInfo[flowSyntax]=Factur-X" \
  -F "File=@PDF/seb.pdf"  

--------------------------------------------------------------------------------
-- FAIT
--------------------------------------------------------------------------------

J'ai mocké le retour de l'API Doxallia 
J'ai créé un endpoint capable de traiter des factures en batch/hors-batch
J'ai créé un topic Kafka avec un producteur et un consommateur
J'ai un composant qui fait des requêtes HTTP avec de l'Auth (à tester)
J'ai des repositories qui créent des enregistrements en base
Je crée des factures, potentiellement rattachées à des batches et avec une history

--------------------------------------------------------------------------------
-- QUESTIONS
--------------------------------------------------------------------------------

Airflow et le run XPR devraient appeler le script submit.py mais sur 80000 factures, quelle est la durée ?

--------------------------------------------------------------------------------
-- CAS DE TEST
--------------------------------------------------------------------------------

Je peux soumettre une facture dans un batch et la resoumettre à l'unité sous le meme nom -> correspond à un UC ?
Si je soumets deux fois la meme requete batch, j'ai bien un message d'err
Par contre si j'envoie 2 fois la même facture, ça passe. Est-ce que c'est normal ?

Que se passe-t-il si on tente de soumettre une facture qui existe en base dans un statut terminal ?

--------------------------------------------------------------------------------
-- COMMANDES
--------------------------------------------------------------------------------

cd ~/Development/api-einvoicing && poetry run uvicorn einvoicing.api.main:app --reload
cd ~/Development/api-einvoicing && poetry run python cmd/consumer.py
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

psql postgres
psql "postgresql://einvoicing_user:secret@localhost:5432/einvoicing"
TRUNCATE TABLE invoice_history, invoices, invoice_batches RESTART IDENTITY;

cd ~/Development/api-einvoicing && find . -type d -name "__pycache__" -exec rm -rf {} + && find . -type f -name "*.pyc" -delete

cd ~/Development/api-einvoicing && docker-compose -f compose/docker-compose-kafka.yml down && docker-compose -f compose/docker-compose-kafka.yml up -d

DEPRECATED :
  poetry run python kafka/scripts/scan_pdf_directory.py PDF --provider doxallia --batch-type XPR --batch-id 20260601000000

--------------------------------------------------------------------------------
-- POLLING
--------------------------------------------------------------------------------
CDAR Worker
  workers/cdar_polling_worker.py
CdarStatusSyncService
  récupérer les invoices à surveiller (non terminales)
  appeler le provider CDAR
  déclencher le parsing
  mapper les statuts
  persister les résultats
CdarClient
CDAR Parser
  renvoie list[CdarStatusEvent]
Status Mapper service 

CDAR Worker
    ↓
CdarStatusSyncService
    ↓
CdarClient (HTTP)
    ↓
CDAR Parser
    ↓
Status Mapper
    ↓
InvoiceHistoryRepository
    ↓
InvoiceRepository

1. Idempotence
ne pas créer plusieurs fois le même event
vérifier les doublons éventuels
2. Statuts terminaux
ne plus poller une invoice terminée
ex : REJETEE, ENCAISSEE

Si tu veux, l’étape suivante est de mettre aussi global_request_id et provider_request_id dans invoice_history.details ou dans des colonnes dédiées.