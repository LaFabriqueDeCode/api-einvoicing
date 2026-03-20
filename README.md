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

-- TEST de l'API mock de Doxallia

curl -X POST http://sebastien.ferrandez.free.fr/freepro/doxallia.php \
  -F "flowInfo[trackingId]=123" \
  -F "flowInfo[name]=seb.pdf"

curl -X POST http://sebastien.ferrandez.free.fr/freepro/doxallia.php \
  -F "flowInfo[trackingId]=123" \
  -F "flowInfo[name]=seb.pdf" \
  -F "flowInfo[processingRule]=B2B" \
  -F "flowInfo[flowSyntax]=Factur-X" \
  -F "File=@PDF/seb.pdf"  

-- CAS DE TEST

Je peux soumettre une facture dans un batch et la resoumettre à l'unité sous le meme nom -> correspond à un UC ?
Si je soumets deux fois la meme requete batch, j'ai bien un message d'err
Par contre si j'envoie 2 fois la même facture, ça passe. Est-ce que c'est normal ?

-- COMMANDES

cd ~/Development/api-einvoicing && poetry run uvicorn einvoicing.api.main:app --reload
cd ~/Development/api-einvoicing && poetry run python scripts/run_consumer.py
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

psql postgres
psql "postgresql://einvoicing_user:secret@localhost:5432/einvoicing"
TRUNCATE TABLE invoice_history, invoices, invoice_batches RESTART IDENTITY;

plus utilisé :
  poetry run python kafka/scripts/scan_pdf_directory.py PDF --provider doxallia --batch-type XPR --batch-id 20260601000000

cd ~/Development/api-einvoicing && find . -type d -name "__pycache__" -exec rm -rf {} + && find . -type f -name "*.pyc" -delete

cd ~/Development/api-einvoicing && docker-compose -f compose/docker-compose-kafka.yml down && docker-compose -f compose/docker-compose-kafka.yml up -d

