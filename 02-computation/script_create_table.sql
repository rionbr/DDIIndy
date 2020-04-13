/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create CoAdministation Table
*/

/*
 * Drop Views/Tables before creation
*/
DROP TABLE IF EXISTS coadministration;


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
	PRIMARY KEY (id_patient, id_drug_i, id_drug_j)
) ENGINE=InnoDB;