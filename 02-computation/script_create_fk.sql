/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Foreign Keys on coadministration table
*/


/*
 * CoAdministration
*/
ALTER TABLE coadministration
	ADD CONSTRAINT fk_id_patient FOREIGN KEY (id_patient)
	REFERENCES patient (id_patient)
	ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE coadministration
	ADD CONSTRAINT fk_id_drug_i FOREIGN KEY (id_drug_i)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE coadministration
	ADD CONSTRAINT fk_id_drug_j FOREIGN KEY (id_drug_j)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;

/*
 * Drop FKs 
*/
/*
ALTER TABLE coadministration DROP FOREIGN KEY `fk_id_patient`;
ALTER TABLE coadministration DROP FOREIGN KEY `fk_id_drug_i`;
ALTER TABLE coadministration DROP FOREIGN KEY `fk_id_drug_j`;

/*
 * Discover where is the problem
*/
/*

*/
