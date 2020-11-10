Feature: database

  @test @case.272
  Scenario: MySQL-001-database/add_group with SIP should succeed
    When I found a valid SIP, or I skip the test
    And I add a MySQL group with the SIP
    Then the response is ok
    And the MySQL group list should contains the MySQL group

  @test @case.272
  Scenario: MySQL-002-database/add_group should succeed
    When I add a MySQL group
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
    When I found a running MySQL instance, or I skip the test
    And I found a MySQL group without MySQL instance, or I skip the test
    And I configure MySQL group SIP
    Then the response is ok
    And update MySQL group SIP successful in 1m

  @test @case.272
  Scenario: MySQL-009-database/stop MySQL service
    When I found a running MySQL instance, or I skip the test
    And I stop MySQL service
    Then the response is ok
    And stop MySQL service should succeed in 1m

  @test @case.272
  Scenario: MySQL-010-database/reset database instance
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
  Scenario: MySQL-011-database/promote to master
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I promote slave instance to master
    Then the response is ok
    And promote slave instance to master should succeed in 1m

  @test @case.272
  Scenario Outline: view slave staus
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I query the slave instance "SELECT SERVICE_STATE FROM performance_schema.<option>"
    Then the MySQL response should be
      |SERVICE_STATE|
      |ON           |
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
  Scenario: MySQL-013-database/add SLA protocol and start or pause
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

  @test @case.272
  Scenario: MySQL-014-master-slave switching when kill three master pid
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I found alert code "EXCLUDE_INSTANCE_SUCCESS", or I skip the test
    And I kill three master pid

    Then master-slave switching in 1m
    And expect alert code "EXCLUDE_INSTANCE_SUCCESS" in 2m


  @test
  Scenario: MySQL-015-database/create MySQL user should succeed
    When I found a running MySQL instance, or I skip the test
    And I create MySQL user "testcase" and grants "all privileges on *.*"
    Then the response is ok

    When I query the MySQL instance "show grants for 'testcase';"
    Then the MySQL response should be
      |Grants for testcase@%|
      |GRANT ALL PRIVILEGES ON *.* TO 'testcase'@'%'|

    When I create MySQL user "testcase" and grants "select on *.*"
    Then the response is ok

    When I query the MySQL instance "show grants for 'testcase';"
    Then the MySQL response should be
      |Grants for testcase@%|
      |GRANT ALL PRIVILEGES ON *.* TO 'testcase'@'%'|

  @test
  Scenario: MySQL-016-data/update MySQL user password
    When I found a running MySQL instance, or I skip the test
    And I create MySQL user "test55" and grants "all privileges on *.*"
    Then the response is ok
    When I query the MySQL instance "show grants for 'test55';"
    Then the MySQL response should be
      |Grants for test55@%|
      |GRANT ALL PRIVILEGES ON *.* TO 'test55'@'%'|

    When I update MySQL user "test55" and password "test"
    Then the response is ok

    When I query the MySQL instance use user "test55" "show grants for 'test55';"
    Then the MySQL response should be
      |Grants for test55@%|
      |GRANT ALL PRIVILEGES ON *.* TO 'test55'@'%'|

  @test
  Scenario: MySQL-017-database/takeover MySQL instance
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I detach MySQL instance
    Then the response is ok

    Then the MySQL instance should be not exist
    When I takeover MySQL instance
    Then the response is ok
    And the MySQL instance should be listed

  @test
  Scenario: MySQL-018-idempotent exclude and include ha
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
  Scenario: MySQL-019-SLA downgrade recovery
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I add SLA protocol "SLA_RPO_sample"
    Then the response is ok

    Then SLA protocol "SLA_RPO_sample" should added

    When I start the group SLA protocol
    Then the response is ok
    And the group SLA protocol should started

    When I exclude ha MySQL instance
    Then the response is ok
    And MySQL instance ha enable should stopped in 1m
    And group sla level PE3 in 1m
    And expect alert code "SLA_LEVEL_CHANGED" and detail "P1 to PE3" in 3m


    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m
    And group sla level P1 in 1m

    When I pause the group SLA protocol
    Then the response is ok
    And the group SLA protocol should paused in 1m
    When I remove the group SLA protocol
    Then the response is ok
    And the group SLA protocol should remove succeed in 1m

    When I add SLA protocol "SLA_RTO_sample"
    Then the response is ok
    And SLA protocol "SLA_RTO_sample" should added
    When I start the group SLA protocol
    Then the response is ok
    And the group SLA protocol should started
    When I exclude ha MySQL instance
    Then the response is ok
    And MySQL instance ha enable should stopped in 1m
    And group sla level TE3 in 1m
    And expect alert code "SLA_LEVEL_CHANGED" and detail "T1 to TE3" in 3m

    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m
    And group sla level T1 in 1m

  @test
  Scenario: MySQL-020-restart slave uguard-agent and view instance data
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test

    When I action pause MySQL instance component uguard-agent
    Then the response is ok
    And action pause MySQL instance component uguard-agent should succeed in 1m

    When I create and insert table in master instance "use mysql;create table test55(id int auto_increment not null primary key ,uname char(8));"
    Then the response is ok
    When I query the slave instance "select table_name from information_schema.tables where table_name="test55";"
    Then the MySQL response should be
      | table_name |
      | test55   |
    When I create and insert table in master instance "use mysql;DROP TABLE test55;"
    Then the response is ok
    When I action start MySQL instance component uguard-agent
    Then the response is ok
    And action start MySQL instance component uguard-agent should succeed in 1m
	
  Scenario Outline: MySQL-025-update MySQL configuration with host connect should succeed
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

  Scenario: MySQL-026-components status when disable HA master-slave instance
	When I found 1 MySQL groups with MySQL HA instances, or I skip the test
	And I action stop role STATUS_MYSQL_SLAVE on HA instance
	Then the response is ok
	And the server uguard should running
	When I action stop role STATUS_MYSQL_MASTER on HA instance
	Then the response is ok
	And the server uguard should running

  Scenario: MySQL-027-takeover MySQL and view data consistent or remove instance
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I detach MySQL instance
    Then the response is ok
    Then the MySQL instance should be not exist
    When I takeover MySQL instance
    Then the response is ok
    And the MySQL instance should be listed
    
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m
    
    When I create and insert table in master instance "use mysql;create table test5(id int auto_increment not null primary key ,uname char(8));"
    Then the response is ok
    When I query the slave instance "select table_name from information_schema.tables where table_name="test5";"
    Then the MySQL response should be
      | table_name |
      | test5      |
    When I create and insert table in master instance "use mysql;DROP TABLE test5;"
    And I stop MySQL instance ha enable
    Then the response is ok
    And MySQL instance ha enable should stopped in 1m
    
    When I remove MySQL instance
    Then the response is ok
    And the MySQL instance list should not contains the MySQL instance
  
  
  Scenario: MySQL-028-uguard-mgr restart
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I add the ip to sip pool
    
    When I found a valid SIP, or I skip the test
    And I configure MySQL group SIP
    Then the response is ok
    And update MySQL group SIP successful in 1m
    
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
	
  Scenario: MySQL-029-no alarm when enable SLA and disable SLA or HA
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I found alert code "RESTART_REPLICATION", or I skip the test
    And I found alert code "EXCLUDE_INSTANCE_SUCCESS", or I skip the test
    And I add SLA protocol "SLA_RPO_sample"
    Then the response is ok
    And SLA protocol "SLA_RPO_sample" should add succeed in 1m
    
    When I start the group SLA protocol
    Then the response is ok
    And the group SLA protocol should started
    
    When I promote slave instance to master
    Then the response is ok
    And promote slave instance to master should succeed in 1m
    And alert code RESTART_REPLICATION should not exist in 1m
    
    When I action stop role STATUS_MYSQL_SLAVE on HA instance
    Then the response is ok
    And alert code EXCLUDE_INSTANCE_SUCCESS should not exist in 1m
    
    When I action stop role STATUS_MYSQL_MASTER on HA instance
    Then the response is ok
    And alert code EXCLUDE_INSTANCE_SUCCESS should not exist in 1m

    When I action start role STATUS_MYSQL_MASTER on HA instance
    Then the response is ok
    And alert code RESTART_REPLICATION should not exist in 1m
    
    When I action start role STATUS_MYSQL_SLAVE on HA instance
    Then the response is ok
    And alert code RESTART_REPLICATION should not exist in 1m
    
    When I isolate the MySQL instance
    Then the response is ok
    And alert code mysql_slave_sql_thread_down should contains in 1m
    And alert code mysql_slave_io_thread_down should contains in 1m


  Scenario: MySQL-030-batch takeover MySQL instances should succeed
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I detach the batch MySQL instance
    Then the response is ok
    And the MySQL instance list should be not exist the MySQL instance

    When I batch takeover the MySQL instance
    Then the response is ok
    And batch takeover the MySQL instance list should contains the MySQL instance in 2m


  Scenario Outline: MySQL-031-Highly Available policy add RTO/RPO template
    When I add a <type> template
    Then the response is ok
    And the Highly Available policy list should contains the <type> template
    
    Examples: sla type
      | type |
      | rto  |
      | rpo  |
  
  Scenario Outline: MySQL-32-Highly Available policy update RTO/RPO template configuration
    When I found a valid <type> template, or I skip the test
    And I update the <type> template configuration, <config>
    Then the response is ok
    And the <type> template should be <config>
    
    Examples: update config
      | type | config                                                                 |
      | rto  | sla_rto: 700, sla_rto_levels: 20,30,400                                |
      | rpo  | sla_rpo: 1, sla_rpo_levels: 10,40,500, sla_rpo_error_levels: 20,50,500 |
  
  
  Scenario Outline: MySQL-033-Highly Available policy remove RTO/RPO template
    When I found a valid <type> template, or I skip the test
    And I remove the <type> template
    Then the response is ok
    And the <type> template should not exist
    
    Examples: sla type
      | type |
      | rto  |
      | rpo  |
  
  
  Scenario: MySQL-034-insert data through group SIP,with the slave's mysql down
	When I found servers with running uguard-agent, or I skip the test
	And I pause uguard-agent on all these servers
	
	When I found a MySQL group with 2 MySQL instance, and without SIP, or I skip the test
	And  I add the ip to sip pool
	Then the sip pool should contain the added IP
	
	When I found a valid SIP, or I skip the test
	And I configure MySQL group SIP
	Then the response is ok
	And update MySQL group SIP successful in 1m
	
	When I found a server of the MySQL group's slave instance
	And I start uguard-agent except the slave's server
	When I kill 1 times slave mysql instance pid
	Then the slave mysql instance should stopped in 20m
	When I start uguard-agent on the slave's server
	Then the slave mysql instance should running in 20m
	
	When I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
	And I query on the slave instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip";"
	Then the MySQL response should be
	  | table_name     |
	  | test_group_sip |
   
   
  Scenario: MySQL-035-insert data through group SIP
	When I found servers with running uguard-agent, or I skip the test
	And I pause uguard-agent on all these servers
	
	When I found a MySQL group with 2 MySQL instance, and without SIP, or I skip the test
	And  I add the ip to sip pool
	Then the sip pool should contain the added IP
	
	When I found a valid SIP, or I skip the test
	And I configure MySQL group SIP
	Then the response is ok
	And update MySQL group SIP successful in 1m
	
	When I found a server of the MySQL group's slave instance
	And I start uguard-agent except the slave's server
	When I execute the MySQL group "create table mysql.test_group_sip_1(id int auto_increment not null primary key ,uname char(8));" with sip
	And I query on the slave instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip_1";"
	Then the MySQL response should be
	  | table_name       |
	  | test_group_sip_1 |
	When I start uguard-agent on the slave's server
	Then the slave mysql instance should running in 20m
	
	When I execute the MySQL group "create table mysql.test_group_sip_2(id int auto_increment not null primary key ,uname char(8));" with sip
	And I query on the slave instance, with the sql: "select table_name from information_schema.tables where table_name="test_group_sip_2";"
	Then the MySQL response should be
	  | table_name       |
	  | test_group_sip_2 |
	

  Scenario: MySQL-036-batch install MySQL instances should succeed
    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I batch install the MySQL m-s instances
    Then the response is ok
    And the batch MySQL instance list should contains the MySQL instance in 5m

  Scenario: MySQL-037-trigger diagnosis report
    When I found a running MySQL instance, or I skip the test
    And I trigger diagnosis report
    Then the response is ok
    And the diagnosis list should contains the diagnosis report

  Scenario: MySQL-038-trigger diagnosis score report
    When I found a running MySQL instance, or I skip the test
    And I trigger diagnosis score report
    Then the response is ok
    And the diagnosis score list should contains the diagnosis score

  Scenario: MySQL-039-pull MySQL instance GTID
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I create and insert table in slave instance "use mysql;create table test03(id int auto_increment not null primary key ,uname char(8));"
    When I query the slave instance "select table_name from information_schema.tables where table_name="test03";"
    Then the MySQL response should be
      | table_name |
      | test03   |
    And the MySQL instance should be exclude HA in 1m
    When I pull the MySQL instance GTID
    Then the response is ok
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

  Scenario: MySQL-040-MySQL group GTID compared
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    Then the MySQL group GTID should be consistent in 1m
    When I create and insert table in slave instance "use mysql;create table test019(id int auto_increment not null primary key ,uname char(8));"
    And I query the slave instance "select table_name from information_schema.tables where table_name="test019";"
    Then the MySQL response should be
      | table_name |
      | test019   |
    And the MySQL instance should be exclude HA in 1m
    And the MySQL group GTID should not consistent in 1m

    When I action stop role STATUS_MYSQL_MASTER on HA instance
    Then the response is ok

    When I action start role STATUS_MYSQL_SLAVE on HA instance
    Then the response is ok
    When I enable HA on the MySQL instance with uguard_status not health
    Then the response is ok
    And the MySQL group GTID should be consistent in 1m

    When I create and insert table in master instance "use mysql;DROP TABLE test019;"

  Scenario: MySQL-041-parameter configuration readonly of master-slave switching in instance information
    When I found a MySQL group with 3 MySQL instance, and without SIP, or I skip the test
    And I update the MySQL instance config readonly 1
    Then the response is ok
    And the MySQL instance config readonly should be 1
    When I kill three master pid
    Then the MySQL instance status should be in 2m

    When I make a manual backup on the master MySQL instance
    Then the response is ok
    When I reset old master MySQL instance
    Then the response is ok
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m
	
	
  Scenario: MySQL-042-restart all uguard-agents, then insert data through the group SIP successfully
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

  Scenario: MySQL-043-uguard-agent restart in master instance
    When I found a MySQL group with 2 MySQL instance, and without SIP, or I skip the test
    And  I add the ip to sip pool
    Then the sip pool should contain the added IP

    When I found a valid SIP, or I skip the test
    And I configure MySQL group SIP
    Then the response is ok
    And update MySQL group SIP successful in 1m

    When I stop the MySQL instance master component uguard-agent
    And I start the MySQL instance master component uguard-agent

    When I execute the MySQL group "create table mysql.test_group_sip04(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test_group_sip04";" with sip
    Then the MySQL response should be
      | table_name       |
      | test_group_sip04 |

  
  Scenario: MySQL-044-not able choose master when HA Cluster no master
    When I found a MySQL group with 2 MySQL instance, and without SIP, or I skip the test
    And I found alert code "NOT_ABLE_CHOOSE_MASTER", or I skip the test
    When I make a manual backup on the master MySQL instance
    Then the response is ok
    When I damage the master MySQL instance configuration file and kill pid
    Then the response is ok
    And the slave MySQL instance promoted in 2m
    When I reset database instance
    Then the response is ok
    And reset database instance should succeed in 2m
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

    When I damage the slave MySQL instance configuration file and kill pid
    Then the response is ok
    And the MySQL instance should not be health in 1m
    When I damage the master MySQL instance configuration file and kill pid
    Then the response is ok
    And the MySQL instance should not be health in 1m
    And alert code NOT_ABLE_CHOOSE_MASTER should contains in 2m

  Scenario: MySQL-045-master-slave switch when amage master MySQL configuration file and kill pid
    When I found a MySQL group with 2 MySQL instance, and without SIP, or I skip the test
    And I make a manual backup on the master MySQL instance
    Then the response is ok
    When I damage the master MySQL instance configuration file and kill pid
    Then the response is ok
    And the slave MySQL instance promoted in 2m
    When I reset database instance
    Then the response is ok
    And reset database instance should succeed in 2m
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m


