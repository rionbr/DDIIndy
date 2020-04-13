/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create All Tables
*/


/*
 * Drop Views/Tables before creation
*/
DROP VIEW IF EXISTS dw_coadministrations;
DROP VIEW IF EXISTS dw_interactions;
/* */
DROP TABLE IF EXISTS coadministration;
DROP TABLE IF EXISTS medication_drug;
/* */
DROP TABLE IF EXISTS medication;
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS ndc;
DROP TABLE IF EXISTS drug;
/* */ 
DROP TABLE IF EXISTS drugbank_interaction;


/*
 * Patient
*/
CREATE TABLE patient (
	id_patient INT PRIMARY KEY,
	gender VARCHAR(7) COMMENT "Male; Female",
	dob DATE,
	age_today INT(3) GENERATED ALWAYS AS (TIMESTAMPDIFF(YEAR, dob, '2020-01-01')) VIRTUAL,
	ethnicity VARCHAR(50) COMMENT "Not Hispanic/Latino; Not Hispanic/Latino/Spanish; Hispanic/Latino; Unknown",
	race VARCHAR(25) COMMENT "White; Black; Hispanic; Asian; Indian; Islander; Bi-racial; Unknown",
	zip5 INT(5) COMMENT "First 5 ZIP numbers",
	zip4 INT(4) COMMENT "Last 4 ZIP numbers"
) ENGINE=InnoDB;


/*
 * NDC
*/
CREATE TABLE ndc (
	id_catalog BIGINT COMMENT "CATALOGCVCD",
	ndc VARCHAR(50) COMMENT "NDC",
	UNIQUE KEY(id_catalog, ndc)
) ENGINE=InnoDB;


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
 * Drug
*/
CREATE TABLE drug (
	id_drug VARCHAR(7) PRIMARY KEY,
	name TEXT,
	type VARCHAR(100),
	class VARCHAR(100),
	subclass VARCHAR(100),
	description TEXT,
	groups VARCHAR(200)
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


/*
 * Co-Administration
*/
CREATE TABLE coadministration (
	id_patient INT NOT NULL,
	id_drug_i VARCHAR(7) NOT NULL,
	id_drug_j VARCHAR(7) NOT NULL,
	qt_i INT(4) UNSIGNED COMMENT "in days",
	qt_j INT(4) UNSIGNED COMMENT "in days",
	len_i INT(4) UNSIGNED COMMENT "in days",
	len_j INT(4) UNSIGNED COMMENT "in days",
	len_ij INT(4) UNSIGNED COMMENT "in days",
	is_ddi BOOLEAN DEFAULT FALSE,
	PRIMARY KEY (id_patient, id_drug_i, id_drug_j),
) ENGINE=InnoDB;


/*
 * DrugBank Interactions
*/
CREATE TABLE drugbank_interaction (
	id_drug_i VARCHAR(7),
	id_drug_j VARCHAR(7),
	description TEXT,
	severity VARCHAR(15),
	PRIMARY KEY (id_drug_i, id_drug_j),
	INDEX (id_drug_i),
	INDEX (id_drug_j)
) ENGINE=InnoDB;
