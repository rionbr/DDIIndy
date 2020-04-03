/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Foreign Keys
*/

/*
 * Medication
*/
ALTER TABLE medication
	ADD CONSTRAINT fk_id_patient FOREIGN KEY (id_patient)
	REFERENCES patient (id_patient)
	ON UPDATE CASCADE ON DELETE CASCADE;
	
ALTER TABLE medication
	ADD CONSTRAINT fk_id_catalog FOREIGN KEy (id_catalog)
	REFERENCES ndc (id_catalog)
	ON UPDATE CASCADE ON DELETE CASCADE;


/*
 * Medication <-> Drug
*/
ALTER TABLE medication_drug
	ADD CONSTRAINT fk_id_medication FOREIGN KEY (id_medication)
	REFERENCES medication (id_medication)
	ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE medication_drug
	ADD CONSTRAINT fk_id_drug FOREIGN KEY (id_drug)
	REFERENCES drug (id_drug)
	ON UPDATE CASCADE ON DELETE RESTRICT;


/*
 * CoAdministration
*/
ALTER TABLE coadministration
	ADD CONSTRAINT fk_id_medication_drug_i FOREIGN KEY (id_medication_drug_i)
	REFERENCES medication_drug (id_medication_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE coadministration
	ADD CONSTRAINT fk_id_medication_drug_j FOREIGN KEY (id_medication_drug_j)
	REFERENCES medication_drug (id_medication_drug)
	ON UPDATE CASCADE ON DELETE CASCADE;
