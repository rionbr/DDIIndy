/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Medication tables
*/


/*
 * Drop Views/Tables before creation
*/
DROP TABLE IF EXISTS medication_drug;
DROP TABLE IF EXISTS medication;


/*
 * Medication
*/
CREATE TABLE medication (
	id_medication INT PRIMARY KEY,
	id_patient INT NOT NULL,
	id_catalog BIGINT COMMENT "CATALOGCVCD",
	dt_start DATETIME NOT NULL COMMENT "ORDERING_DATE",
	dt_end DATETIME NOT NULL COMMENT "ORDERING_DATE + DURATION",
	status VARCHAR(15) COMMENT "Sent; Ordered; Completed; Discontinued",
	name TEXT,
	dose_strength FLOAT(14,2),
	dose_strength_unit VARCHAR(25),
	qt_dispensed FLOAT(14,2),
	qt_dispensed_unit VARCHAR(25),
	qt_refill FLOAT(14,2) COMMENT "REFILLQTY",
	nr_refill INT(2) COMMENT "NBRREFILLS",
	duration INT(3),
	duration_unit VARCHAR(15),
	is_topic BOOLEAN DEFAULT FALSE,
	is_ophthalmo BOOLEAN DEFAULT FALSE,
	is_vaccine BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB;


/*
 * Medication <-> Drug
*/
CREATE TABLE medication_drug (
	id_medication_drug INT PRIMARY KEY AUTO_INCREMENT,
	id_medication INT NOT NULL,
	id_drug VARCHAR(7) NOT NULL,
	UNIQUE KEY(id_medication, id_drug)
) ENGINE=InnoDB;
