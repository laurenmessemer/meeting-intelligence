-- One-time database correction: Fix client names containing "MTCA CRM" to "MTCA"
-- Affects ONLY the meetings table
-- Idempotent: Safe to run multiple times (only affects rows still containing "MTCA CRM")

-- PREVIEW: Uncomment the line below to see affected rows BEFORE running the update
-- SELECT id, client_name, meeting_date FROM meetings WHERE client_name ILIKE '%MTCA CRM%' ORDER BY meeting_date DESC;

-- UPDATE: Fix client names containing "MTCA CRM" to "MTCA"
UPDATE meetings
SET client_name = 'MTCA'
WHERE client_name ILIKE '%MTCA CRM%';

-- VERIFICATION: Uncomment the line below to verify the update
-- SELECT id, client_name, meeting_date FROM meetings WHERE client_name = 'MTCA' ORDER BY meeting_date DESC;


