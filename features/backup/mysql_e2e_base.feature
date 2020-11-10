Feature: base cases.272

  @test @case.272
  Scenario: MySQL-001-database/add_group should succeed
    When I add a MySQL group
    Then the response is ok
    And the MySQL group list should contains the MySQL group

  @test @case.272
  Scenario: MySQL-002-database/add_group with SIP should succeed
    When I found a valid SIP, or I skip the test
    And I add a MySQL group with the SIP
    Then the response is ok
    And the MySQL group list should contains the MySQL group

  @test @case.272
  Scenario: MySQL-003-database/remove_group should succeed
    When I found a MySQL group without MySQL instance, or I skip the test
    And I remove the MySQL group
    Then the response is ok
    And the MySQL group list should not contains the MySQL group

  @test @case.272 @slow
  Scenario: MySQL-004-add database instances of m-s should succeed
    When I found a MySQL group without MySQL instance, and without SIP, or I skip the test
    And I found a server with components ustats,udeploy,uguard-agent,urman-agent, or I skip the test
    And I found a valid port, or I skip the test
    And I add MySQL instance in the MySQL group
    Then the response is ok
    And the MySQL group should have 1 running MySQL instance in 11s

    When I found a MySQL master in the MySQL group
    And I make a manual backup on the MySQL instance
    Then the response is ok

    When I add MySQL slave in the MySQL group
    Then the response is ok
    And the MySQL group should have 2 running MySQL instance in 11s

    When I enable HA on all MySQL instance in the MySQL group
    Then the response is ok
    And the MySQL group should have 1 running MySQL master and 1 running MySQL slave in 30s

  @test @case.272
  Scenario: MySQL-005-database/remove instance should succeed
    When I found a running MySQL instance, or I skip the test
    And I remove MySQL instance
    Then the response is ok
    And the MySQL instance list should not contains the MySQL instance

  @test @case.272
  Scenario: MySQL-006-database/start MySQL instance ha enable should succeed
    When I found a running MySQL instance, or I skip the test
    And I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

  @test @case.272
  Scenario: MySQL-007-database/stop MySQL instance ha enable should succeed
    When I found a running MySQL instance and uguard enable,or I skip the test
    And I stop MySQL instance ha enable
    Then the response is ok
    And MySQL instance ha enable should stopped in 1m

  @test @case.272
  Scenario: MySQL-008-database/configure group SIP
    When I found a valid SIP, or I skip the test
    And I found a MySQL group without MySQL instance, and without SIP, or I skip the test
    And I configure MySQL group SIP
    Then the response is ok
    And update MySQL group SIP successful in 1m

  @test @case.272
  Scenario: MySQL-09-database/reset database instance
    When I found a running MySQL instance, or I skip the test
    And I make a manual backup on the MySQL instance
    Then the response is ok

    When I stop MySQL service
    Then the response is ok
    And stop MySQL service should succeed in 1m

    When I reset database instance
    Then the response is ok
    And reset database instance should succeed in 2m

  @test @case.272
  Scenario: MySQL-010-database/promote to master
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I promote slave instance to master
    Then the response is ok
    And promote slave instance to master should succeed in 1m

  @test @case.272
  Scenario Outline: MySQL-011-view slave staus
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I query the slave instance "SELECT SERVICE_STATE FROM performance_schema.<option>"
    Then the MySQL response should be
      | SERVICE_STATE |
      | ON            |
    Examples:
      | option                        |
      | replication_connection_status |
      | replication_applier_status    |

  @test @case.272
  Scenario: MySQL-012-create table in instance
    When I found a running MySQL instance, or I skip the test
    And I execute the MySQL instance "use mysql;create table testcase(id int auto_increment not null primary key ,uname char(8),gender char(2),birthday date );"
    And I query the MySQL instance "select table_name from information_schema.tables where table_name="testcase";"
    Then the MySQL response should be
      | table_name |
      | testcase   |
    When I execute the MySQL instance "use mysql;DROP TABLE testcase;"

  @test
  Scenario: MySQL-013-database/create MySQL user should succeed
    When I found a running MySQL instance, or I skip the test
    And I create MySQL user "testcase" and grants "all privileges on *.*"
    Then the response is ok

    When I query the MySQL instance "show grants for 'testcase';"
    Then the MySQL response should be
      | Grants for testcase@%                         |
      | GRANT ALL PRIVILEGES ON *.* TO 'testcase'@'%' |

    When I create MySQL user "testcase" and grants "select on *.*"
    Then the response is ok

    When I query the MySQL instance "show grants for 'testcase';"
    Then the MySQL response should be
      | Grants for testcase@%                         |
      | GRANT ALL PRIVILEGES ON *.* TO 'testcase'@'%' |

  @test
  Scenario: MySQL-014-data/update MySQL user password
    When I found a running MySQL instance, or I skip the test
    And I create MySQL user "test55" and grants "all privileges on *.*"
    Then the response is ok
    When I query the MySQL instance "show grants for 'test55';"
    Then the MySQL response should be
      | Grants for test55@%                         |
      | GRANT ALL PRIVILEGES ON *.* TO 'test55'@'%' |

    When I update MySQL user "test55" and password "test"
    Then the response is ok

    When I query the MySQL instance use user "test55" "show grants for 'test55';"
    Then the MySQL response should be
      | Grants for test55@%                         |
      | GRANT ALL PRIVILEGES ON *.* TO 'test55'@'%' |

  @test
  Scenario: MySQL-015-idempotent exclude and include ha
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I exclude ha MySQL instance
    Then the response is ok
    And MySQL instance ha enable should stopped in 1m

    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

    When I stop MySQL instance ha enable
    Then the response is ok
    And MySQL instance ha enable should stopped in 1m

    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

  @test
  Scenario: MySQL-016-restart slave uguard-agent and view instance data
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test

    When I action pause MySQL instance component uguard-agent
    Then the response is ok
    And action pause MySQL instance component uguard-agent should succeed in 1m

    When I create and insert table in master instance "use mysql;create table test55(id int auto_increment not null primary key ,uname char(8));"
    Then the response is ok
    When I query the slave instance "select table_name from information_schema.tables where table_name="test55";"
    Then the MySQL response should be
      | table_name |
      | test55     |
    When I create and insert table in master instance "use mysql;DROP TABLE test55;"
    Then the response is ok
    When I action start MySQL instance component uguard-agent
    Then the response is ok
    And action start MySQL instance component uguard-agent should succeed in 1m

  @test
  Scenario: MySQL-017-add MongoDB group should succeed
    When I found a valid port, or I skip the test
    And I add MongoDB group
    Then the response is ok
    And the MongoDB group list should contains the MongoDB group

  Scenario: MySQL-018-add MongoDB instance should succeed
    When I found a server with components ustats,udeploy,uguard-agent,urman-agent, or I skip the test
    And I found a MongoDB group without MongoDB instance, or I skip the test
    When I add MongoDB instance
    Then the response is ok
    And the MongoDB instance should add succeed in 1m

    When I found a server with components ustats,udeploy,uguard-agent,urman-agent, or I skip the test
    When I add MongoDB instance
    Then the response is ok
    And the MongoDB group should have 1 running MongoDB master and 1 running MongoDB slave in 1m

  Scenario: MySQL-019-stop and start MongoDB instance should succeed
    When I found a running MongoDB instance slave, or I skip the test
    And I action stop the MongoDB instance
    Then the response is ok
    And the MongoDB instance should stopped in 2m

    When I action start the MongoDB instance
    Then the response is ok
    And the MongoDB instance should started in 2m

  Scenario: MySQL-020-database/add SLA protocol and start or pause
    When I found a running MySQL instance, or I skip the test
    And I bind SLA protocol to the MySQL group
    Then the response is ok
    And SLA protocol of the MySQL group should be binded

    When I enable the SLA protocol of the MySQL group
    Then the response is ok
    And SLA protocol should started

    When I pause SLA protocol
    Then the response is ok
    And SLA protocol should paused

    When I unbind SLA protocol
    Then the response is ok
    And SLA protocol should not exist

  Scenario Outline: MySQL-021-update MySQL configuration with host connect should succeed
    When I found a running MySQL instance, or I skip the test
    And I update MySQL configuration with host connect "<option>" to "<option_value>"
    Then the response is ok
    When I wait for updating MySQL configuration finish in 1m
    And I query the MySQL instance "show global variables like '<option>'"
    Then the MySQL response should be
      | Variable_name | Value          |
      | <option>      | <option_value> |

    Examples:
      | option            | option_value |
      | slave_net_timeout | 999          |
      | slave_net_timeout | 998          |
      | slave_net_timeout | 997          |

  Scenario Outline: MySQL-022-Highly Available policy add RTO/RPO template
    When I add a <type> template
    Then the response is ok
    And the Highly Available policy list should contains the <type> template

    Examples: sla type
      | type |
      | rto  |
      | rpo  |

  Scenario Outline: MySQL-023-Highly Available policy update RTO/RPO template configuration
    When I found a valid <type> template, or I skip the test
    And I update the <type> template configuration, <config>
    Then the response is ok
    And the <type> template should be <config>

    Examples: update config
      | type | config                                                                 |
      | rto  | sla_rto: 700, sla_rto_levels: 20,30,400                                |
      | rpo  | sla_rpo: 1, sla_rpo_levels: 10,40,500, sla_rpo_error_levels: 20,50,500 |

  Scenario Outline: MySQL-024-Highly Available policy remove RTO/RPO template
    When I found a valid <type> template, or I skip the test
    And I remove the <type> template
    Then the response is ok
    And the <type> template should not exist

    Examples: sla type
      | type |
      | rto  |
      | rpo  |

  Scenario: MySQL-025-uguard-agent restart in master instance
    When I found a MySQL group with 2 MySQL instance, and without SIP, or I skip the test
    When I found a valid SIP, or I skip the test
    And I configure MySQL groups SIP
    Then the response is ok
    And update MySQL groups SIP successful in 1m

    When I stop the MySQL instance master component uguard-agent
    And I start the MySQL instance master component uguard-agent

    When I execute the MySQL group "create table mysql.test_group_sip04(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test_group_sip04";" with sip
    Then the MySQL response should be
      | table_name       |
      | test_group_sip04 |
    When I execute the MySQL group "drop table mysql.test_group_sip04;" with sip
    Then the response is ok

  Scenario: MySQL-026-restart all uguard-agents, then insert data through the group SIP successfully
    When I found servers with running uguard-agent, or I skip the test
    And I pause uguard-agent on all these servers
    And I start uguard-agent on all these servers
    When I found a MySQL group with 2 MySQL instance, and with SIP, or I skip the test
    And I found a master MySQL's instance in the MySQL group
    When I execute the MySQL group "create table mysql.test_group_sip_restart(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query on the master instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip_restart";"
    Then the MySQL response should be
      | table_name             |
      | test_group_sip_restart |
    When I found a slave MySQL's instance in the MySQL group
    And I query on the slave instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip_restart";"
    Then the MySQL response should be
      | table_name             |
      | test_group_sip_restart |
    When I execute the MySQL group "drop table mysql.test_group_sip_restart;" with sip
    Then the response is ok

  Scenario: MySQL-027-uguard-mgr restart
    When I found a MySQL group with 2 MySQL instance, and with SIP, or I skip the test

    When I action stop component uguard-mgr in server
    Then the response is ok
    And component uguard-mgr should stopped in 1m

    When I action start component uguard-mgr
    Then the response is ok
    And component uguard-mgr should started in 1m

    When I execute the MySQL group "use mysql;create table test10(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test10";}" with sip
    Then the MySQL response should be
      | table_name |
      | test10     |

    When I execute the MySQL group "use mysql;DROP TABLE test10;" with sip
    Then the response is ok

  Scenario: MySQL-028-insert data through group SIP,with the slave's mysql down
    When I found servers with running uguard-agent, or I skip the test
    And I pause uguard-agent on all these servers

    When I found a MySQL group with 2 MySQL instance, and with SIP, or I skip the test
    When I found a server of the MySQL group's slave instance
    And I start uguard-agent except the slave's server
    When I kill 1 times slave mysql instance pid
    Then the slave MySQL instance should stopped in 2m
    When I start uguard-agent on the slave's server
    Then the slave MySQL instance should running in 2m

    When I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query on the slave instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip";"
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |
    When I execute the MySQL group "use mysql;DROP TABLE test_group_sip;" with sip
    Then the response is ok

  Scenario: MySQL-029-insert data through group SIP
    When I found servers with running uguard-agent, or I skip the test
    And I pause uguard-agent on all these servers
    When I found a MySQL group with 2 MySQL instance, and with SIP, or I skip the test
    When I found a server of the MySQL group's slave instance
    And I start uguard-agent except the slave's server
    When I execute the MySQL group "create table mysql.test_group_sip_1(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query on the slave instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip_1";"
    Then the MySQL response should be
      | table_name       |
      | test_group_sip_1 |
    When I start uguard-agent on the slave's server
    Then the slave mysql instance should running in 2m

    When I execute the MySQL group "create table mysql.test_group_sip_2(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query on the slave instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip_2";"
    Then the MySQL response should be
      | table_name       |
      | test_group_sip_2 |

  Scenario: MySQL-030-remove MongoDB instance should succeed
    When I found a running MongoDB instance slave, or I skip the test
    And I remove MongoDB instance
    Then the response is ok
    And the MongoDB instance list should not contains the MongoDB instance in 2m

  Scenario: MySQL-031-trigger diagnosis report
    When I found a running MySQL instance, or I skip the test
    And I trigger diagnosis report
    Then the response is ok
    Then the diagnosis list should contains the diagnosis report

  Scenario: MySQL-032-trigger diagnosis score report
    When I found a running MySQL instance, or I skip the test
    And I trigger diagnosis score report
    Then the response is ok
    And the diagnosis score list should contains the diagnosis score

  Scenario: MySQL-033-pull MySQL instance GTID
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I create and insert table in slave instance "use mysql;create table test03(id int auto_increment not null primary key ,uname char(8));"
    When I query the slave instance "select table_name from information_schema.tables where table_name="test03";"
    Then the MySQL response should be
      | table_name |
      | test03     |
    And the MySQL instance should be exclude HA in 1m
    When I pull the MySQL instance GTID
    Then the response is ok
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m


