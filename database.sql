-- Connect to the database
-- \c einvoicing

-- Drop tables in reverse order of creation (due to foreign key dependencies)
DROP TABLE IF EXISTS invoice_history          CASCADE;
DROP TABLE IF EXISTS invoices                 CASCADE;
DROP TABLE IF EXISTS invoice_batches          CASCADE;
DROP TABLE IF EXISTS invoice_status_mappings  CASCADE;
DROP TABLE IF EXISTS invoice_provider_statuses CASCADE;
DROP TABLE IF EXISTS invoice_app_statuses      CASCADE;

-- ==============================
-- Table: invoice_app_statuses
-- ==============================
CREATE TABLE invoice_app_statuses (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    description TEXT
);

-- ==============================
-- Table: invoice_provider_statuses
-- ==============================
CREATE TABLE invoice_provider_statuses (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    code INTEGER NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    is_terminal BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (provider, code)
);

-- ==============================
-- Table: invoice_status_mappings
-- ==============================
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

-- ==============================
-- Table: invoice_batches
-- ==============================
CREATE TABLE invoice_batches (
    id BIGSERIAL PRIMARY KEY,
    external_batch_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    batch_type TEXT NOT NULL,
    directory TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================
-- Table: invoices
-- ==============================
CREATE TABLE invoices (
    id BIGSERIAL PRIMARY KEY,
    tracking_id TEXT NOT NULL,
    batch_id BIGINT NULL,
    provider TEXT NOT NULL,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    current_provider_status_id BIGINT NULL, -- Will be updated upon receipt of lifecycle information
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

-- ==============================
-- Table: invoice_history
-- ==============================
CREATE TABLE invoice_history (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    provider_status_id BIGINT NULL,
    app_status_id BIGINT NULL,
    global_request_id TEXT NULL,
    provider_request_id TEXT NULL,
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

-- ==============================
-- Indexes
-- ==============================

-- Indexes on invoice_history
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

CREATE INDEX idx_invoice_history_global_request_id
ON invoice_history(global_request_id);

CREATE INDEX idx_invoice_history_provider_request_id
ON invoice_history(provider_request_id);

CREATE INDEX idx_invoice_history_invoice_id_global_request_id
ON invoice_history(invoice_id, global_request_id);

CREATE UNIQUE INDEX uniq_invoice_history_provider_request_id
ON invoice_history(provider_request_id)
WHERE provider_request_id IS NOT NULL;

-- Indexes on invoices
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

-- Index on invoice_batches
CREATE INDEX idx_invoice_batches_created_at
ON invoice_batches(created_at);

-- ==============================
-- Initial Data
-- ==============================

-- Insert application statuses
INSERT INTO invoice_app_statuses (code, label, description) VALUES
('OK', 'Succès', 'Statut considéré comme valide ou réussi dans le SI'),
('ERROR', 'Erreur', 'Statut considéré comme une erreur dans le SI'),
('PENDING', 'En attente', 'Statut intermédiaire ou en attente de traitement');

-- Insert provider statuses for Doxallia
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

-- Insert status mappings
-- OK: active or successful states
INSERT INTO invoice_status_mappings (provider_status_id, app_status_id)
SELECT ps.id, aps.id
FROM invoice_provider_statuses ps
JOIN invoice_app_statuses aps ON aps.code = 'OK'
WHERE ps.provider = 'doxallia'
AND ps.code IN (900, 200, 201, 202, 203, 209, 212);

-- ERROR: rejected or failed states
INSERT INTO invoice_status_mappings (provider_status_id, app_status_id)
SELECT ps.id, aps.id
FROM invoice_provider_statuses ps
JOIN invoice_app_statuses aps ON aps.code = 'ERROR'
WHERE ps.provider = 'doxallia'
AND ps.code IN (213, 913);

-- PENDING: intermediate or waiting states
INSERT INTO invoice_status_mappings (provider_status_id, app_status_id)
SELECT ps.id, aps.id
FROM invoice_provider_statuses ps
JOIN invoice_app_statuses aps ON aps.code = 'PENDING'
WHERE ps.provider = 'doxallia'
AND ps.code IN (908, 909);

-- ==============================
-- Column Comments (Documentation)
-- ==============================

-- invoice_provider_statuses
COMMENT ON COLUMN invoice_provider_statuses.provider IS 'Name of the e-invoicing provider (e.g., doxallia). Used to namespace status codes.';
COMMENT ON COLUMN invoice_provider_statuses.code IS 'Provider-specific numeric status code (e.g., 200, 900). Must be unique per provider.';
COMMENT ON COLUMN invoice_provider_statuses.status IS 'Official status label from the provider (e.g., DEPOSEE, REJETEE). Case-sensitive and business-critical.';
COMMENT ON COLUMN invoice_provider_statuses.reason IS 'Human-readable explanation of the status, including business or technical context. Used for user communication and debugging.';
COMMENT ON COLUMN invoice_provider_statuses.is_terminal IS 'True if this status is final and no further updates are expected. Terminal statuses stop the invoice workflow.';

-- invoice_app_statuses
COMMENT ON COLUMN invoice_app_statuses.code IS 'Internal normalized status code (e.g., OK, ERROR, PENDING). Used in business logic and integrations.';
COMMENT ON COLUMN invoice_app_statuses.label IS 'User-friendly label for display in UI or logs (e.g., "Succès", "Erreur").';
COMMENT ON COLUMN invoice_app_statuses.description IS 'Detailed explanation of the application-level status. Helps developers and support teams understand its meaning.';

-- invoice_status_mappings
COMMENT ON COLUMN invoice_status_mappings.provider_status_id IS 'References a provider-specific status in invoice_provider_statuses.';
COMMENT ON COLUMN invoice_status_mappings.app_status_id IS 'Maps to a normalized application status in invoice_app_statuses. Drives business logic and UI behavior.';

-- invoice_batches
COMMENT ON COLUMN invoice_batches.external_batch_id IS 'Provider-issued unique identifier for the batch (e.g., 2026030207). Used for tracking and reconciliation.';
COMMENT ON COLUMN invoice_batches.provider IS 'Name of the e-invoicing provider (e.g., doxallia).';
COMMENT ON COLUMN invoice_batches.batch_type IS 'Type of batch (e.g., XPR for Factur-X). Used to determine processing rules.';
COMMENT ON COLUMN invoice_batches.directory IS 'Filesystem path where invoice files of this batch are stored. Used for retrieval and audit.';
COMMENT ON COLUMN invoice_batches.created_at IS 'Timestamp when the batch was created in the system (UTC).';

-- invoices
COMMENT ON COLUMN invoices.tracking_id IS 'Unique tracking ID for the invoice within the provider system (e.g., seb). Must be unique per provider and batch.';
COMMENT ON COLUMN invoices.batch_id IS 'Reference to the batch this invoice belongs to. NULL if not part of a batch.';
COMMENT ON COLUMN invoices.provider IS 'Name of the e-invoicing provider handling this invoice (e.g., doxallia).';
COMMENT ON COLUMN invoices.name IS 'Original filename of the invoice (e.g., seb.pdf). Used for identification and logging.';
COMMENT ON COLUMN invoices.file_path IS 'Absolute filesystem path to the invoice document. Used for access and audit.';
COMMENT ON COLUMN invoices.current_provider_status_id IS 'Latest status received from the provider. NULL if no update has been received yet.';
COMMENT ON COLUMN invoices.current_app_status_id IS 'Latest normalized application status (e.g., OK, ERROR). Drives business logic and user experience.';
COMMENT ON COLUMN invoices.submitted_at IS 'Timestamp when the invoice was submitted to the provider (UTC).';
COMMENT ON COLUMN invoices.created_at IS 'Timestamp when the invoice record was created (UTC).';
COMMENT ON COLUMN invoices.updated_at IS 'Timestamp when the invoice record was last updated (UTC). Automatically refreshed on UPDATE.';

-- invoice_history
COMMENT ON COLUMN invoice_history.invoice_id IS 'Reference to the associated invoice. Cascades delete.';
COMMENT ON COLUMN invoice_history.provider_status_id IS 'Provider status at the time of this event. NULL if not applicable.';
COMMENT ON COLUMN invoice_history.app_status_id IS 'Mapped application status at the time of this event.';
COMMENT ON COLUMN invoice_history.global_request_id IS 'Correlation ID for end-to-end tracing of a batch or invoice operation (e.g., UUID). Shared across related events.';
COMMENT ON COLUMN invoice_history.provider_request_id IS 'Provider-issued request ID for this specific invoice (e.g., UUID). Used for provider-side tracking and support.';
COMMENT ON COLUMN invoice_history.source IS 'Origin of the event (e.g., doxallia, internal_system). Helps identify the source system or component.';
COMMENT ON COLUMN invoice_history.event_type IS 'Type of event recorded (e.g., PROVIDER_SUBMISSION_ACCEPTED, STATUS_UPDATE). Used for routing, alerts, and analysis.';
COMMENT ON COLUMN invoice_history.event_at IS 'Timestamp when the event occurred in the provider or system context (UTC). May differ from created_at.';
COMMENT ON COLUMN invoice_history.raw_payload IS 'Full JSON payload received from or sent to the provider. Used for debugging, auditing, and compliance.';
COMMENT ON COLUMN invoice_history.details IS 'Human-readable summary or error message for operational visibility. Not structured, for logging purposes.';
COMMENT ON COLUMN invoice_history.created_at IS 'Timestamp when the history record was inserted into the database (UTC).';