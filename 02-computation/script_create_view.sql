/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Views
*/

/*
 * DW - Co-Administration (view)
*/
CREATE VIEW dw_coadministration AS
SELECT
	p.id_patient,
	p.gender,
	p.dob,
	p.ethnicity,
	p.race,
	p.zip5,
	p.zip4,
	di.id_drug_i,
	dj.id_drug_j,
	di.name AS 'name_i',
	dj.name AS 'name_j',
	c.qt_i,
	c.qt_j,
	c.len_i,
	c.len_j,
	c.len_ij,
	c.is_ddi
FROM coadmin c
	JOIN drug AS di ON mdi.id_drug = di.id_drug
	JOIN drug AS dj ON mdj.id_drug = dj.id_drug
	JOIN patient AS pi ON mi.id_patient = pi.id_patient;


/*
 * DW - Interaction (view)
*/
CREATE VIEW dw_interaction AS
SELECT
	p.id_patient,
	p.gender,
	p.dob,
	p.ethnicity,
	p.race,
	p.zip5,
	p.zip4,
	di.id_drug_i,
	dj.id_drug_j,
	di.name AS 'name_i',
	dj.name AS 'name_j',
	c.qt_i,
	c.qt_j,
	c.len_i,
	c.len_j,
	c.len_ij,
	c.is_ddi
FROM coadmin c
	JOIN drug AS di ON mdi.id_drug = di.id_drug
	JOIN drug AS dj ON mdj.id_drug = dj.id_drug
	JOIN patient AS pi ON mi.id_patient = pi.id_patient;
WHERE
	c.is_ddi = TRUE;
