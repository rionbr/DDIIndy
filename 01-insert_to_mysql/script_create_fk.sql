/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Foreign Keys
*/

/*
 * Medication
*/
ALTER TABLE medication
	ADD CONSTRAINT fk_medication_id_patient FOREIGN KEY (id_patient)
	REFERENCES patient (id_patient)
	ON UPDATE CASCADE ON DELETE CASCADE;
	
ALTER TABLE medication
	ADD CONSTRAINT fk_medication_id_catalog FOREIGN KEy (id_catalog)
	REFERENCES ndc (id_catalog)
	ON UPDATE CASCADE ON DELETE CASCADE;


/*
 * Medication <-> Drug
*/
ALTER TABLE medication_drug
	ADD CONSTRAINT fk_medication_drug_id_medication FOREIGN KEY (id_medication)
	REFERENCES medication (id_medication)
	ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE medication_drug
	ADD CONSTRAINT fk_medication_drug_id_drug FOREIGN KEY (id_drug)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE RESTRICT;


/*
 * DrugBank Interaction
*/
ALTER TABLE drugbank_interaction
	ADD CONSTRAINT fk_db_interaction_id_drug_i FOREIGN KEY (id_drug_i)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE drugbank_interaction
	ADD CONSTRAINT fk_db_interaction_id_drug_j FOREIGN KEY (id_drug_j)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;

/*
 * Select FKs 
*/
/*
SELECT 
  TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM
  INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE
  REFERENCED_TABLE_SCHEMA = 'casci_ddi_indy' AND
  TABLE_NAME = 'medication_drug';
*/

/*
 * Drop FKs 
*/
/*
ALTER TABLE medication DROP FOREIGN KEY `fk_medication_id_patient`;
ALTER TABLE medication DROP FOREIGN KEY `fk_medication_id_catalog`;

ALTER TABLE medication_drug DROP FOREIGN KEY `fk_medication_drug_id_medication`;
ALTER TABLE medication_drug DROP FOREIGN KEY `fk_medication_drug_id_drug`;

ALTER TABLE drugbank_interaction DROP FOREIGN KEY `fk_db_interaction_id_drug_i`;
ALTER TABLE drugbank_interaction DROP FOREIGN KEY `fk_db_interaction_id_drug_j`;

/*
 * Discover where is the problem
*/
/*
SELECT * FROM medication_drug WHERE id_drug NOT IN (SELECT DISTINCT id_drug FROM drug) LIMIT 1;

SELECT id_drug, name FROM drug WHERE id_drug = 'DB01402';
SELECT id_drug, name FROM drug WHERE name LIKE '%aliskiren%';

UPDATE medication_drug SET id_drug = 'DB01258' WHERE id_drug = 'DB09026';
DELETE FROM medication_drug WHERE id_drug = 'DB14487';
*/

SELECT * FROM drugbank_interaction WHERE id_drug_i NOT IN (SELECT id_drug FROM drug)