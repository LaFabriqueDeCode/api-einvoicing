CREATE DATABASE einvoicing;

CREATE TABLE invoice_provider_statuses (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    code INTEGER NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    is_terminal BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (provider, code)
);

CREATE TABLE invoice_app_statuses (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    description TEXT
);

INSERT INTO invoice_app_statuses (code, label, description) VALUES
('OK', 'Succès', 'Statut considéré comme valide ou réussi dans le SI'),
('ERROR', 'Erreur', 'Statut considéré comme une erreur dans le SI'),
('PENDING', 'En attente', 'Statut intermédiaire ou en attente de traitement');

CREATE TABLE invoice_status_mappings (
    id BIGSERIAL PRIMARY KEY,
    provider_status_id BIGINT NOT NULL,
    app_status_id BIGINT NOT NULL,

    CONSTRAINT fk_invoice_status_mappings_provider_status
        FOREIGN KEY (provider_status_id)
        REFERENCES invoice_provider_statuses(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_invoice_status_mappings_app_status
        FOREIGN KEY (app_status_id)
        REFERENCES invoice_app_statuses(id),

    CONSTRAINT uq_invoice_status_mappings_provider_status
        UNIQUE (provider_status_id)
);

CREATE TABLE invoice_batches (
    id BIGSERIAL PRIMARY KEY,
    external_batch_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    batch_type TEXT NOT NULL,
    directory TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE invoices (
    id BIGSERIAL PRIMARY KEY,

    tracking_id TEXT NOT NULL,
    batch_id BIGINT NULL,
    provider TEXT NOT NULL,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,

    current_provider_status_id BIGINT NULL,
    current_app_status_id BIGINT NULL,
    submitted_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_invoices_batch
        FOREIGN KEY (batch_id)
        REFERENCES invoice_batches(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_invoices_current_provider_status
        FOREIGN KEY (current_provider_status_id)
        REFERENCES invoice_provider_statuses(id),

    CONSTRAINT fk_invoices_current_app_status
        FOREIGN KEY (current_app_status_id)
        REFERENCES invoice_app_statuses(id)
);

CREATE TABLE invoice_history (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    provider_status_id BIGINT NULL,
    app_status_id BIGINT NULL,
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_invoice_history_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_invoice_history_provider_status
        FOREIGN KEY (provider_status_id)
        REFERENCES invoice_provider_statuses(id),

    CONSTRAINT fk_invoice_history_app_status
        FOREIGN KEY (app_status_id)
        REFERENCES invoice_app_statuses(id)
);

CREATE UNIQUE INDEX uniq_invoices_batch_tracking
    ON invoices (provider, batch_id, tracking_id)
    WHERE batch_id IS NOT NULL;

CREATE INDEX idx_invoices_tracking_id
    ON invoices(tracking_id);

CREATE INDEX idx_invoices_batch_id
    ON invoices(batch_id);

CREATE INDEX idx_invoices_provider
    ON invoices(provider);

CREATE INDEX idx_invoices_current_provider_status_id
    ON invoices(current_provider_status_id);

CREATE INDEX idx_invoices_current_app_status_id
    ON invoices(current_app_status_id);

CREATE INDEX idx_invoices_created_at
    ON invoices(created_at);

CREATE INDEX idx_invoice_batches_created_at
    ON invoice_batches(created_at);

CREATE INDEX idx_invoice_history_invoice_id
    ON invoice_history(invoice_id);

CREATE INDEX idx_invoice_history_invoice_id_event_at
    ON invoice_history(invoice_id, event_at);

CREATE INDEX idx_invoice_history_provider_status_id
    ON invoice_history(provider_status_id);

CREATE INDEX idx_invoice_history_app_status_id
    ON invoice_history(app_status_id);

CREATE INDEX idx_invoice_history_event_at
    ON invoice_history(event_at);

CREATE INDEX idx_invoice_history_event_type
    ON invoice_history(event_type);

INSERT INTO invoice_provider_statuses (provider, code, status, reason, is_terminal) VALUES
('doxallia', 900, 'DEPOSEE_OD', 'Facture déposée après pré-contrôles réglementaires et/ou métiers OK', FALSE),
('doxallia', 913, 'REJETEE_OD', 'Facture rejetée lors des pré-contrôles réglementaires et/ou métiers KO ; la facture peut être réémise avec le même numéro', TRUE),
('doxallia', 908, 'SUSPENDUE_OD', 'Facture suspendue en attente de pièces jointes complémentaires', FALSE),
('doxallia', 909, 'COMPLETEE_OD', 'Transmission de pièces jointes pour compléter une facture suspendue', FALSE),
('doxallia', 200, 'DEPOSEE', 'Facture déposée après contrôles réglementaires OK', FALSE),
('doxallia', 213, 'REJETEE', 'Facture rejetée après contrôles réglementaires KO ; elle doit être annulée comptablement et ne peut pas être réémise avec le même numéro', TRUE),
('doxallia', 201, 'EMISE_PAR_LA_PLATEFORME', 'Facture transmise vers la plateforme de réception de l’acheteur', FALSE),
('doxallia', 202, 'RECUE_DE_LA_PLATEFORME', 'Facture reçue par la plateforme de l’acheteur', FALSE),
('doxallia', 203, 'MISE_A_DISPOSITION', 'Facture mise à disposition de l’acheteur', FALSE),
('doxallia', 212, 'ENCAISSEE', 'Facture encaissée', TRUE),
('doxallia', 209, 'COMPLETEE', 'Transmission d’un document ou d’une donnée complémentaire nécessaire au traitement de la facture', FALSE);

INSERT INTO invoice_status_mappings (provider_status_id, app_status_id)
SELECT ps.id, aps.id
FROM invoice_provider_statuses ps
JOIN invoice_app_statuses aps ON aps.code = 'OK'
WHERE ps.provider = 'doxallia'
  AND ps.code IN (900, 200, 201, 202, 203, 209, 212);

INSERT INTO invoice_status_mappings (provider_status_id, app_status_id)
SELECT ps.id, aps.id
FROM invoice_provider_statuses ps
JOIN invoice_app_statuses aps ON aps.code = 'ERROR'
WHERE ps.provider = 'doxallia'
  AND ps.code IN (213, 913);

INSERT INTO invoice_status_mappings (provider_status_id, app_status_id)
SELECT ps.id, aps.id
FROM invoice_provider_statuses ps
JOIN invoice_app_statuses aps ON aps.code = 'PENDING'
WHERE ps.provider = 'doxallia'
  AND ps.code IN (908, 909);