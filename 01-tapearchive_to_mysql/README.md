# DDI Indy - Data Management

This file traces commands used to create and give permission and handle the raw data.
This file will provide little information to users without the necessary permissions to the Indiana University UITS systems.


## MySQL Enterprise information


Project schema: `casci_ddi_indy`.


### Create Tables


```
CREATE TABLE patient (
	id_patient INT PRIMARY KEY,
	gender VARCHAR(6) COMMENT "Male; Female",
	dob DATE,
	age_today INT(3) GENERATED ALWAYS AS (TIMESTAMPDIFF(YEAR, dob, '2020-01-01')) VIRTUAL,
	ethnicity VARCHAR(25) COMMENT "Not Hispanic or Latino; Not Hispanic, Latino/a, or Spanish Origin; Unkonwn",
	race VARCHAR(25) COMMENT "White; Black; Hispanic; Asian; Indian; Islander; >1 race; Unknown",
	zip5 INT(5) COMMENT "First 5 ZIP numbers",
	zip4 INT(4) COMMENT "Last 4 ZIP numbers"
) ENGINE=InnoDB;
```

```
CREATE TABLE ndc (
	id_catalog BIGINT PRIMARY KEY COMMENT "CATALOGCVCD",
	ndc BIGINT COMMENT "NDC"
) ENGINE=InnoDB;
```

```
CREATE TABLE medication (
	id_medication INT PRIMARY KEY AUTO_INCREMENT,
	id_drugbank VARCHAR(7),
	id_patient INT NOT NULL,
	id_catalog BIGINT COMMENT "CATALOGCVCD",
	gpi BIGINT COMMENT "GPI",
	dt_order DATE NOT NULL,
	status VARCHAR(15) COMMENT "Sent; Ordered; Completed; Discontinued",
	name TEXT,
	dose_strength FLOAT(10,2),
	dose_strength_unit VARCHAR(15),
	qt_dispensed FLOAT(10,2),
	qt_dispensed_unit VARCHAR(15),
	qt_refill FLOAT(10,2) COMMENT "REFILLQTY",
	nr_refill INT(2) COMMENT "NBRREFILLS",
	duration INT(3),
	duration_unit VARCHAR(15),
	is_topic BOOLEAN DEFAULT FALSE,
	is_ophthalmo BOOLEAN DEFAULT FALSE,
	is_vaccine BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB;

ALTER TABLE medication
	ADD CONSTRAINT fk_id_patient FOREIGN KEY (id_patient)
	REFERENCES patient (id_patient)
	ON UPDATE CASCADE ON DELETE RESTRICT;
	
ALTER TABLE medication
	ADD CONSTRAINT fk_id_catalog FOREIGN KEy (id_catalog)
	REFERENCES ndc (id_catalog)
	ON UPDATE CASCADE ON DELETE RESTRICT;
```


### Drop Tables

```
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS medication;
DROP TABLE IF EXISTS ndc;
```


### MySQL Management


Show help on creating schemas and users:

```
CALL api.help('me');
```

Code used to create the 'ddi_indy' MySQL schemas and the `rionbr` user.

```
CALL api.createSchema('ddi_indy');
CALL api.createUser('rionbr', '%', '<password>', false, false);
CALL api.grant('casci_rionbr', '%', 'ALL PRIVILEGES', 'casci_ddi_indy', '*');
```


## Raw data access information

Raw data is stored at IU's Scholarly Data Archive (SDA).
To access it you need to login in to an IU's supercomputer, i.e. Carbonate.

`> ssh carbonate.uits.iu.edu`

Then you need to load the `hpss` module to be able to access the SDA.

`> module load hpss`

Then you can enter the `hsi` module to access the data and navigate to the files location.

```
> hsi
> Kerberos Principal: <username>
> cd /hpss/c/a/casci/ddiindy
> get
```

The following files are part of the raw data

```
     size filename
105935521 p2876_demographics.csv
 34118970 p2876_meds_01_t.csv
 59543922 p2876_meds_01_u.csv
 31783367 p2876_meds_02_t.csv
 59695353 p2876_meds_02_u.csv
 32735246 p2876_meds_03_t.csv
 57181584 p2876_meds_03_u.csv
 32526927 p2876_meds_04_t.csv
 54424638 p2876_meds_04_u.csv
 33106270 p2876_meds_05_t.csv
 54732334 p2876_meds_05_u.csv
 31400220 p2876_meds_06_t.csv
 54325254 p2876_meds_06_u.csv
 33560108 p2876_meds_07_t.csv
 57880374 p2876_meds_07_u.csv
 32354787 p2876_meds_08_t.csv
 55122996 p2876_meds_08_u.csv
 33349672 p2876_meds_09_t.csv
 54049346 p2876_meds_09_u.csv
 34286775 p2876_meds_10_t.csv
 55274803 p2876_meds_10_u.csv
 33235309 p2876_meds_11_t.csv
 57319335 p2876_meds_11_u.csv
 32352764 p2876_meds_12_t.csv
 56510580 p2876_meds_12_u.csv
   679458 p2876_ndc.csv
```
