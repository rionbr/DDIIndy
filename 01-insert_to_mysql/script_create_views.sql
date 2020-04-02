/*
 * Author: Rion B. Correia
 * Date: April 02, 2020
 * Description: Create Views
*/

/*
 * DW - Co-Administration (view)
*/
CREATE VIEW dw_coadministrations AS
SELECT
	di.id_drug AS 'id_i',
	dj.id_drug AS 'id_j',
	di.name AS 'i',
	dj.name AS 'j',
	pi.id_patient AS 'id_patient',
	c.length,
	c.is_ddi
FROM coadministration c
	/* drug i */
	JOIN medication_drug AS mdi ON c.id_medication_drug_i = mdi.id_medication_drug
	JOIN medication AS mi ON mdi.id_medication = mi.id_medication
	JOIN drug AS di ON mdi.id_drug = di.id_drug
	JOIN patient AS pi ON mi.id_patient = pi.id_patient
	/* drug j */
	JOIN medication_drug AS mdj ON c.id_medication_drug_j = mdj.id_medication_drug
	JOIN medication AS mj ON mdj.id_medication = mj.id_medication
	JOIN drug AS dj ON mdj.id_drug = dj.id_drug
	JOIN patient AS pj ON mj.id_patient = pj.id_patient;


/*
 * DW - Interaction (view)
*/
CREATE VIEW dw_interactions AS
SELECT
	di.id_drug AS 'id_i',
	dj.id_drug AS 'id_j',
	di.name AS 'i',
	dj.name AS 'j',
	pi.id_patient AS 'id_patient',
	c.length,
FROM coadministration c
	/* drug i */
	JOIN medication_drug AS mdi ON c.id_medication_drug_i = mdi.id_medication_drug
	JOIN medication AS mi ON mdi.id_medication = mi.id_medication
	JOIN drug AS di ON mdi.id_drug = di.id_drug
	JOIN patient AS pi ON mi.id_patient = pi.id_patient
	/* drug j */
	JOIN medication_drug AS mdj ON c.id_medication_drug_j = mdj.id_medication_drug
	JOIN medication AS mj ON mdj.id_medication = mj.id_medication
	JOIN drug AS dj ON mdj.id_drug = dj.id_drug
	JOIN patient AS pj ON mj.id_patient = pj.id_patient
WHERE
	c.is_ddi = TRUE;
