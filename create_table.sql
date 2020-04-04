CREATE TABLE IF NOT EXISTS Challenge
(
    challengeId INT(8) PRIMARY KEY,
    projectId INT(8),
    forumId INT(8),

    track VARCHAR(12), # one of (DEVELOP, DESIGN, DATA_SCIENCE)
    subTrack VARCHAR(30), # one of (DESIGN, DEVELOPMENT, SECURITY, PROCESS, TESTING_COMPETITION, SPECIFICATION, ARCHITECTURE, COMPONENT_PRODUCTION, BUG_HUNT, DEPLOYMENT, TEST_SUITES, ASSEMBLY_COMPETITION, UI_PROTOTYPE_COMPETITION, CONCEPTUALIZATION, RIA_BUILD_COMPETITION, RIA_COMPONENT_COMPETITION, TEST_SCENARIOS, SPEC_REVIEW, COPILOT_POSTING, CONTENT_CREATION, REPORTING, DEVELOP_MARATHON_MATCH, FIRST_2_FINISH, CODE, BANNERS_OR_ICONS, WEB_DESIGNS, WIREFRAMES, LOGO_DESIGN, PRINT_OR_PRESENTATION, WIDGET_OR_MOBILE_SCREEN_DESIGN, FRONT_END_FLASH, APPLICATION_FRONT_END_DESIGN, STUDIO_OTHER, IDEA_GENERATION, DESIGN_FIRST_2_FINISH, SRM, MARATHON_MATCH)

    challengeTitle VARCHAR(512),
    detailedRequirements TEXT,
    finalSubmissionGuidelines TEXT,

    totalPrize FLOAT,
    numberOfRegistrants INT(4),
    numberOfSubmissions INT(4),
    numberOfSubmitters INT(4),

    platforms VARCHAR(128),
    technologies VARCHAR(256),

    registrationStartDate DATETIME,
    registrationEndDate DATETIME,
    submissionEndDate DATETIME,
    postingDate DATETIME
) ENGINE = INNODB;

CREATE TABLE IF NOT EXISTS Challenge_Registrant_Relation (
    challengeId INT(8),
    handle VARCHAR(128),
    registrationDate DATETIME,
    submissionDate DATETIME,
    PRIMARY KEY(challengeId, handle)
) ENGINE = INNODB;

CREATE TABLE IF NOT EXISTS Challenge_Winner (
    challengeId INT(8),
    handle VARCHAR(128),
    submissionDate DATETIME,
    ranking INT(8),
    points FLOAT,
    PRIMARY KEY(challengeId, handle)
) ENGINE = INNODB;

CREATE TABLE IF NOT EXISTS  User_Profile (
    handle VARCHAR(128) UNIQUE,
    userId INT(8) UNIQUE,
    memberSince DATETIME,
    countryCode CHAR(3),
    description VARCHAR(512),
    wins INT(4),
    challenges INT(4),
    PRIMARY KEY(handle)
) ENGINE = INNODB;

CREATE TABLE IF NOT EXISTS User_Skill (
    userId INT(8),
    skill VARCHAR(128),
    score FLOAT,
    fromChallenge BOOLEAN,
    fromUserEnter BOOLEAN
) ENGINE = INNODB;

