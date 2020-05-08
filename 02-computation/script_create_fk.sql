/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Foreign Keys on coadministration table
*/


/*
 * CoAdministration
*/
ALTER TABLE coadministration
	ADD CONSTRAINT fk_coadmin_id_patient FOREIGN KEY (id_patient)
	REFERENCES patient (id_patient)
	ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE coadministration
	ADD CONSTRAINT fk_coadmin_id_drug_i FOREIGN KEY (id_drug_i)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE coadministration
	ADD CONSTRAINT fk_coadmin_id_drug_j FOREIGN KEY (id_drug_j)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;

/*
 * Drop FKs 
*/
/*
SHOW INDEX FROM coadministration;


SELECT 
  TABLE_NAME,COLUMN_NAME,CONSTRAINT_NAME, REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME
FROM
  INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE
  TABLE_SCHEMA = 'casci_ddi_indy'
  REFERENCED_TABLE_SCHEMA = 'casci_ddi_indy' AND
  REFERENCED_TABLE_NAME = 'coadministration';


ALTER TABLE coadministration DROP FOREIGN KEY `fk_coadmin_id_patient`;
ALTER TABLE coadministration DROP FOREIGN KEY `fk_id_drug_i`;
ALTER TABLE coadministration DROP FOREIGN KEY `fk_id_drug_j`;

/*
 * Discover where is the problem
*/
/*

*/