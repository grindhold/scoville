CREATE DATABASE 'skdrepo.fdb' DEFAULT CHARACTER SET UTF8;

CREATE GENERATOR DEP_GEN;
CREATE GENERATOR DEV_GEN;
CREATE GENERATOR MOD_GEN;
CREATE GENERATOR TMP_GEN;

CREATE TABLE CONFIG
(
  PARAM Varchar(32) NOT NULL,
  VAL Varchar(1024) NOT NULL,
  CONSTRAINT CONF_PK PRIMARY KEY (PARAM)
);
CREATE TABLE DEPENDENCIES
(
  DEP_ID Integer NOT NULL,
  DEP_MOD_ID Integer NOT NULL,
  DEP_MOD_DEPENDSON Integer NOT NULL,
  CONSTRAINT DEP_PK PRIMARY KEY (DEP_ID)
);
CREATE TABLE DEVELOPER
(
  DEV_ID Integer NOT NULL,
  DEV_NAME Varchar(128) NOT NULL,
  DEV_FULLNAME Varchar(1024),
  DEV_PUBLICKEY Varchar(1024),
  CONSTRAINT DEV_PK PRIMARY KEY (DEV_ID),
  CONSTRAINT DEV_UNIQUE_NAME UNIQUE (DEV_NAME)
);
CREATE TABLE MODULES
(
  MOD_ID Integer NOT NULL,
  MOD_NAME Varchar(64) NOT NULL,
  MOD_DISPLAYNAME Varchar(64) NOT NULL,
  MOD_VERSIONMAJOR Integer NOT NULL,
  MOD_VERSIONMINOR Integer NOT NULL,
  MOD_VERSIONREV Integer NOT NULL,
  MOD_SIGNATURE Varchar(172) NOT NULL,
  MOD_DATA Blob sub_type 1 NOT NULL,
  MOD_JSMANDATORY INT DEFAULT 0 NOT NULL,
  CONSTRAINT MOD_PK PRIMARY KEY (MOD_ID)
);
CREATE TABLE SESSIONS
(
  SES_ID Varchar(64) NOT NULL,
  SES_EXPIRES Timestamp NOT NULL,
  SES_IS_ADMIN Integer NOT NULL,
  CONSTRAINT SES_PK PRIMARY KEY (SES_ID)
);
CREATE TABLE TEMPLATES
(
  TMP_ID Integer NOT NULL,
  TMP_NAME Varchar(255) NOT NULL,
  TMP_DESCRIPTION Varchar(2048) NOT NULL,
  TMP_AUTHOR Varchar(1024) NOT NULL,
  TMP_SIGNATURE Varchar(172) NOT NULL,
  TMP_DATA Blob sub_type 1 NOT NULL,
  CONSTRAINT TMP_PK PRIMARY KEY (TMP_ID)
);

COMMIT;

INSERT INTO CONFIG (PARAM,VAL) VALUES ('password','729ee5ddf67f15e4e33a790004a257750ae7433ecedb78d34e76dc3a766f2af2672fa8f8423301aa945ab761817e6a2249c4312de8af2c6934fe9599fb2f0a8b');
INSERT INTO CONFIG (PARAM,VAL) VALUES ('salt','Z7mbp09lOrH2Mb+pURrzzkJX77TJ2Rc2pg4MoJu2EZr6aZeqO4x7utdaQisCdKSkUlHPCCSj/fHZsGjS18RuhYSx7ZYqQ5pvxrmYjwx7VYyvY4dBGIahn4l8Tb0G7d7ahyNIAGLrBFAY4ir8/XUEBIAcooa1o2mdAx3PEwW2knN/8BsRYjUDbReDwx+ptjkYULrWe3fi3qi7+XXCtfYNgEouLzvN8FWhUu+V4CR1abKTq3sicwsoAbXhcD6A4knB8zqhMZzq8CrZSIP9HRQLYw5Wh8Lv1jCob5/vACG/k9VFzxP3ZinEhppVslAoEQo=');

ALTER TABLE DEPENDENCIES ADD CONSTRAINT DEP_FK_MOD
  FOREIGN KEY (DEP_MOD_ID) REFERENCES MODULES (MOD_ID) ON UPDATE CASCADE ON DELETE CASCADE;
GRANT DELETE, INSERT, REFERENCES, SELECT, UPDATE
 ON CONFIG TO SKDREPO WITH GRANT OPTION;

GRANT DELETE, INSERT, REFERENCES, SELECT, UPDATE
 ON DEPENDENCIES TO SKDREPO WITH GRANT OPTION;

GRANT DELETE, INSERT, REFERENCES, SELECT, UPDATE
 ON DEVELOPER TO SKDREPO WITH GRANT OPTION;

GRANT DELETE, INSERT, REFERENCES, SELECT, UPDATE
 ON MODULES TO SKDREPO WITH GRANT OPTION;

GRANT DELETE, INSERT, REFERENCES, SELECT, UPDATE
 ON SESSIONS TO SKDREPO WITH GRANT OPTION;

GRANT DELETE, INSERT, REFERENCES, SELECT, UPDATE
 ON TEMPLATES TO SKDREPO WITH GRANT OPTION;
